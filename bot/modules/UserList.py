import string
#from modules import LogLib



class UserList:
    def __init__(self):
        self.shouldBeUpToDate = False
        self.userList = {}



    # ==========================================================================
    # for the IRCLib:
    def onLeave(self, source, channel, reason):
        del self.userList[source]

    def onQuit(self, source, reason):
        del self.userList[source]

    def onKick(self, source, target, reason, channel):
        del self.userList[target]

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
                #LogLib.log.add(LogLib.LOGLVL_DEBUG, str(self.userList[targets[currentTargetIndex]]))
                if(currentTargetIndex < len(targets)):
                    if currentMode == '+':
                        if(not char in self.userList[targets[currentTargetIndex]][0]):
                            self.userList[targets[currentTargetIndex]][0] += char
                            currentTargetIndex += 1
                    else:
                        if(char in self.userList[targets[currentTargetIndex]][0]):
                            self.userList[targets[currentTargetIndex]][0] = string.join([x for x in self.userList[targets[currentTargetIndex]][0] if x!=char], "")
                            currentTargetIndex += 1

    def onJoin(self, source, channel):
        self.userList[source] = ["", None, None, None]

    def onChangeNick(self, source, target):
        self.userList[target] = self.userList[source]
        del self.userList[source]
        
    def rebuildUserList(self, namesBuffer):
        self.userList = {}
        for list in namesBuffer:
            for user in list.split(" "):
                if(user[0] == "@"):
                    self.userList[user[1:]] = ["o", None, None, None]
                elif(user[0] == "+"):
                    self.userList[user[1:]] = ["v", None, None, None]
                else:
                    self.userList[user] = ["", None, None, None]

    def reportWhois(self, nick, username, host, userinfo):
        if(nick in self.userList):
            self.userList[nick][1] = username
            self.userList[nick][2] = host
            self.userList[nick][3] = userinfo





    # ==========================================================================
    # for the plugins:
    def getFlags(self, user):
        return(self.userList[user][0])
    
    
    
    def getAuthData(self, nick):
        if(nick in self.userList):
            (flags, username, host, userinfo) = self.userList[nick]
            return(username, host, userinfo)
        else:
            return(None, None, None)

    
    
    def areAllFlagsSet(self, user, flags):
        if(user in self.userList):
            for flag in flags:
                if(not (flag in self.userList[user][0])):
                    return(False)
            return(True)
        else:        # WARNING: areAllFlagsSet also returns False if the person is not known
            return(False)



    def getDictionaryWithFlags(self):        # returns {"abc" ==> 'o', "def" ==> 'v', "ghi" ==> ''}
        result = {}
        for (user, (flags, username, host, userinfo)) in self.userList.items():
            result[user] = flags
        return(result)
    
    
    
    def getPureList(self):           # returns ["abc", "def", "ghi"]
        result = []
        for (user, (flags, username, host, userinfo)) in self.userList.items():
            result.append(user)
        return(result)

        
        
    def getRawDictionary(self):
        return(self.userList)
    