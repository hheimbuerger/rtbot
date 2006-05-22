# These imports are only used for the unit-test code, they are ignored when used as a plugin (but all of them are automatically imported by the PluginInterface)
import re, logging

class VoiceChatPlugin:
    import csv, os, pickle, exceptions
    
    vcDialects = {}
    DialectPreferences = {"test":"default"}
    PreferenceFilename = "resources/VCDialectPreferences.lst"
    
    def __init__(self, pluginInterface):
        # Save reference to the pluginInterface
        self.pluginInterfaceReference = pluginInterface

        # If file present - load dialect preferences
        if self.os.path.isfile(self.PreferenceFilename) and self.os.path.getsize(self.PreferenceFilename) > 0:
            file = open(self.PreferenceFilename, "r")
            self.DialectPreferences = self.pickle.load(file)
            file.close()
        for file in self.os.listdir("resources/"):
            filepath = "resources/" + file
            if((file[:4] == "VCs.") and (file[-4:] == ".csv")):
                dialect = file[4:-4]
                #print dialect
                self.vcDialects[dialect] = {}
                file = open(filepath, "r")
                reader = self.csv.reader(file)
                for row in reader:
                    #print row[0] + " = " + row[1]
                    self.vcDialects[dialect][row[0].lower()] = row[1]
                file.close()

    def getVersionInformation(self):
        return("$Id$")

    def getCanonicalName(self, rawName):
        # retrieve AuthenticationPlugin
        authenticationPlugin = self.pluginInterfaceReference.getPluginByClassname("AuthenticationPlugin")
        if(authenticationPlugin == None):
            logging.info("ERROR: VoiceChatPlugin didn't succeed at lookup of AuthenticationPlugin during execution of getCanonicalName()")
            return(rawName)
        else:
            return(authenticationPlugin.getCanonicalName(rawName))

    # Note: SetVCDialectPreference does not check whether the dialect exists or not.
    def SetVCDialectPreference(self, user, dialect):
        self.DialectPreferences[user] = dialect
        file = open(self.PreferenceFilename, "w")
        self.pickle.dump(self.DialectPreferences, file)
        file.close()
    # This might not return a valid dialect
    def GetVCDialectPreference(self, user):
        if user in self.DialectPreferences:
            return self.DialectPreferences[user]
        else:
            return "default"

    def listAll(self):
        for a in self.vcDialects.keys():
            print a
        for b in self.vcDialects[a].keys():
            print b + " = " + self.vcDialects[a][b]
        print

    def getText(self, dialect, keyseq):
        if not dialect in self.vcDialects:
            return "I'm sorry, but can't find the " + dialect + " voice chat dialect"

#        if (not keyseq[0] in "'`~") or len(keyseq) < 2:
#            return("Invalid syntax! Try 'XX. (For example, 'gu or '1)")
#        searchString = keyseq[1:].lower()
        if (keyseq[0] in "'`~"):
            searchString = keyseq[1:].lower()
        else:
            searchString = keyseq.lower()

        if(searchString in self.vcDialects[dialect]):
            return(dialect + ": '" + searchString + " = " + self.vcDialects[dialect][searchString])
        else:
            return("That VC isn't part of the %s dialect!" % (dialect))

    def getVC(self, dialect, queryWords):
        if not dialect in self.vcDialects:
            return "I'm sorry, but can't find the " + dialect + " voice chat dialect"
            
        theRE = ""
        for a in queryWords:
            theRE += ".*?" + re.escape(a.lower())
        for a in self.vcDialects[dialect].items():
            try:
                if(re.match(theRE, a[1].lower())):
                    return(dialect + ": '" + a[0] + " = " + a[1])
            except:
                pass 
        return("I'm not aware of a VC with that content in the %s dialect." % (dialect))

    # Parses the different commands and acts accordingly.
    # replyfunc is called with an appropriate response as argument (it should be a function that takes a string)
    def handleMessage(self, msg, source, replyfunc):
        if(len(msg.split()) > 0):
            messageWords = msg.split()
            command = messageWords[0]
            numTokens = len(messageWords)
            user = self.getCanonicalName(source)
        
            # vc 'XXX - either fetch dialect from preference or use default
            if numTokens == 2 and command == "vc":
                dialect = self.GetVCDialectPreference(user)
                chatShortcut = messageWords[1]
                replyfunc(self.getText(dialect, chatShortcut))
            
            # vc dialect 'XXX - read dialect from message                     
            elif numTokens == 3 and command == "vc":
                (dialect, chatShortcut) = messageWords[1:3]
                replyfunc(self.getText(dialect, chatShortcut))
            
            # findvc dialect <keywords> - read dialect from message
            elif numTokens >= 3 and command == "findvc" and msg.split()[1] in self.vcDialects:
                dialect = messageWords[1]
                query   = messageWords[2:]
                replyfunc(self.getVC(dialect, query))
                
            # findvc <keywords> - read dialect from preference or use default                    
            elif numTokens >= 2 and command == "findvc":
                dialect = self.GetVCDialectPreference(user)
                query = messageWords[1:]
                replyfunc(self.getVC(dialect, query))
            
            # vcpref preference
            elif numTokens >= 2 and command == "vcpref":
                dialect = messageWords[1]
                if dialect in self.vcDialects:
                    self.SetVCDialectPreference(user, dialect)
                    replyfunc("Setting VC dialect for " + user)
                else:
                    replyfunc("I'm sorry, but can't find the " + dialect + " voice chat dialect, " + source)
        
    def onPrivateMessage(self, irclib, source, msg):
        self.handleMessage(msg, source, (lambda reply: irclib.sendPrivateMessage(source, reply)))

    def onChannelMessage(self, irclib, source, msg):
        self.handleMessage(msg, source, (lambda reply: irclib.sendChannelMessage(reply)))


#Unit-test
if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
    
    class FakeAuthenticationPlugin:
        def getCanonicalName(self, name):
            return name
    
    class FakePluginInterface:
        def getPluginByClassname(self, name):
            if name == "AuthenticationPlugin":
                return FakeAuthenticationPlugin()
    
    class FakeFailingPluginInterface:
        def getPluginByClassname(self, name):
            return None

    a = VoiceChatPlugin(FakePluginInterface())
    #a.listAll()
    a.onChannelMessage(FakeIrcLib(), "source", "findvc default fir")
    a.onChannelMessage(FakeIrcLib(), "source", "findvc CortDialect heh heh")
    a.onChannelMessage(FakeIrcLib(), "source", "vc default ~ra")
    a.onChannelMessage(FakeIrcLib(), "source", "vc '1")
    a.onChannelMessage(FakeIrcLib(), "source", "findvc affir")
    a.onChannelMessage(FakeIrcLib(), "tester", "vcpref TigereyeDialect")
    a.onChannelMessage(FakeIrcLib(), "tester", "vc `tqa")  # Should be "Out of ammo - interesting"
    a.onChannelMessage(FakeIrcLib(), "tester", "vcpref Nonexistant")
    
    b = VoiceChatPlugin(FakeFailingPluginInterface())
    b.onChannelMessage(FakeIrcLib(), "foo", "vcpref bar") # Should print AuthenticationPlugin error message