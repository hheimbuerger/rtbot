import datetime, string, logging

class MutingPlugin:
    mutingTimeoutSeconds = 60
#===============================================================================
#    revolutionTimeoutSeconds = 20
#    minimumRevolutionistsNeeded = 3
#===============================================================================
    
    def __init__(self, pluginInterface):
#        self.muteList = {}
        self.pluginInterfaceReference = pluginInterface
#===============================================================================
#        self.revolutionStartingTime = None
#        self.revolutionists = []
#===============================================================================

    def getVersionInformation(self):
        return("$Id$")

    def getMuteList(self, userList):
        result = []
        for user in userList:
            if(user.dataStore.getAttributeDefault("isMuted", False)):
                result.append(user)
        return(result)

    def onTimer(self, irclib):
        # unmute timeout
        for mutee in self.getMuteList(irclib.getUserList().values()):
            timeOfMuting = mutee.dataStore.getAttribute("mutedAt")
            deltatime = datetime.datetime.utcnow() - timeOfMuting
            if((deltatime.days != 0) or (deltatime.seconds > self.mutingTimeoutSeconds)):
                self.unmute(irclib, mutee.nick)

#===============================================================================
#        # abort a revolution
#        if(self.revolutionStartingTime):
#            deltatime = datetime.datetime.now() - self.revolutionStartingTime
#            if((deltatime.days != 0) or (deltatime.seconds > self.revolutionTimeoutSeconds)):
#                self.revolutionStartingTime = None
#                self.revolutionists = []
#===============================================================================

    def mute(self, irclib, source, nick, verbose = True):
        if(nick.lower() == irclib.nickname.lower()):
            self.mute(irclib, irclib.nickname, source)
        else:
            if(verbose):
                if(nick in self.getMuteList(irclib.getUserList().values())):
                    irclib.sendChannelEmote("decides to keep %s muted a bit longer" % (nick))
                else:
                    irclib.sendChannelEmote("decides to mute %s" % (nick))
                irclib.sendChannelMessage(":P")
            user = irclib.getUserList()[nick]
            user.dataStore.setAttribute("isMuted", True)
            user.dataStore.setAttribute("mutedAt", datetime.datetime.utcnow())
            #self.triggerModeUpdate(irclib)

    def unmute(self, irclib, nick):
        # check if the user is around, otherwise ignore
        if(irclib.getUserList().has_key(nick)):
            user = irclib.getUserList()[nick]
            # check if the user is really muted, otherwise ignore
            if(user.dataStore.getAttributeDefault("isMuted", False)):
                irclib.sendChannelMessage("Okay, you'll be free, %s." % (nick))
                user.dataStore.removeAttribute("isMuted")
                user.dataStore.removeAttribute("mutedAt")
                #self.triggerModeUpdate(irclib)

#===============================================================================
#    def revolution(self, irclib, name):
#        # initialise the timer if not yet set
#        if(not self.revolutionStartingTime):
#            self.revolutionStartingTime = datetime.datetime.now()
#        
#        # add this person to the list of revolutionists
#        canonicalName = self.getCanonicalName(name)
#        if(name in self.revolutionists):
#            irclib.sendChannelMessage("I know, %s." % (canonicalName))
#        else:
#            self.revolutionists.append(name)
#
#        # remove those that aren't here anymore
#        for revolutionist in self.revolutionists:
#            if(not revolutionist in irclib.getUserList().getPureList()):
#                self.revolutionists.remove(revolutionist)
#
#        # do it if we have the appropriate number
#        if(len(self.revolutionists) >= self.minimumRevolutionistsNeeded):
#            irclib.sendChannelEmote("imitates a civil war")
#            for user in irclib.getUserList().getPureList():
#                if((user != irclib.nickname) and (not user in self.revolutionists)):
#                    self.mute(irclib, irclib.nickname, user, False)
#            irclib.sendChannelMessage("And I, for one, welcome our new virtual overlords. I'd like to remind them that as a trusted IRC personality, I can be helpful in rounding up others to toil in their underground byte caves.")
#        else:
#            if(len(self.revolutionists) == 1):
#                irclib.sendChannelMessage("Are you sure? I need %i more to support this..." % (self.minimumRevolutionistsNeeded - len(self.revolutionists)))
#            else:
#                irclib.sendChannelMessage("Okay %s, I need %i more..." % (canonicalName, self.minimumRevolutionistsNeeded - len(self.revolutionists)))
#===============================================================================

#===============================================================================
#    def printMuteList(self, irclib):
#        outputList = []
#        for (mutee, timeOfMuting) in self.muteList.items():
#            deltatime = datetime.datetime.now() - timeOfMuting
#            outputList.append("%s for %i seconds" % (mutee, deltatime.seconds))
#        if(len(outputList) > 0):
#            irclib.sendChannelMessage("My current muting list: %s" % (string.join(outputList, ", ")))
#        else:
#            irclib.sendChannelMessage("I don't know of any mutings.")
#===============================================================================

    def onChannelMessage(self, irclib, source, message):
        if((len(message.split()) >= 2) and (message.split()[0] == "!mute")):
            if(source.isAdmin()):
                nick = message.split()[1]
                self.mute(irclib, source, nick)
            else:
                irclib.sendChannelMessage("What makes you think that I would accept a command from you? :P")
        elif((len(message.split()) >= 2) and (message.split()[0] == "!unmute")):
            if(source.isAdmin()):
                nick = message.split()[1]
                self.unmute(irclib, nick)
            else:
                irclib.sendChannelMessage("What makes you think that I would accept a command from you? :P")
#===============================================================================
#        elif(message == "!mutelist"):
#            self.printMuteList(irclib)
#===============================================================================
#===============================================================================
#        elif(message == "!coup"):
#            if(self.isFriend(irclib, source)):
#                self.revolution(irclib, source)
#            else:
#                irclib.sendChannelMessage("What makes you think that I would accept a command from you? :P")
#===============================================================================





#Unit-test
if __name__ == "__main__":
    class AuthPluginMock:
        def isFriend(self, irclib, name):
            return(name == "friend")
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

    import time
    a = MutingPlugin(PluginInterfaceMock())
    a.onChannelMessage(IrcLibMock(), "source", "!mute anybody")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "!mute aaa")
    print "==============="
    time.sleep(3)
    a.onChannelMessage(IrcLibMock(), "friend", "!mutelist")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "!unmute bbb")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "!mute bbb")
    print "==============="
    time.sleep(3)
    a.onChannelMessage(IrcLibMock(), "friend", "!mutelist")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "!unmute aaa")
    print "==============="
    time.sleep(3)
    a.onChannelMessage(IrcLibMock(), "friend", "!mutelist")
    