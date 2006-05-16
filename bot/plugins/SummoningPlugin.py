class SummoningPlugin:
    summonCommand = "Kal Vas Xen"

    def getVersionInformation(self):
        return("$Id: SummoningPlugin.py 163 2006-02-08 14:28:11Z cortex $")

    def onChannelMessage(self, irclib, source, message):
        if(message[:len(self.summonCommand)] == self.summonCommand):
            target = message[len(self.summonCommand)+1:]
            if(target in irclib.getUserList().getPureList()):
                irclib.sendPrivateNotice(target, "You have been summoned by %s!" % (source))
                irclib.sendChannelEmote("does a ritual dance.")
                irclib.sendChannelMessage("Oh, great %s, from the depths of idling, we summon thee!" % (target))
            else:
                irclib.sendChannelEmote("does a ritual dance.")
                irclib.sendChannelMessage("Oh, great %s, from the depths of idling, we summon thee!" % (target))
                irclib.sendChannelEmote("fizzles. :(")
