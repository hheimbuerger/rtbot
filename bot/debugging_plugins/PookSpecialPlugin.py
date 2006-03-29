class PookSpecialPlugin:
    def onChannelMessage(self, irclib, source, message):
        if(source == "Pook"):
            irclib.sendChannelMessage("http://www.freeallegiance.org/pook/pook-hottie%s.jpg" % (str(int(random.random() * 45))))
