from modules import PluginInterface

class StatusPlugin:
    def __init__(self, pluginInterface):
        self.pi = pluginInterface
        
    @PluginInterface.Priorities.prioritized(PluginInterface.Priorities.PRIORITY_NORMAL)
    def onChannelMessage(self, irclib, source, message):
        def reply(message):
            irclib.sendChannelMessage(message)
        
        words = message.split()
        command = words[0]
        if command == "!status":
            for pf in self.pi.pluginFiles.values():
                if pf.enabled:
                    deps = pf.plugin.dependencies.keys()
                    depsOnline = pf.plugin.Online()
                else:
                    deps = []
                    depsOnline = "Unknown (plugin disabled)"
                reply("%s: Enabled: %s. Dependencies: %s. Dependencies online: %s" % (pf.filepath.basename(), pf.enabled, deps, depsOnline))
        if command == "!disable":
            try:
                self.pi.setPluginStateByFilename(words[1],False)
                reply("Disabled the %s plugin" % words[1])
            except:
                reply("Can't find the %s plugin" % words[1])
        if command == "!enable":
            try:
                self.pi.setPluginStateByFilename(words[1],True)
                reply("Enabled the %s plugin" % words[1])
            except:
                reply("Can't find the %s plugin" % words[1])