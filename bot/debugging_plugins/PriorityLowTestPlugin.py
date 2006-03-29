from modules import PluginInterface

class PriorityLowTestPlugin:

    @PluginInterface.Priorities.prioritized(PluginInterface.Priorities.PRIORITY_LOW)
    def onChannelMessage(self, irclib, source, message):
        irclib.sendChannelMessage("low")
