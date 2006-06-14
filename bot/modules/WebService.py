from threading import Thread
from SimpleXMLRPCServer import SimpleXMLRPCServer
import string
import md5

class WebService(Thread):
    this = None

    def __init__(self, botManagerReference, host, port):
        Thread.__init__(self, group=None, target=None, name="WebServiceThread", args=(), kwargs={})
        self.server = SimpleXMLRPCServer(addr=(host, port), logRequests=False)
        self.setDaemon(True)
        self.botManager = botManagerReference
        self.logWatchClients = {}
        WebService.this = self

    def run(self):
        self.server.register_instance(self, False)
        self.server.serve_forever()

    def addLogMessage(self, message):
        for (id, data) in self.logWatchClients.items():
            data['latestMessages'].append(message)
    
#  def status(self, plugin):
#        # returns a tuple of (pluginName, status, revision, commit, creator)
#        try:
#            return self.botManager.pluginInterface.getPluginWrapper(plugin).getStatus()
#        except KeyError:
#            return "The plugin %s could not be found" % plugin

    def enablePlugin(self, plugin):
        try:
            self.botManager.pluginInterface.setPluginState(plugin, True)
            return ""
        except KeyError:
            return "The plugin %s could not be found" % plugin

    def disablePlugin(self, plugin):
        try:
            self.botManager.pluginInterface.setPluginState(plugin, False)
            return ""
        except KeyError:
            return "The plugin %s could not be found" % plugin

    def pluginStatusList(self):
        list = [[wrapper.pluginName, wrapper.enabled, wrapper.online()] for wrapper in self.botManager.pluginInterface.pluginWrappers.values() ]
        list.sort()
        return(list)

#	def PluginList(self):
#		list = self.botManager.pluginInterface.getPluginNames()
#		list.sort()
#		#return("Plugins: " + string.join(list, ", "))
#		return(list)

    def retrieveLogWatchTicket(self, nick, components, filters):
        id = md5.new(nick).hexdigest()
        self.logWatchClients[id] = {'latestMessages': [], 'components': components, 'filters': filters}
        return(id)

    def getLogMessages(self, id):
        #print "getLogMessages called"
        if(self.logWatchClients[id]['latestMessages']):
            messages = self.logWatchClients[id]['latestMessages'].reverse()
        else:
            messages = []
        #print "messages: %s" % (messages)
        self.logWatchClients[id]['latestMessages'] = []
        return(messages)
        
    def stopWatching(self, id):
        del(self.logWatchClients[id])
        return

    def getStatus(self):
        return([self.botManager.getState(), len(self.botManager.pluginInterface.pluginWrappers), len(self.botManager.pluginInterface.eventHandlers)])



if __name__ == "__main__":
	import sys
	# launch with command line argument "client" to simulate an XML-RPC call
	if(len(sys.argv) >= 2 and sys.argv[1] == "client"):
		import xmlrpclib, time
		sp = xmlrpclib.ServerProxy("http://localhost:8000/")
		id = sp.retrieveLogWatchTicket()
		print id
		while True:
			messages = sp.getLogMessages(id)
			print "Messages: " + str(messages)
			print "Waiting 5s..."
			time.sleep(5)

	else:
		ws = WebService()
		ws.start()
		import time
		while True:
			time.sleep(1)
