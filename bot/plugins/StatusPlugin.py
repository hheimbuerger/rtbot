import logging

class StatusPlugin:
    def __init__(self, pluginInterface):
        self.pi = pluginInterface
        
    def handleMessage(self, reply, source, message):
        words = message.split()
        command = words[0]
        if command == "!status" and len(words) == 2:
            try:
                plugin = self.pi.getPluginWrapper(words[1])
                reply("%s: Enabled: %s. Dependencies: %s. Plugin online: %s" % (words[1], plugin.enabled, plugin.getDependencies(), plugin.online()))
            except KeyError:
                reply("Could not find the plugin %s" % words[1])
        if command == "!disable" and len(words) == 2:
            try:
                self.pi.setPluginState(words[1],False)
                reply("Disabled the %s plugin" % words[1])
            except KeyError:
                reply("Can't find the %s plugin" % words[1])
        if command == "!enable" and len(words) == 2:
            try:
                self.pi.setPluginState(words[1],True)
                reply("Enabled the %s plugin" % words[1])
            except KeyError:
                reply("Can't find the %s plugin" % words[1])
                        
    def onChannelMessage(self, irclib, source, message):
        def reply(message):
            irclib.sendChannelMessage(message)
        self.handleMessage(reply, source, message)
        
    def onPrivateMessage(self, irclib, source, message):
        def reply(message):
            irclib.sendChannelMessage(message)
        self.handleMessage(reply, source, message)
