class EchoPlugin:

    def getVersionInformation(self):
        return("$Id: EchoPlugin.py 123 2005-12-16 03:36:07Z ksero $")

    def onChannelMessage(self, irclib, source, message):
        irclib.sendChannelMessage("You said: %s" % message)

    def onChannelEmote(self, irclib, source, emote):
        irclib.sendChannelEmote("saw you emoting: %s" % emote)

    def onPrivateMessage(self, irclib, source, message):
        irclib.sendPrivateMessage(source, "You privately said: %s" % message)

    def onPrivateEmote(self, irclib, source, emote):
        irclib.sendPrivateEmote(source, "saw you privately emoting: %s" % emote)
