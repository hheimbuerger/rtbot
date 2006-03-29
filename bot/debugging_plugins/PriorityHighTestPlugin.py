from modules import PluginInterface

class PriorityHighTestPlugin:

    @PluginInterface.Priorities.prioritized(PluginInterface.Priorities.PRIORITY_HIGH)
    def onChannelMessage(self, irclib, source, message):
        irclib.sendChannelMessage("high")
