import re, pickle



class RespectahPlugin:
    commandRE = re.compile("(\\S*?)\\.(\\S*?)\\((\\S*?)\\)((\\+\\+)|(--))")
    
    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        self.data = {}
        try:
            file = open("resources/respectah_data.pickle", "rb")
            self.data = pickle.load(file)
            file.close()
        except IOError:
            self.data = {}
        except EOFError:
            self.data = {}

    def saveList( self ):
        file = open("resources/respectah_data.pickle", "wb" )
        pickle.dump(self.data, file)
        file.close()

    def getVersionInformation(self):
        return("$Id: RespectahPlugin.py 260 2006-05-23 22:37:56Z Ksero $")

    @classmethod
    def getDependencies(self):
        return(["AuthenticationPlugin"])

    def isFriend(self, irclib, name):
        # retrieve AuthenticationPlugin
        authenticationPlugin = self.pluginInterfaceReference.getPlugin("AuthenticationPlugin")
        if(authenticationPlugin == None):
          logging.info("ERROR: RespectahPlugin didn't succeed at lookup of AuthenticationPlugin during execution of isFriend()")
          return(False)
        else:
          return(authenticationPlugin.isFriend(irclib, name))

    def printCurrentList(self, irclib, user, attribute):
        if(self.data.has_key(user)):
            if(self.data[user].has_key(attribute)):
                if(len(self.data[user][attribute].items())):
                    results = []
                    for (target, value) in self.data[user][attribute].items():
                        results.append("%s = %i" % (target, value))
                    irclib.sendChannelMessage("%s's %s: %s" % (user, attribute, ", ".join(results)))
                else:
                    irclib.sendChannelMessage("You never gave %s to anybody!" % (attribute))
            else:
                irclib.sendChannelMessage("You never used that attribute!")
        else:
            irclib.sendChannelMessage("You never gave any respectah!")
    
    def setValue(self, user, attribute, target, op):
        currentValue = self.data.setdefault(user, {}).setdefault(attribute, {}).setdefault(target, 0)
        self.data[user][attribute][target] = currentValue + op
        self.saveList()

    def getValue(self, user, attribute, target, op):
        return(self.data.get(user, {}).get(attribute, {}).get(target, 0))

    def onChannelMessage(self, irclib, source, message):
        auth = self.isFriend(irclib, source)
        if(auth):
            # "list respect"
            if((len(message.split()) >= 2) and (message.split()[0] == "list")):
                attribute = message.split()[1]
                self.printCurrentList(irclib, auth, attribute)

            # "self.respect(something)++"
            result = RespectahPlugin.commandRE.search(message)
            if(result):
                object = result.group(1)
                attribute = result.group(2)
                target = result.group(3)
                operation = result.group(4)
                if((object == auth) or (object == "self")):
                    if(operation == "++"):
                        op = +1
                    else:
                        op = -1
                    self.setValue(auth, attribute, target, op)
                    irclib.sendChannelMessage("%s's current %s for %s is %i." % (auth, attribute, target, self.getValue(auth, attribute, target, op)))
            





#Unit-test
if __name__ == "__main__":
    class AuthPluginMock:
        def isFriend(self, irclib, name):
            if(name == "friend"):
                return(name)
            else:
                return(None)
        def triggerModeUpdate(self, irclib):
            irclib.sendChannelMessage("AuthPlugin: updating!")

    class PluginInterfaceMock:
        def getPlugin(self, name):
            return(AuthPluginMock())

    class IrcLibMock:
        nickname = "RTBot"
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def sendChannelEmote(self, text):
            print "* %s" % (text)

    a = RespectahPlugin(PluginInterfaceMock())
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.respect(a)++ def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.respect(a)++ def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.respect(a)-- def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "somebodyelse", "abc friend.respect(a)-- def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc somebodyelse.respect(a)-- def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.respect(b)++ def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.stuff(a)++ def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "list respect")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "list stuff")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "list nothing")
    print "==============="
