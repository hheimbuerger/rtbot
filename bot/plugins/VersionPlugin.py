import re

class VersionPlugin:

    def __init__(self, pluginInterface):
        self.pluginInterface = pluginInterface
    
    def getVersionInformation(self):
        return("$Id$")
  
    def getCoreVersion(self):
        return("5.0")
    
    def getVersionOutput(self):
        result = "Core version: " + self.getCoreVersion()
        list = self.pluginInterface.getPluginNames()
        list.sort()
        result += " / Plugins: " + ", ".join(list)
        return result

    def getPluginVersion(self, requestedPlugin, replyfunc):
        plugin = self.pluginInterface.getPlugin(requestedPlugin)
        if plugin:
            if hasattr(plugin, "getVersionInformation"):
                reobj = re.match("\$Id: (.*) (.*) (.*) (.*) (.*) \$", plugin.getVersionInformation())
                if(reobj):
                    replyfunc("Filename: " + reobj.group(1))
                    replyfunc("Revision: " + reobj.group(2))
                    replyfunc("Commit date: " + reobj.group(3))
                    replyfunc("Commit time: " + reobj.group(4))
                    replyfunc("Last author: " + reobj.group(5))
                else:
                    replyfunc("Plugin didn't return a valid version information.")
            else:
                replyfunc("No version information available for this plugin.")
        else:
            replyfunc("Couldn't find plugin.")

    # Parses the different commands and acts accordingly.
    # replyfunc is called with an appropriate response as argument (it should be a function that takes a string)
    def handleMessage(self, msg, replyfunc):
        words = msg.split()
        if(len(words) > 0):
            command = words[0]
            if command == "version":
                if len(words) > 1:
                    self.getPluginVersion(words[1], replyfunc)
                else:
                    replyfunc(self.getVersionOutput())

    def onPrivateMessage(self, irclib, source, msg):
        self.handleMessage(msg, lambda reply: irclib.sendPrivateMessage(source, reply))
    def onChannelMessage(self, irclib, source, msg):
        self.handleMessage(msg, lambda reply: irclib.sendChannelMessage(reply))
