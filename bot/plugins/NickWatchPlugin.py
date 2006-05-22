import datetime
import string

class NickWatchPlugin:
    
    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        self.recheckTimeoutSeconds = 60
        self.lastCheck = datetime.datetime.now()
        self.watchList = []

    def getVersionInformation(self):
        return("$Id: NickWatchPlugin.py 202 2006-03-25 23:14:16Z cortex $")

    def onTimer(self, irclib):
        deltatime = datetime.datetime.now() - self.lastCheck
        if((deltatime.days != 0) or (deltatime.seconds > self.recheckTimeoutSeconds)):
            self.sendChecks(irclib)
            self.lastCheck = datetime.datetime.now()

    def sendChecks(self, irclib):
        for (watcher, nickToWatch) in self.watchList:
            irclib.doWhois(nickToWatch)
            #print "Sent WHOIS about %s." % (nickToWatch)

    def addToWatchList(self, watcher, nickToWatch):
        self.watchList.append((watcher, nickToWatch))
        #print "Added %s to the watchList of %s." % (nickToWatch, watcher)

    def changeWatcher(self, source, target):
        for (watcher, nickToWatch) in self.watchList:
            if(watcher == source):
                self.watchList.remove((source, nickToWatch))
                self.watchList.append((target, nickToWatch))
                #print "Changed entry for %s to %s." % (source, target)

    def reportUnusedNick(self, irclib, watcher, nickToWatch):
        irclib.sendPrivateNotice(watcher, "The nick %s you asked for is now free for taking." % (nickToWatch))
        self.watchList.remove((watcher, nickToWatch))
        #print "Reported %s to %s." % (nickToWatch, watcher)

    def onWhoisResult(self, irclib, nick, username, host, userinfo):
        for (watcher, nickToWatch) in self.watchList:
            if(nickToWatch == nick):
                if((username == None) and (host == None) and (userinfo == None)):
                    self.reportUnusedNick(irclib, watcher, nickToWatch)

    def onChangeNick(self, irclib, source, target):
        self.changeWatcher(source, target)

    def onChannelMessage(self, irclib, source, message):
        if((len(message.split()) >= 2) and (message.split()[0] == "!nickwatch")):
            name = message.split()[1]
            self.addToWatchList(source, name)






#Unit-test
if __name__ == "__main__":
    class IrcLibMock:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def sendChannelEmote(self, text):
            print "* %s" % (text)

    pass