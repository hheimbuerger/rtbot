class SummoningPlugin:
    summonCommand = "Kal Vas Xen"
    banishCommand = "An Vas Xen"

    def getVersionInformation(self):
        return("$Id: SummoningPlugin.py 163 2006-07-27 14:28:11Z terralthra $")

    def __init__(self, pluginInterface):
        self.muteList = {}
        self.pluginInterfaceReference = pluginInterface
        self.revolutionStartingTime = None
        self.revolutionists = []

    @classmethod
    def getDependencies(self):
        return(["AuthenticationPlugin"])

    def isFriend(self, irclib, name):
        # retrieve AuthenticationPlugin
        authenticationPlugin = self.pluginInterfaceReference.getPlugin("AuthenticationPlugin")
        if(authenticationPlugin == None):
          logging.info("ERROR: SummoningPlugin didn't succeed at lookup of AuthenticationPlugin during execution of isFriend()")
          return(False)
        else:
          return(authenticationPlugin.isFriend(irclib, name))

    def getCanonicalName(self, rawName):
        # retrieve AuthenticationPlugin
        authenticationPlugin = self.pluginInterfaceReference.getPlugin("AuthenticationPlugin")
        if(authenticationPlugin == None):
          logging.info("ERROR: SummoningPlugin didn't succeed at lookup of AuthenticationPlugin during execution of getCanonicalName()")
          return(rawName)
        else:
          return(authenticationPlugin.getCanonicalName(rawName))
    
    def getList(self):
        return(self.muteList.keys())

    def summon(self, irclib, source, target):
        if(target in irclib.getUserList().getPureList()):
            irclib.sendPrivateNotice(target, "You have been summoned by %s!" % (source))
            irclib.sendChannelEmote("does a ritual dance.")
            irclib.sendChannelMessage("Oh, great %s, from the depths of idling, we summon thee!" % (target))
        else:
            irclib.sendChannelEmote("does a ritual dance.")
            irclib.sendChannelMessage("Oh, great %s, from the depths of idling, we summon thee!" % (target))
            irclib.sendChannelEmote("fizzles. :(")
        
    def banish(self, irclib, source, target):
        if(target in irclib.getUserList().getPureList()):
            irclib.sendPrivateNotice(target, "You feel your soul exorcized by %s" %(source))
	    irclib.sendChannelEmote("burns some bat guano.")
            irclib.sendChannelMessage("Oh, evil %s, from this channel we banish thee!" % (target))
            irclib.sendRawMsg("KICK %s %s" % (irclib.channel, target))
        else:
            irclib.sendChannelEmote("burns some bat guano.")
            irclib.sendChannelMessage("Oh, evil %s, from this channel we banish thee!" % (target))
            irclib.sendChannelEmote("fizzles. :(")


    def onChannelMessage(self, irclib, source, message):
        if(message[:len(self.summonCommand)] == self.summonCommand):
            target = message[len(self.summonCommand)+1:]
            self.summon(irclib, source, target)
        elif(message[:len(self.banishCommand)] == self.banishCommand):
            target = message[len(self.banishCommand)+1:]
            if(target.lower() == irclib.nickname.lower()):
	        target = source
                self.banish(irclib, source, target)
                irclib.sendChannelMessage("Oops.")
            elif(self.isFriend(irclib, source)):
                self.banish(irclib, source, target)
            else:
                irclib.sendChannelMessage("What makes you think that I would accept a command from you? :P")
                target = source
                self.banish(irclib, source, target)
