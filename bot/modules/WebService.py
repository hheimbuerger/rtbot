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
        return (plugin, ["1.0", "running"])

    def PluginList(self):
        list = self.botManager.pluginInterface.getPluginNames()
        list.sort()
        #return("Plugins: " + string.join(list, ", "))
        return(list)



if __name__ == "__main__":
    ws = WebService()
    ws.start()
    import time
    while True:
        time.sleep(1)
