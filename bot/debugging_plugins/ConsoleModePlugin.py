import string
import code
import sys
from modules import PluginInterface




class MyStdoutStream:
    def __init__(self, irclib, user):
        self.irclib = irclib
        self.user = user

    def write(self, data):
        self.irclib.sendPrivateMessage(self.user, data)



class MyInterpreter(code.InteractiveInterpreter):
    def __init__(self, irclib, user, locals):
        self.irclib = irclib
        self.user = user
        sys.stdout = MyStdoutStream(irclib, user)
        code.InteractiveInterpreter.__init__(self, locals)
        
    def cleanup(self):
        sys.stdout == sys.__stdout__
        
    def write(self, data):
        self.irclib.sendPrivateMessage(self.user, data)



class ConsoleModePlugin:
    currentUser = None

    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        self.interpreter = None

    def getVersionInformation(self):
        return("$Id$")
    
    @PluginInterface.Priorities.prioritized( PluginInterface.Priorities.PRIORITY_VERYHIGH )
    def onPrivateMessage(self, irclib, source, message):
        if(message == "!login" and not self.currentUser):
            # switch to console mode
            irclib.sendPrivateMessage(source, "===== LOGGED IN =====")
            irclib.sendPrivateMessage(source, "Initialised local variables:")
            irclib.sendPrivateMessage(source, "- self: the ConsoleModePlugin you're working with")
            irclib.sendPrivateMessage(source, "- irclib: the IRC library")
            irclib.sendPrivateMessage(source, "- pi: the plugin interface")
            irclib.sendPrivateMessage(source, "- core: the bot core")
            self.currentUser = source
            self.interpreter = MyInterpreter(irclib, source, {"self": self, "irclib": irclib, "pi": self.pluginInterfaceReference, "core": self.pluginInterfaceReference.botcore})
            return(True)
        elif(message == "!logout" and self.currentUser):
            # leave console mode
            irclib.sendPrivateMessage(source, "===== LOGGED OUT =====")
            self.interpreter.cleanup()
            self.currentUser = None
            self.interpreter = None
            return(True)
        elif(self.currentUser and self.currentUser == source):
            codeObject = self.interpreter.runsource(message)
            return(True)



#Unit-test
if __name__ == "__main__":
    class PluginInterfaceMock:
        def getPluginByClassname(self, name):
            return(AuthPluginMock())

    class IrcLibMock:
        def sendPrivateMessage(self, target, text):
            print text

    a = ConsoleModePlugin(PluginInterfaceMock())
    a.onPrivateMessage(IrcLibMock(), "source", "!login")
    a.onPrivateMessage(IrcLibMock(), "source", "print 'a'")
    a.onPrivateMessage(IrcLibMock(), "source", "!logout")
    