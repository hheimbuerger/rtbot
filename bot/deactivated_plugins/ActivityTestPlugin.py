

class ActivityTestPlugin:
    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        self.currentActivity = 0.5
        self.dropoffCoefficient = 0.5
        self.activityCoefficient = 0.8

    def onTimer(self, irclib):
        self.currentActivity = -(self.currentActivity ** self.dropoffCoefficient)+1.0
    
    def onChannelMessage(self, irclib, sender, message):
        oldActivity = self.currentActivity
        self.currentActivity = self.currentActivity ** self.activityCoefficient
        if(message == "activity"):
            irclib.sendChannelMessage("Current activity: %.02f-->%.02f" % (oldActivity, self.currentActivity))





if __name__ == "__main__":
    pass