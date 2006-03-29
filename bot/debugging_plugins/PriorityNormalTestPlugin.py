from modules import PluginInterface

class PriorityNormalTestPlugin:

    @PluginInterface.Priorities.prioritized(PluginInterface.Priorities.PRIORITY_NORMAL)
    def onChannelMessage(self, irclib, source, message):
        irclib.sendChannelMessage("normal")
