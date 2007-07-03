import re, pickle



class RespectahPlugin:
    commandRE = re.compile("(\\S*?)\\.(\\S*?)\\((\\S*?)\\)((\\+\\+)|(--))")
    commandREPE = re.compile("(\\S*?)\\.(\\S*?)\\((\\S*?)\\)([\\+-]=)(\\S*)")

    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        self.data = {}
        try:
            file = open("resources/respectah_data.pickle", "rb")
            self.data = pickle.load(file)
            file.close()
        except IOError:
            self.data = {}
        except EOFError:
            self.data = {}

    def saveList( self ):
        file = open("resources/respectah_data.pickle", "wb" )
        pickle.dump(self.data, file)
        file.close()

    def getVersionInformation(self):
        return("$Id: RespectahPlugin.py 260 2006-05-23 22:37:56Z Ksero $")

    def printCurrentList(self, irclib, user, attribute):
        if(self.data.has_key(user)):
            if(self.data[user].has_key(attribute)):
                if(len(self.data[user][attribute].items())):
                    results = []
                    for (target, value) in self.data[user][attribute].items():
                        results.append("%s = %i" % (target, value))
                    irclib.sendChannelMessage("%s's %s: %s" % (user, attribute, ", ".join(results)))
                else:
                    irclib.sendChannelMessage("You never gave %s to anybody!" % (attribute))
            else:
                irclib.sendChannelMessage("You never used that attribute!")
        else:
            irclib.sendChannelMessage("You never gave any respectah!")

    def printCurrentListAll(self, irclib, user):
        if(self.data.has_key(user)):
            results = [] 
            for (attribute, target) in self.data[user].items():
                if ( attribute not in results ):
                    results.append("%s" % (attribute))
            if (len(results)):
                irclib.sendChannelMessage("%s's %s" % (user, results))
            else:
                irclib.sendChannelMessage("You never gave any respectah!")
    
    def setValue(self, user, attribute, target, op):
        currentValue = self.data.setdefault(user, {}).setdefault(attribute, {}).setdefault(target, 0)
        if(currentValue + op == 0):
            del self.data[user][attribute][target]
            if(len(self.data[user][attribute]) == 0):
                del self.data[user][attribute]
                if(len(self.data[user]) == 0):
                    del self.data[user]
        else:
            self.data[user][attribute][target] = currentValue + op
        self.saveList()

    def getValue(self, user, attribute, target, op):
        return(self.data.get(user, {}).get(attribute, {}).get(target, 0))

    def onChannelMessage(self, irclib, source, message):
        if(source.isAuthed()):
            name = source.dataStore.getAttribute("authedAs")
            
            # "list respect"
            if((len(message.split()) >= 2) and (message.split()[0] == "list")):
                attribute = message.split()[1]
                if attribute == "*":
                    self.printCurrentListAll(irclib, name)
                else:
                    self.printCurrentList(irclib, name, attribute) 

            # "self.respect(something)++"
            result = RespectahPlugin.commandRE.search(message)
            if(result):
                object = result.group(1)
                attribute = result.group(2)
                target = result.group(3)
                operation = result.group(4)
                if((object == name) or (object == "self")):
                    if(operation == "++"):
                        op = +1
                    else:
                        op = -1
                    self.setValue(name, attribute, target, op)
                    irclib.sendChannelMessage("%s's current %s for %s is %i." % (name, attribute, target, self.getValue(name, attribute, target, op)))

            # "self.respect(something)+=value"
            result = RespectahPlugin.commandREPE.search(message)
            if(result):
                object = result.group(1)
                attribute = result.group(2)
                target = result.group(3)
                operation = result.group(4)
                value = result.group(5)
                if((object == name) or (object == "self")):
                    irclib.sendChannelMessage("object: %s attribute: %s target: %s operation: %s value: %s" % (object, attribute, target, operation, value))
                    if(value.isdigit()):
                        if(operation == "+="):
                            op = +int(value)
                        else:
                            op = -int(value)
                        self.setValue(name, attribute, target, op)
                        irclib.sendChannelMessage("%s's current %s for %s is %i." % (name, attribute, target, self.getValue(name, attribute, target, op)))

#Unit-test
if __name__ == "__main__":
    class AuthPluginMock:
        def isFriend(self, irclib, name):
            if(name == "friend"):
                return(name)
            else:
                return(None)
        def triggerModeUpdate(self, irclib):
            irclib.sendChannelMessage("AuthPlugin: updating!")

    class PluginInterfaceMock:
        def getPlugin(self, name):
            return(AuthPluginMock())

    class IrcLibMock:
        nickname = "RTBot"
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def sendChannelEmote(self, text):
            print "* %s" % (text)

    a = RespectahPlugin(PluginInterfaceMock())
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.respect(a)++ def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.respect(a)++ def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.respect(a)-- def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "somebodyelse", "abc friend.respect(a)-- def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc somebodyelse.respect(a)-- def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.respect(b)++ def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "abc friend.stuff(a)++ def")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "list respect")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "list stuff")
    print "==============="
    a.onChannelMessage(IrcLibMock(), "friend", "list nothing")
    print "==============="
