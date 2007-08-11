import string
import UserDict
import re
#from modules import LogLib





class UserDataStore:
    def __init__(self):
        self.attributes = {}
        
    def hasAttribute(self, key):
        return(self.attributes.has_key(key))
        
    def getAttribute(self, key):
        return(self.attributes[key])
    
    def getAttributeDefault(self, key, default=None):
        try:
            return(self.attributes[key])
        except KeyError:
            return(default)

    def setAttribute(self, key, value):
        self.attributes[key] = value

    # ignored if the key doesn't exist
    def removeAttribute(self, key):
        if(self.attributes.has_key(key)):
            del self.attributes[key]





class User:
    lastAssignedID = 0
    
    def __init__(self, nick, mode = ""):
        User.lastAssignedID += 1
        self.id = User.lastAssignedID
        self.nick = nick
        self.mode = mode
        self.username = None
        self.host = None
        self.userinfo = None
        self.dataStore = UserDataStore()
        
    def getCanonicalNick(self):
        # (\S+?)(?:\[.*?\]|\|.*?|_{1,2})
        pattern =(r"^"          # nothing in front of this
                  r"(\S+?)"     # username, followed by
                  r"(?:\[.*?\]" # [....] or
                  r"|\|.*?"     # |..... or
                  r"|_{1,2})"   # _ or __
                  r"$")         # nothing after this
        result = re.match(pattern, self.nick)
        if(result):
            return(result.group(1))
        else:
            return(self.nick)
        
    # String: returns the name if possible, and the canonical nick otherwise
    def getAdressingName(self):
        if(self.isAuthed()):
            return(self.getName())
        else:
            return(self.getCanonicalNick())

    # Boolean: has the user been authed (group is irrelevant)?
    def isAuthed(self):
        return(self.dataStore.getAttributeDefault("authedAs", "") != "")
    
    # Boolean: has the user been authed as an admin?
    def isAdmin(self):
        return(self.isAuthed() and self.dataStore.getAttribute("group") == "admin")
    
    def getName(self):
        return(self.dataStore.getAttributeDefault("authedAs"))
    
    def hasOp(self):
        return(self.mode.find("o") != -1)
    
    def hasVoice(self):
        return(self.mode.find("v") != -1)
    




class UserList(UserDict.IterableUserDict):
    def __init__(self):
        self.data = {}



    # ==========================================================================
    # for the IRCLib:
    def onLeave(self, source, channel, reason):
        del self.data[source]

    def onQuit(self, source, reason):
        del self.data[source]

    def onKick(self, source, target, reason, channel):
        del self.data[target]

    def onMode(self, source, targets, flagstring, channel):
        currentMode = '+'
        currentTargetIndex = 0
        for char in flagstring:
            if(char == '+'):
                currentMode = '+'
            elif(char == '-'):
                currentMode = '-'
            elif((char == 'o') or (char == 'v')):
                #LogLib.log.add(LogLib.LOGLVL_DEBUG, str(currentTargetIndex))
                #LogLib.log.add(LogLib.LOGLVL_DEBUG, str(targets))
                #LogLib.log.add(LogLib.LOGLVL_DEBUG, str(targets[currentTargetIndex]))
                #LogLib.log.add(LogLib.LOGLVL_DEBUG, str(self.data[targets[currentTargetIndex]]))
                if(currentTargetIndex < len(targets)):
                    if currentMode == '+':
                        if(not char in self.data[targets[currentTargetIndex]].mode):
                            self.data[targets[currentTargetIndex]].mode += char
                            currentTargetIndex += 1
                    else:
                        if(char in self.data[targets[currentTargetIndex]].mode):
                            self.data[targets[currentTargetIndex]].mode = string.join([x for x in self.data[targets[currentTargetIndex]].mode if x!=char], "")
                            currentTargetIndex += 1

    def onJoin(self, source, channel):
        self.data[source] = User(source)

    def onChangeNick(self, source, target):
        self.data[target] = self.data[source]
        self.data[target].nick = target
        del self.data[source]

    def rebuildUserList(self, namesBuffer):
        self.data = {}
        for list in namesBuffer:
            for name in list.split(" "):
                if(name[0] == "@"):
                    self.data[name[1:]] = User(name[1:], "o")
                elif(name[0] == "+"):
                    self.data[name[1:]] = User(name[1:], "v")
                else:
                    self.data[name] = User(name)

    def reportWhois(self, nick, username, host, userinfo):
        if(nick in self.data):
            self.data[nick].username = username
            self.data[nick].host = host
            self.data[nick].userinfo = userinfo

    def reportWho(self, nick, username, host, userinfo):
        if(nick in self.data):
            self.data[nick].username = username
            self.data[nick].host = host
            self.data[nick].userinfo = userinfo

    # ===========================================================================================
    # NEW ACCESS FUNCTIONS
    # ===========================================================================================
    
    # Boolean:
    def isOnline(self, nick):
        return(self.data.has_key(nick))
        
    # String or Exception:
#    def findByNick(self, nick):
#        if()
    
    # String or None:
#    def findByNickDefault(self, nick, default = None):
#        pass
    
    # String or Exception
    def findByName(self, name):
        user = self.findByNameDefault(name)
        if(user):
            return(user)
        else:
            raise KeyError("UserList::findByNick(): Couldn't find a user who has authed as '%s'." % (name))
    
    # String or None:
    def findByNameDefault(self, name, default = None):
        for (nick, user) in self.data.items():
            authedAs = user.dataStore.getAttributeDefault("authedAs")
            if(authedAs and authedAs == name):
                return(user)
        return(default)



    # ==========================================================================
    # for the plugins:
    #def getFlags(self, user):
    #    return(self.data[user].mode)
    
    
    
    
#    def getAuthData(self, nick):
#        if(nick in self.data):
#            return(self.data[nick].username, self.data[nick].host, self.data[nick].userinfo)
#        else:
#            return(None, None, None)
            
            
    
#    def getUser(self, nick):
#        if(self.data.has_key(nick)):
#            return(self.data[nick])
#        else:
#            return(None)



#    def areAllFlagsSet(self, user, flags):
#        if(user in self.data):
#            for flag in flags:
#                if(not (flag in self.data[user].mode)):
#                    return(False)
#            return(True)
#        else:        # WARNING: areAllFlagsSet also returns False if the person is not known
#            return(False)



#    def getDictionaryWithFlags(self):        # returns {"abc" ==> 'o', "def" ==> 'v', "ghi" ==> ''}
#        result = {}
#        for (name, user) in self.data.items():
#            result[name] = user.mode
#        return(result)
    
    
    
#    def getPureList(self):           # returns ["abc", "def", "ghi"]
#        return(self.data.keys())


    
#    def getIdByNick(self, nick):
#        if(self.data.has_key(nick)):
#            return(self.data[nick].id)
#        else:
#            return(0)




