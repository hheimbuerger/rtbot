class SamplePlugin:

    def getVersionInformation(self):
        return("$Id$")

    def onChannelMessage(self, irclib, source, message):
        if(message == "!sample"):
            irclib.sendChannelEmote("emotes")
            irclib.sendChannelMessage("Hello, brave new world!")
