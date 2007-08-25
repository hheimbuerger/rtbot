class PingPlugin:
   
    #TODO: some kind of flood protection against /msg RTBot Ping DoS'ses :D
    #But Authentication plugin would need it so much more.
   
    def getVersionInformation(self):
        return("$Id: PingPlugin.py 423 2007-08-25 09:26:16Z badpazzword $")

    def onPrivateMessage(self, irclib, source, msg):
        if(msg.lower() == "ping"):
            irclib.sendPrivateMessage(source, "Pong")
            
    def onChannelMessage(self, irclib, source, msg):
       	
        if(msg == "Earth to RTBot, Earth to RTBot, can you read us?"):
            irclib.sendChannelMessage("Strong and clear, Earth.")
            
#        if(msg == "%s to RTBot, %s to RTBot, can you read me?" % (nick, nick):
#            irclib.sendChannelMessage("Strong and clear, %s." % nick)