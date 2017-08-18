import csv, os, pickle, re

from plugin_base import BasePlugin


class VoiceChatPlugin(BasePlugin):

    vcDialects = {}
    DialectPreferences = {"test": "default"}
    PreferenceFilename = "resources/VCDialectPreferences.lst"
    
    def __init__(self):
        # If file present - load dialect preferences
        if os.path.isfile(self.PreferenceFilename) and os.path.getsize(self.PreferenceFilename) > 0:
            with open(self.PreferenceFilename, "rb") as f:
                self.DialectPreferences = pickle.load(f)
        for file in os.listdir("resources/"):
            filepath = "resources/" + file
            if((file[:4] == "VCs.") and (file[-4:] == ".csv")):
                dialect = file[4:-4]
                #print dialect
                self.vcDialects[dialect] = {}
                file = open(filepath, "r")
                reader = csv.reader(file)
                for row in reader:
                    #print row[0] + " = " + row[1]
                    self.vcDialects[dialect][row[0].lower()] = row[1]
                file.close()

    # Note: SetVCDialectPreference does not check whether the dialect exists or not.
    def SetVCDialectPreference(self, user, dialect):
        self.DialectPreferences[user] = dialect
        file = open(self.PreferenceFilename, "w")
        pickle.dump(self.DialectPreferences, file)
        file.close()

    # This might not return a valid dialect
    def GetVCDialectPreference(self, user):
        if user in self.DialectPreferences:
            return self.DialectPreferences[user]
        else:
            return "default"

    def listAll(self):
        for a in self.vcDialects.keys():
            print(a)
        for b in self.vcDialects[a].keys():
            print(b + " = " + self.vcDialects[a][b])
        print()

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
    async def on_message(self, channel, user, message):
        if(len(message.split()) > 0):
            messageWords = message.split()
            command = messageWords[0]
            numTokens = len(messageWords)
        
            # vc 'XXX - either fetch dialect from preference or use default
            if numTokens == 2 and command == "vc":
                dialect = self.GetVCDialectPreference(user.id)
                chatShortcut = messageWords[1]
                await channel.reply(self.getText(dialect, chatShortcut))
            
            # vc dialect 'XXX - read dialect from message                     
            elif numTokens == 3 and command == "vc":
                (dialect, chatShortcut) = messageWords[1:3]
                await channel.reply(self.getText(dialect, chatShortcut))
            
            # findvc dialect <keywords> - read dialect from message
            elif numTokens >= 3 and command == "findvc" and message.split()[1] in self.vcDialects:
                dialect = messageWords[1]
                query   = messageWords[2:]
                await channel.reply(self.getVC(dialect, query))
                
            # findvc <keywords> - read dialect from preference or use default                    
            elif numTokens >= 2 and command == "findvc":
                dialect = self.GetVCDialectPreference(user.id)
                query = messageWords[1:]
                await channel.reply(self.getVC(dialect, query))
            
            # vcpref preference
            elif numTokens >= 2 and command == "vcpref":
                dialect = messageWords[1]
                if dialect in self.vcDialects:
                    self.SetVCDialectPreference(user.id, dialect)   # TODO: would be nice to able to just store 'user' as the identity here and then behind the scenes it would be the internal ID that gets serialized/deserialized
                    await channel.reply("Setting VC dialect for " + user.name)
                else:
                    await channel.reply("I'm sorry, but can't find the " + dialect + " voice chat dialect, " + user.name)
