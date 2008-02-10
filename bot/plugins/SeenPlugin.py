# Keeps track of the last time people were in the channel
import pickle, os, datetime, exceptions, logging, re
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

    def getCanonicalUserList(self, irclib):
        userList = irclib.getUserList().values()
        return [user.getCanonicalNick() for user in userList]
        
    
    def getVersionInformation(self):
        return("$Id$")
        
    def getCanonicalNick(self, nick):
        # (\S+?)(?:\[.*?\]|\|.*?|_{1,2})
        pattern =(r"^"          # nothing in front of this
                  r"(\S+?)"     # username, followed by
                  r"(?:\[.*?\]" # [....] or
                  r"|\|.*?"     # |..... or
                  r"|_{1,2})"   # _ or __
                  r"$")         # nothing after this
        result = re.match(pattern, nick)
        if(result):
            return(result.group(1))
        else:
            return(nick)

    # Maybe we should limit how many people we keep track of? At first I thought
    # I'd use the buddy-list, but then I thought that would be too restrictive...
    # Maybe if we have > 512 entries, remove the oldest?
    def handleUserLeft(self, canonicalSourceNick, message):
        self.lastSeenTimes[canonicalSourceNick.lower()] = SeenRecord(message)
        self.saveList()
        
    def onLeave(self, irclib, source):
        self.handleUserLeft(source.getCanonicalNick(), "leaving channel")
    def onQuit(self, irclib, source, reason):
        self.handleUserLeft(source.getCanonicalNick(), "leaving IRC: " + reason)
    def onKick(self, irclib, source, target, reason):
        self.handleUserLeft(source.getCanonicalNick(), "getting kicked by " + source.nick + " for " + reason)
    def onChangeNick(self, irclib, sourceNick, target):
        self.handleUserLeft(self.getCanonicalNick(sourceNick), "changing nick to " + target.nick)

    @PluginInterface.Priorities.prioritized(PluginInterface.Priorities.PRIORITY_NORMAL)
    def onChannelMessage(self, irclib, source, message):
        words = message.split()
        if len(words) == 2 and words[0] == "seen":
            targetNick = self.getCanonicalNick(words[1]).lower()
            sourceNick = source.getCanonicalNick().lower()
            if sourceNick == targetNick:
                irclib.sendChannelMessage("I see you very well, sai!") # bonus-points for recognizing the quote / reference  // Ksero
            else:
                nicksInChannel = self.getCanonicalUserList(irclib)
                if targetNick == irclib.nickname.lower():
                    irclib.sendChannelMessage("#mute " + sourceNick + "@jesters :P")
                #elif targetNick in nicksInChannel:
                elif any(v.lower() == targetNick for v in nicksInChannel):
                    irclib.sendChannelMessage("Ummm... " + targetNick + " is right here, yo? Whatcha talkin' bout, boy?")
                elif targetNick in self.lastSeenTimes:
                    irclib.sendChannelMessage(targetNick + " was last seen " + str(self.lastSeenTimes[targetNick]))
                else:
                    irclib.sendChannelMessage("I've never seen anybody called " + targetNick)
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