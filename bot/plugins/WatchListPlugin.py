import datetime
import string



# NOTE: the !watchnick part of this plugin would better use the command ISON that WHOIS'ing everybody on the list (credit to neek)



class WatchListPlugin:
    
    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        self.recheckTimeoutSeconds = 60
        self.lastCheck = datetime.datetime.now()
        self.possiblyActiveWatchers = False
        self.possiblyActiveNickWaiters = False
        self.possiblyActiveNameWaiters = False

    def getVersionInformation(self):
        return("$Id: WatchListPlugin.py 202 2006-03-25 23:14:16Z cortex $")

    @classmethod
    def getDependencies(self):
        return(["AuthenticationPlugin"])

    def getAccountList(self):
        # retrieve InsultPlugin
        authenticationPlugin = self.pluginInterfaceReference.getPlugin("AuthenticationPlugin")
        if(authenticationPlugin == None):
            logging.info("ERROR: WatchListPlugin didn't succeed at lookup of AuthenticationPlugin during execution of getAccountList()")
            pass
        else:
            return(authenticationPlugin.accountList)

    def onTimer(self, irclib):
        if(self.possiblyActiveWatchers or self.possiblyActiveNameWaiters):
            deltatime = datetime.datetime.now() - self.lastCheck
            if((deltatime.days != 0) or (deltatime.seconds > self.recheckTimeoutSeconds)):
                if(self.possiblyActiveWatchers):
                    self.sendGlobalChecks(irclib)
                if(self.possiblyActiveNameWaiters):
                    self.checkNames(irclib)
                self.lastCheck = datetime.datetime.now()

    def sendGlobalChecks(self, irclib):
        anyActiveWatchers = False
        for user in irclib.getUserList().values():
            watchedNicks = user.dataStore.getAttributeDefault("watchedNicks", [])
            if(len(watchedNicks) > 0):
                for nick in watchedNicks:
                    irclib.doExternalWhois(nick)
                anyActiveWatchers = True
        self.possiblyActiveWatchers = anyActiveWatchers

    def checkNames(self, irclib):
        anyActiveNameWaiters = False
        for user in irclib.getUserList().values():
            waitedForNames = user.dataStore.getAttributeDefault("waitedForNames", [])
            if(len(waitedForNames) > 0):
                for name in waitedForNames:
                    if(irclib.getUserList().findByNameDefault(name)):
                        self.reportNamePresence(irclib, user, name, irclib.getUserList().findByNameDefault(name).nick)
                        waitedForNames.remove(name)
                        if(len(waitedForNames) == 0):
                            user.dataStore.removeAttribute("waitedForNames")
                        else:
                            user.dataStore.setAttribute("waitedForNames", waitedForNames)
                    else:
                        anyActiveNameWaiters = True
        self.possiblyActiveNameWaiters = anyActiveNameWaiters

    def checkNick(self, irclib, newNick):
        anyActiveNickWaiters = False
        for user in irclib.getUserList().values():
            waitedForNicks = user.dataStore.getAttributeDefault("waitedForNicks", [])
            if(len(waitedForNicks) > 0):
                if(newNick in waitedForNicks):
                    self.reportNickPresence(irclib, user, newNick)
                    waitedForNicks.remove(newNick)
                    if(len(waitedForNicks) == 0):
                        user.dataStore.removeAttribute("waitedForNicks")
                    else:
                        user.dataStore.setAttribute("waitedForNicks", waitedForNicks)
                else:
                    anyActiveNickWaiters = True
        self.possiblyActiveNickWaiters = anyActiveNickWaiters

    def reportUnusedNick(self, irclib, watcher, nickToWatch):
        irclib.sendPrivateNotice(watcher, "The nick %s you asked for is now free for taking." % (nickToWatch))

    def reportNickPresence(self, irclib, watcher, nickWaitingFor):
        irclib.sendPrivateNotice(watcher, "The nick %s you asked me to wait for just arrived." % (nickWaitingFor))

    def reportNamePresence(self, irclib, watcher, nameWaitingFor, nick):
        irclib.sendPrivateNotice(watcher, "The user %s you asked me to wait for just arrived with the nick %s." % (nameWaitingFor, nick))

    def watchNick(self, watcher, nickToWatch):
        self.possiblyActiveWatchers = True
        watchedNicks = watcher.dataStore.getAttributeDefault("watchedNicks", [])
        watchedNicks.append(nickToWatch)
        watcher.dataStore.setAttribute("watchedNicks", watchedNicks)

    def waitforNick(self, watcher, nickToWaitFor):
        self.possiblyActiveNickWaiters = True
        waitedForNicks = watcher.dataStore.getAttributeDefault("waitedForNicks", [])
        waitedForNicks.append(nickToWaitFor)
        watcher.dataStore.setAttribute("waitedForNicks", waitedForNicks)

    def waitforName(self, watcher, userToWaitFor):
        self.possiblyActiveNameWaiters = True
        waitedForNames = watcher.dataStore.getAttributeDefault("waitedForNames", [])
        waitedForNames.append(userToWaitFor)
        watcher.dataStore.setAttribute("waitedForNames", waitedForNames)

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

    def isNickAroundCaseInsensitive(self, irclib, target):
        for user in irclib.getUserList().values():
            if(user.getCanonicalNick().lower() == target.getCanonicalNick().lower()):
                return(True)
        return(False)

    def onWhoisResult(self, irclib, user):
        self.handleWhoisResult(irclib, user.nick, user.username, user.host, user.userinfo)
    
    def onExternalWhoisResult(self, irclib, nick, username, host, userinfo):
        self.handleWhoisResult(irclib, nick, username, host, userinfo)

    def onChangeNick(self, irclib, source, target):
        #irclib.sendChannelMessage("DEBUG: possiblyActiveNickWaiters=%s" % (str(self.possiblyActiveNickWaiters)))
        if(self.possiblyActiveNickWaiters):
            #irclib.sendChannelMessage("DEBUG: target.nick=%s" % (str(target.nick)))
            self.checkNick(irclib, target.nick.lower())

    def onJoin(self, irclib, source):
        if(self.possiblyActiveNickWaiters):
            self.checkNick(irclib, source.nick.lower())

    def onChannelMessage(self, irclib, source, message):
        if(len(message.split()) == 2):
            command = message.split()[0]
            target = message.split()[1]
            
            if(command == "!watchnick"):
                watchedNicks = source.dataStore.getAttributeDefault("watchedNicks", [])
                if(target.lower() in watchedNicks):
                    irclib.sendChannelMessage("I'm already watching that nick for you!")
                else:
                    self.watchNick(source, target.lower())
                    irclib.sendChannelMessage("Okay %s, I'll watch the availability of the nick '%s' for you." % (source.getAdressingName(), target))
            
            elif(command == "!waitfornick"):
                waitedForNicks = source.dataStore.getAttributeDefault("waitedForNicks", [])
                if(target.getCanonicalNick().lower() in waitedForNicks):
                    irclib.sendChannelMessage("I'm already waiting for the nick '%s' for you!" % (target.getCanonicalNick()))
                elif(self.isNickAroundCaseInsensitive(irclib, target)):
                    irclib.sendChannelMessage("Turn around, that person is right behind you! :)")
                else:
                    self.waitforNick(source, target.getCanonicalNick().lower())
                    irclib.sendChannelMessage("Okay %s, I'll tell you when the nick '%s' shows up." % (source.getAdressingName(), target))
            
            elif(command == "!waitforuser"):
                waitedForNames = source.dataStore.getAttributeDefault("waitedForNames", [])
                if(target in waitedForNames):
                    irclib.sendChannelMessage("I'm already waiting for that user for you!")
                elif(irclib.getUserList().findByNameDefault(target)):
                    irclib.sendChannelMessage("Turn around, that person is right behind you! :)")
                elif(not self.getAccountList().isKnown(target)):
                    irclib.sendChannelMessage("I don't know a user with that name.")
                else:
                    self.waitforName(source, target)
                    irclib.sendChannelMessage("Okay %s, I'll tell you when the user '%s' shows up." % (source.getAdressingName(), target))

        elif(message == "!watchlist"):
            #anyNicksWatched = False
            #for user in irclib.getUserList().values():
            #    watchedNicks = user.dataStore.getAttributeDefault("watchedNicks", [])
            #    if(len(watchedNicks) > 0):
            #        irclib.sendChannelMessage("%s is watching the nick(s): %s" % (user.nick, ", ".join(watchedNicks)))
            #        anyNicksWatched = True
            #if(not anyNicksWatched):
            #    irclib.sendChannelMessage("I'm currently not watching any nicks.")
            watchedNicks = source.dataStore.getAttributeDefault("watchedNicks", [])
            waitedForNicks = source.dataStore.getAttributeDefault("waitedForNicks", [])
            waitedForNames = source.dataStore.getAttributeDefault("waitedForNames", [])
            output = []
            if(len(watchedNicks) == 0):
                output.append("Not watching any nicks.")
            else:
                output.append("Watching nicks: %s" % (", ".join(watchedNicks)))
            if(len(waitedForNicks) == 0):
                output.append("Not waiting for any nicks.")
            else:
                output.append("Waiting for nicks: %s" % (", ".join(waitedForNicks)))
            if(len(waitedForNames) == 0):
                output.append("Not waiting for any users.")
            else:
                output.append("Waiting for users: %s" % (", ".join(waitedForNames)))
            irclib.sendChannelMessage(source.getAdressingName() + "'s watchlist: " + " / ".join(output))







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