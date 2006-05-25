from threading import Thread
from SimpleXMLRPCServer import SimpleXMLRPCServer
import string

class WebService(Thread):
    def __init__(self, botManagerReference, host, port):
        Thread.__init__(self, group=None, target=None, name="WebServiceThread", args=(), kwargs={})
        self.server = SimpleXMLRPCServer(addr=(host, port), logRequests=False)
        self.setDaemon(True)
        self.botManager = botManagerReference

    def run(self):
        self.server.register_instance(self, False)
        self.server.serve_forever()

    def status(self, plugin):
        # returns a tuple of (pluginName, status, revision, commit, creator)
        try:
            return self.botManager.pluginInterface.getPluginWrapper(plugin).getStatus()
        except KeyError:
            return "The plugin %s could not be found" % plugin
    
    def setPluginState(self, plugin, newState):
        try:
            self.botManager.pluginInterface.setPluginState(plugin, newState)
        except KeyError:
            return "The plugin %s could not be found" % plugin

    def PluginList(self):
        list = self.botManager.pluginInterface.getPluginNames()
        list.sort()
        return list
    
    def pluginStatusList(self):
        return self.botManager.pluginInterface.getStatus()



if __name__ == "__main__":
    ws = WebService()
    ws.start()
    import time
    while True:
        time.sleep(1)
