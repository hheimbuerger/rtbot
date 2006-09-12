import datetime
import string

class NickWatchPlugin:
    
    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        self.recheckTimeoutSeconds = 60
        self.lastCheck = datetime.datetime.now()
        self.possiblyActiveWatchers = False

    def getVersionInformation(self):
        return("$Id: NickWatchPlugin.py 202 2006-03-25 23:14:16Z cortex $")

    def onTimer(self, irclib):
        if(self.possiblyActiveWatchers):
            deltatime = datetime.datetime.now() - self.lastCheck
            if((deltatime.days != 0) or (deltatime.seconds > self.recheckTimeoutSeconds)):
                self.sendChecks(irclib)
                self.lastCheck = datetime.datetime.now()

    def sendChecks(self, irclib):
        anyActiveWatchers = False
        for user in irclib.getUserList().values():
            watchedNicks = user.dataStore.getAttributeDefault("watchedNicks", [])
            if(len(watchedNicks) > 0):
                for nick in watchedNicks:
                    irclib.doExternalWhois(nick)
                anyActiveWatchers = True
        self.possiblyActiveWatchers = anyActiveWatchers

    def reportUnusedNick(self, irclib, watcher, nickToWatch):
        irclib.sendPrivateNotice(watcher, "The nick %s you asked for is now free for taking." % (nickToWatch))

    def watch(self, watcher, nickToWatch):
        self.possiblyActiveWatchers = True
        currentlyWatchedNicks = watcher.dataStore.getAttributeDefault("watchedNicks", [])
        currentlyWatchedNicks.append(nickToWatch)
        watcher.dataStore.setAttribute("watchedNicks", currentlyWatchedNicks)

    def handleWhoisResult(self, irclib, nick, username, host, userinfo):
        for user in irclib.getUserList().values():
            watchedNicks = user.dataStore.getAttributeDefault("watchedNicks", [])
            if(nick.lower() in watchedNicks):
                if((username == None) and (host == None) and (userinfo == None)):
                    self.reportUnusedNick(irclib, user, nick.lower())
                    watchedNicks.remove(nick.lower())
                    if(len(watchedNicks) == 0):
                        user.dataStore.removeAttribute("watchedNicks")
                    else:
                        user.dataStore.setAttribute("watchedNicks", watchedNicks)

    def onWhoisResult(self, irclib, user):
        self.handleWhoisResult(irclib, user.nick, user.username, user.host, user.userinfo)
    
    def onExternalWhoisResult(self, irclib, nick, username, host, userinfo):
        self.handleWhoisResult(irclib, nick, username, host, userinfo)

    def onChannelMessage(self, irclib, source, message):
        if((len(message.split()) >= 2) and (message.split()[0] == "!nickwatch")):
            watchedNicks = source.dataStore.getAttributeDefault("watchedNicks", [])
            nick = message.split()[1]
            if(nick.lower() in watchedNicks):
                irclib.sendChannelMessage("I'm already watching that nick for you!")
            else:
                self.watch(source, nick.lower())
                irclib.sendChannelMessage("Okay, I'll watch the availability of the nick '%s' for you." % (nick))
        elif(message == "!watchednickslist"):
            anyNicksWatched = False
            for user in irclib.getUserList().values():
                watchedNicks = user.dataStore.getAttributeDefault("watchedNicks", [])
                if(len(watchedNicks) > 0):
                    irclib.sendChannelMessage("%s is watching the nick(s): %s" % (source.nick, ", ".join(watchedNicks)))
                    anyNicksWatched = True
            if(not anyNicksWatched):
                irclib.sendChannelMessage("I'm currently not watching any nicks.")
                







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