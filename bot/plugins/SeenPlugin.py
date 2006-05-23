# Keeps track of the last time people were in the channel
import pickle, os, datetime, exceptions, logging
from modules import PluginInterface

class SeenRecord:
    # If you add or remove a field from this class, please increment this
    # number and add an appropriate conversion in __setstate__
    ClassVersion = 1
    def __init__(self, message):
        self.message = message
        self.time = datetime.datetime.now()
        
    def formatDeltaTime(self, deltaTime):
        days    = deltaTime.days
        hours   = int(deltaTime.seconds/3600)
        minutes = int( (deltaTime.seconds % 3600) / 60)
        seconds = deltaTime.seconds % 60
        if days != 0:
            return "%i days and %i hours ago" % (days, hours)
        elif hours != 0:
            return "%i hours and %i minutes ago" % (hours, minutes)
        elif minutes != 0:
            return "%i minutes and %i seconds ago" % (minutes, seconds)
        else:
            return "%i seconds ago" % (seconds,)
        
    def __str__(self):
        return self.formatDeltaTime(datetime.datetime.now() - self.time) + ", " + self.message
    
    # Pickling methods
    def __getstate__(self):
        odict = self.__dict__.copy()
        odict["version"] = self.ClassVersion
        return odict
    def __setstate__(self, dict):
        if dict["version"] == self.ClassVersion:
            self.__dict__.update(dict)
        else:
            raise exceptions.IOError("Unknown SeenRecord version encountered! Please upgrade RTBot!")

class SeenPlugin:
    # Dictionary
    lastSeenTimes = {}
    SaveFile = "resources/seentimes.lst"
    
    def __init__(self, pluginInterface):
        self.pluginInterface = pluginInterface
        self.loadList()
    
    def saveList(self):
        file = open(self.SaveFile, "w")
        pickle.dump(self.lastSeenTimes, file, -1)
        file.close()
        
    def loadList(self):
        # If file present - load the old list
        try:
            file = open(self.SaveFile, "r")
            self.lastSeenTimes = pickle.load(file)
            file.close()
        except:
            lastSeenTimes = {}
            
    def getCanonicalName(self, rawName):
        # retrieve AuthenticationPlugin
        authenticationPlugin = self.pluginInterface.getPlugin("AuthenticationPlugin")
        if(authenticationPlugin == None):
            logging.info("ERROR: SeenPlugin didn't succeed at lookup of AuthenticationPlugin during execution of getCanonicalName()")
            return(rawName)
        else:
            return(authenticationPlugin.getCanonicalName(rawName))

    def getCanonicalUserList(self, irclib):
        rawUserList = irclib.getUserList().getPureList()
        # retrieve AuthenticationPlugin
        authenticationPlugin = self.pluginInterface.getPlugin("AuthenticationPlugin")
        if(authenticationPlugin == None):
            logging.info("ERROR: SeenPlugin didn't succeed at lookup of AuthenticationPlugin during execution of getCanonicalUserList()")
            return rawUserList
        else:
            return [authenticationPlugin.getCanonicalName(rawName) for rawName in rawUserList]
        
    
    def getVersionInformation(self):
        return("$Id$")
        
    # Maybe we should limit how many people we keep track of? At first I thought
    # I'd use the buddy-list, but then I thought that would be too restrictive...
    # Maybe if we have > 512 entries, remove the oldest?
    def handleUserLeft(self, source, message):
        self.lastSeenTimes[self.getCanonicalName(source).lower()] = SeenRecord(message)
        self.saveList()
        
    def onLeave(self, irclib, source):
        self.handleUserLeft(source, "leaving channel")
    def onQuit(self, irclib, source, reason):
        self.handleUserLeft(source, "leaving IRC: " + reason)
    def onKick(self, irclib, source, target, reason):
        self.handleUserLeft(source, "getting kicked by " + source + " for " + reason)
    def onChangeNick(self, irclib, source, target):
        self.handleUserLeft(source, "changing nick to " + target)

    @PluginInterface.Priorities.prioritized(PluginInterface.Priorities.PRIORITY_NORMAL)
    def onChannelMessage(self, irclib, source, message):
        words = message.split()
        if len(words) == 2 and words[0] == "seen":
            name = self.getCanonicalName(words[1]).lower()
            source = self.getCanonicalName(source).lower()
            if name == source:
                irclib.sendChannelMessage("I see you very well, sai!") # bonus-points for recognizing the quote / reference  // Ksero
            else:
                users = self.getCanonicalUserList(irclib)
                if name == "rtbot":
                    irclib.sendChannelMessage("#mute " + source + "@jesters :P")
                elif name in users:
                    irclib.sendChannelMessage("Ummm... " + name + " is right here, yo? Whatcha talkin' bout, boy?")
                elif name in self.lastSeenTimes:
                    irclib.sendChannelMessage(name + " was last seen " + str(self.lastSeenTimes[name]))
                else:
                    irclib.sendChannelMessage("I've never seen anybody called " + name)
            return(True)

#Unit-test
if __name__ == "__main__":
    #import time for sleep
    import time
    class FakeUserList:
        def getFullList(self):
            return {"foo": "o", "bar": "v"}

    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def getUserList(self):
            return(FakeUserList())
    
    class AuthenticationPlugin:
        def getCanonicalName(self, name):
            return name
    
    class FakePluginInterface:
        def getPlugin(self, name):
            if name == "AuthenticationPlugin":
                return AuthenticationPlugin()

    a = SeenPlugin(FakePluginInterface())
    a.onLeave(FakeIrcLib(), "other")
    time.sleep(1)
    a.onChannelMessage(FakeIrcLib(), "foo", "seen bar") # bar is already in channel
    a.onChannelMessage(FakeIrcLib(), "foo", "seen foo") # seen yourself?
    a.onChannelMessage(FakeIrcLib(), "foo", "seen other") # other was last seen...