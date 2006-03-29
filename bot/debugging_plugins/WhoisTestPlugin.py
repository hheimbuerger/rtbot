from modules import LogLib

class WhoisTestPlugin:
    
    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        
    def onChannelMessage(self, irclib, source, message):
        if((len(message.split()) >= 2) and (message.split()[0] == "!whois")):
            irclib.doWhois(message.split()[1])

    def onWhoisResult(self, irclib, nick, host, userinfo):
        irclib.sendChannelMessage("WHOIS %s: HOST=%s, USERINFO=%s" % (nick, host, userinfo))
