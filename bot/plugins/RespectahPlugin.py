import re, pickle
from lib import pastebin

class RespectahPlugin:
    commandRE = re.compile("(\\S*?)\\.(\\S*?)\\((\\S*?)\\)((\\+\\+)|(--))")
    commandREPE = re.compile("(\\S*?)\\.(\\S*?)\\((\\S*?)\\)([\\+-]=)(\\S*)")
    commandREEQ = re.compile("(\\S*?)\\.(\\S*?)\\((\\S*?)\\)=(\\S*)")

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
        return("$Id$")

    def printCurrentList(self, irclib, user, attribute):
        if not self.data.has_key(user):
            irclib.sendChannelMessage("You never gave any respectah!")
            return
        if not self.data[user].has_key(attribute):
            irclib.sendChannelMessage("You never used that attribute!")
            return
        if not len(self.data[user][attribute].items()):
            irclib.sendChannelMessage("You never gave %s to anybody!" % (attribute))
            return
        
        
        results = self.data[user][attribute].items()
        results.sort( key=(lambda pair: -pair[1]) ) #from highest to lowest
        display_these_many = 5
        
        topResults = results[:display_these_many]
        
        header = "%s's %s" % (user, attribute)
        
        ircMessage = header + ": "
        ircMessage += ", ".join("%s %s" % (target, "> 9000" if value > 9000 else "= %d" % value)
                                for (target, value) in topResults)

        if len(results) > display_these_many:
            fullMessage = header + ":\n\n"
            fullMessage += "\n".join("\t%s = %i" % (target, value) for (target, value) in results)
            url = pastebin.postToPastebin(fullMessage, title = header)
            ircMessage += "; %s for all %d" % (url, len(results))

        irclib.sendChannelMessage(ircMessage)          

    def printCurrentListAll(self, irclib, user):
        if(self.data.has_key(user)):
            keys = sorted(self.data[user], key = lambda x: -len(self.data[user][x]))
            display_these_many = 7
            topKeys = keys[:display_these_many]
            
            if (len(keys)):
                header = "%s's respectah lists" % user
        
                ircMessage = header + ": "
                ircMessage += ", ".join(topKeys)

                if len(keys) > display_these_many:
                    fullMessage = header + ":\n\n"
                    fullMessage += "\n".join(sorted("\t" + key for key in keys))
                    url = pastebin.postToPastebin(fullMessage, title = header)
                    ircMessage += "; %s for all %d" % (url, len(keys))

                irclib.sendChannelMessage(ircMessage)
            else:
                irclib.sendChannelMessage("You never gave any respectah!")
        else:
            irclib.sendChannelMessage("I don't know them.")
    
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

    def setAbsValue(self, user, attribute, target, op):
        currentValue = self.data.setdefault(user, {}).setdefault(attribute, {}).setdefault(target, 0)
        if(op == 0):
            del self.data[user][attribute][target]
            if(len(self.data[user][attribute]) == 0):
                del self.data[user][attribute]
                if(len(self.data[user]) == 0):
                    del self.data[user]
        else:
            self.data[user][attribute][target] = op
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
                elif ( attribute.find( "." ) != -1 ):
                    DotPos = attribute.find( "." )
                    name = attribute[0:DotPos]
                    attribute = attribute[DotPos+1:999]
                    if ( attribute == "*" ):
                        self.printCurrentListAll(irclib, name)
                    else:
                        self.printCurrentList(irclib, name, attribute)                     
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
                    newValue = self.getValue(name, attribute, target, op)
                    newValueString = "over nine thousand" if newValue > 9000 else "%d" % newValue
                    if "over" in newValueString and "-" in operation: newValueString = "still " + newValueString
                    irclib.sendChannelMessage("%s's current %s for %s is %s." % (name, attribute, target, newValueString))

            # "self.respect(something)+=value"
            result = RespectahPlugin.commandREPE.search(message)
            if(result):
                object = result.group(1)
                attribute = result.group(2)
                target = result.group(3)
                operation = result.group(4)
                value = result.group(5)
                if((object == name) or (object == "self")):
                    if(value.isdigit()):
                        if(operation == "+="):
                            op = +int(value)
                        else:
                            op = -int(value)
                        self.setValue(name, attribute, target, op)
                    newValue = self.getValue(name, attribute, target, op)
                    newValueString = "over nine thousand" if newValue > 9000 else "%d" % newValue
                    if "over" in newValueString and "-" in operation: newValueString = "still " + newValueString
                    irclib.sendChannelMessage("%s's current %s for %s is %s." % (name, attribute, target, newValueString))

            # "self.respect(something)=value"
            result = RespectahPlugin.commandREEQ.search(message)
            if(result):
                object = result.group(1)
                attribute = result.group(2)
                target = result.group(3)
                value = result.group(4)
                if((object == name) or (object == "self")):
                    if(value.isdigit()):
                        op = int(value)
                        self.setAbsValue(name, attribute, target, op)
                    newValue = self.getValue(name, attribute, target, op)
                    newValueString = "still over nine thousand" if newValue > 9000 else "%d" % newValue
                    irclib.sendChannelMessage("%s's current %s for %s is %s." % (name, attribute, target, newValueString))



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
