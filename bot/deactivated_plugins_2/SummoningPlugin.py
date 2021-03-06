class SummoningPlugin:
    helpCommand = "listspells"
    summonCommand = "Kal Vas Xen"
    banishCommand = "An Vas Xen"
    summonAllCommand = "An Zu Grav!"
    wisdomCommand = "In Bet Wis!"

    def getVersionInformation(self):
        return("$Id: SummoningPlugin.py 353 2006-12-18 11:38:11Z terralthra $")

    @classmethod
    def getDependencies(self):
        return(["WarWisdomPlugin"])

    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface

    def summon(self, irclib, sourceNick, targetNick):
        if(irclib.getUserList().has_key(targetNick)):
            irclib.sendPrivateNotice(irclib.getUserList()[targetNick], "You have been summoned by %s!" % (sourceNick))
            irclib.sendChannelEmote("does a ritual dance.")
            irclib.sendChannelMessage("Oh, great %s, from the depths of idling, we summon thee!" % (targetNick))
        else:
            irclib.sendChannelEmote("does a ritual dance.")
            irclib.sendChannelMessage("Oh, great %s, from the depths of idling, we summon thee!" % (targetNick))
            irclib.sendChannelEmote("fizzles. :(")

    def banish(self, irclib, sourceNick, targetNick):
        if(irclib.getUserList().has_key(targetNick)):
            irclib.sendPrivateNotice(irclib.getUserList()[targetNick], "You feel your soul exorcized by %s" % (sourceNick))
            irclib.sendChannelEmote("burns some bat guano.")
            irclib.sendChannelMessage("Oh, evil %s, from this channel we banish thee!" % (targetNick))
            irclib.kick(irclib.getUserList()[targetNick], "poof")
        else:
            irclib.sendChannelEmote("burns some bat guano.")
            irclib.sendChannelMessage("Oh, evil %s, from this channel we banish thee!" % (targetNick))
            irclib.sendChannelEmote("fizzles. :(")

    def summonAll(self, irclib, sourceNick):
        irclib.sendChannelMessage("In Uus Xen!")
        irclib.sendChannelEmote("throws something in the fire, and there is a great flash!") 
        for user in irclib.getUserList().values():
            if(user.isAdmin()):
                irclib.sendPrivateNotice(user, "You have been summoned by %s!" % (sourceNick))

    def summonWisdom(self, irclib):
        warWisdomPlugin = self.pluginInterfaceReference.getPlugin("WarWisdomPlugin")
        irclib.sendChannelEmote("channels the ancient martial spirits.") 
        warWisdomPlugin.giveWisdom(irclib)

    def onChannelMessage(self, irclib, source, message):
        if(message[:len(self.summonCommand)] == self.summonCommand):
            targetNick = message[len(self.summonCommand)+1:]
            self.summon(irclib, source.nick, targetNick)
        elif(message[:len(self.banishCommand)] == self.banishCommand):
            targetNick = message[len(self.banishCommand)+1:]
            if(targetNick.lower() == irclib.nickname.lower()):
                self.banish(irclib, irclib.nickname, source.nick)
                irclib.sendChannelMessage("Oops.")
            elif(source.isAdmin()):
                self.banish(irclib, source.nick, targetNick)
            elif(source.getCanonicalNick()[:len("Imm")] == "Imm"):
                irclib.sendChannelMessage("Such a spell may only be cast for a member of my tribe!")
                irclib.sendChannelMessage("Come think of it, you do look like an RT to me...")
                self.banish(irclib, source.nick, targetNick)
            elif(irclib.getUserList()[targetNick].isAdmin()):
                irclib.sendChannelMessage("Such a spell may only be cast for a member of my tribe!")
                self.banish(irclib, irclib.nickname, source.nick)
        elif(message == self.summonAllCommand):
            if(source.isAdmin()):
                self.summonAll(irclib, source.nick)
            else:
                irclib.sendChannelMessage("Such a spell may only be cast for a member of my tribe!")
                self.banish(irclib, irclib.nickname, source.nick)
        elif(message == self.wisdomCommand):
            self.summonWisdom(irclib)
        elif(message == self.helpCommand):
            irclib.sendChannelMessage("I can currently cast:")
            irclib.sendChannelMessage("Summon <target>: Kal Vas Xen <target>")
            irclib.sendChannelMessage("Summon all: An Zu Grav!")
            irclib.sendChannelMessage("Channel wisdom: In Bet Wis!")
            irclib.sendChannelMessage("Banish <target>: An Vas Xen <target>")
            irclib.sendChannelMessage("Start a Werewolf game: In Quas Corp Xen!")
            irclib.sendChannelMessage("Abort a Werewolf game: An Quas Corp Xen!")
            irclib.sendChannelMessage("Remember, spelling, capitalization, and punctuation count.")

        
  

