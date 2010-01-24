class SamplePlugin:

    def getVersionInformation(self):
        return("$Id: SamplePlugin.py 163 2006-02-08 14:28:11Z cortex $")

    def onChannelMessage(self, irclib, source, message):
        if(message == "!showtopic"):
            irclib.sendChannelMessage("The current channel topic is: %s" % (irclib.channelTopic))
        elif(message == "!settopic"):
            irclib.setChannelTopic("test2 word4 word5")
