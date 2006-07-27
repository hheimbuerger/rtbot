import re, time, datetime, string, pickle, logging
from modules import PluginInterface

class AuthenticationPlugin:

    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
    	self.dontThankLNextTime = False
        self.listOfKnownPersons = {}
        self.listOfPunishedPersons = []
    	self.loadList()

    def getVersionInformation( self ):
        return( "$Id$" )
    
    def sendMessage(self, sender, receiver, message, needDeliveryNotification, isDeliveryNotification, instantDelivery = False):
        mailboxPlugin = self.pluginInterfaceReference.getPlugin("MailboxPlugin")
        if(mailboxPlugin == None):
            logging.info("ERROR: AuthenticationPlugin didn't succeed at lookup of MailboxPlugin during execution of sendMessage()")
            return(False)
        else:
            mailboxPlugin.sendMessage(sender, receiver, message, needDeliveryNotification, isDeliveryNotification, instantDelivery)
            return(True)

    def getListOfMutees(self):
        mutingPlugin = self.pluginInterfaceReference.getPlugin("MutingPlugin")
        if(mutingPlugin == None):
            logging.info("ERROR: AuthenticationPlugin didn't succeed at lookup of MutingPlugin during execution of getListOfMutees()")
            return([])
        else:
            return(mutingPlugin.getList())

    def loadList( self ):
        self.listOfKnownPersons = {}
#        file = open("resources/friends.lst", "r")
#        lines = file.readlines()
#        file.close()
#        for line in lines:
#          line_contents = string.split(line, "|")
#          if((len(lineSplitted) > 0) and (len(lineSplitted[0]) > 0)):
#              name = lineSplitted[0]
#              self.listOfKnownPersons[name] = []
#              auths = lineSplitted[1:]
#              for auth in auths:
#                  (usernameRE, hostRE, userinfoRE) = string.split(auth, ",")
#                  self.listOfKnownPersons[name].append((usernameRE, hostRE, userinfoRE))
        try:
            file = open("resources/friends.lst", "rb")
            self.listOfKnownPersons = pickle.load(file)
            file.close()
        except EOFError:
            self.listOfKnownPersons = {}

    def saveList( self ):
        file = open( "resources/friends.lst", "wb" )
#        for (name, auths) in self.listOfKnownPersons:
#            
#            line = string.join([name] + hosts, "|")
#            file.write(line + "\n")
        pickle.dump(self.listOfKnownPersons, file)
        file.close()

    def makeMeOp( self, irclib ):
        self.dontThankLNextTime = True
        irclib.sendPrivateMessage( "L", "OP " + irclib.channel )

    def determineNecessaryUpdate(self, targetFlag, currentFlags):
        if(targetFlag == 'o'):
            if(not ('o' in currentFlags)):
                return("+o")
                #irclib.sendChannelMessage("You're my friend, " + self.getCanonicalName(user) + "! I gave you op status.")
        elif(targetFlag == 'v'):
            if('o' in currentFlags):
                return("-o")
            if(not 'v' in currentFlags):
                return("+v")
        else:
            if('o' in currentFlags):
                return("-o")
            if('v' in currentFlags):
                return("-v")
        return(None)

#    def updateUserModeIfNecessary(self, irclib, user, targetFlag, currentFlags):
#        if(irclib.isOp()):
#            flagModifier = self.determineNecessaryUpdate(targetFlag, currentFlags)
#            irclib.setChannelMode(flagModifier, user)

    def updateChannelModeIfNecessary(self, irclib, flagModifier):
        if((flagModifier == "+m") and (not 'm' in irclib.channelModes)):
            irclib.setChannelMode("+m")
        elif((flagModifier == "-m") and ('m' in irclib.channelModes)):
            irclib.setChannelMode("-m")

    def updateModes(self, irclib):
        # create a list of canonical mutee names
        rawMutees = self.getListOfMutees()
        mutees = []
        for rawMutee in rawMutees:
            mutees.append(self.getCanonicalName(rawMutee))

        # iterate over the user list and change to the appropriate mode if necessary
        userList = irclib.getUserList().getRawDictionary()
        flagsToSet = ""
        usersToSet = []
        for (nick, (flags, usernameRE, hostRE, userinfoRE)) in userList.items():
            if(nick != irclib.nickname and nick != "L"):
                canonicalName = self.getCanonicalName(nick)
                isFriend = self.isFriend(irclib, nick)
                isMuted = (canonicalName in mutees)
                isPunished = (canonicalName in self.listOfPunishedPersons)
                if(isMuted):
                    targetFlag = ''
                elif(isFriend and not isPunished):
                    targetFlag = 'o'
                else:
                    targetFlag = 'v'
                #self.updateUserModeIfNecessary(irclib, nick, targetFlag, flags)
                deltaFlag = self.determineNecessaryUpdate(targetFlag, flags)
                if(deltaFlag):
                    flagsToSet += deltaFlag
                    usersToSet.append(nick)
        
        # apply the changes en bloc
        irclib.setModes(flagsToSet, usersToSet)

        # set the appropriate channel mode
        if(len(mutees) > 0):
            self.updateChannelModeIfNecessary(irclib, "+m")
        else:
            self.updateChannelModeIfNecessary(irclib, "-m")

    def getCanonicalName(self, name):
        # (\S+?)(?:\[.*?\]|\|.*?|_{1,2})
        pattern =( r"^"          # nothing in front of this
                  r"(\S+?)"     # username, followed by
                  r"(?:\[.*?\]" # [....] or
                  r"|\|.*?"     # |..... or
                  r"|_{1,2})"   # _ or __
                  r"$" )         # nothing after this
        result = re.match( pattern, name )
        if( result ):
          name = result.group( 1 )

        #LogLib.log.add(False, "canonName = " + name)
        return name
    
    def reMatches(self, irclib, RE, input):
        try:
            return(re.compile("^" + RE + "$").match(input))
        except re.error:
            message = "ERROR: RegEx error in auth info ('%s'|'%s')!" % (RE, input)
            logging.debug(message)
            #self.sendMessage(irclib.nickname, "@Cort", message, False, False, True)
            return(False)

    def isFriend(self, irclib, nick):
        # retrieve the additional auth information of the user
        (username, host, userinfo) = irclib.getUserList().getAuthData(nick)
        
        # if the host is still set to None, this user either does not exist or has not been WHOISed yet.
        # Either way, it's not a friend.
        if(not username or not host or not userinfo):
            return(None)
        
        # now we've got a host, let's see if it is in our list
        for (user, auths) in self.listOfKnownPersons.items():
            for auth in auths:
                (usernameRE, hostRE, userinfoRE) = auth
                if(     self.reMatches(irclib, usernameRE, username)
                    and self.reMatches(irclib, hostRE, host)
                    and self.reMatches(irclib, userinfoRE, userinfo)):
                    return(user)

        # if we couldn't find this host somewhere in our list, it's not a friend
        return(None)
    
    def isKnown(self, username):
        return(username in self.listOfKnownPersons)
  
    def punish(self, irclib, name):
        canonicalName = self.getCanonicalName(name)
        if(not canonicalName in self.listOfPunishedPersons):
            self.listOfPunishedPersons.append(name)
        self.updateModes(irclib)

    def onTimer(self, irclib):
        self.updateModes(irclib)
        
    def onChangeNick( self, irclib, source, target ):
      #self.makeOpIfKnown( irclib, source, target )
        self.updateModes(irclib)

    def getAuthInformationList(self, user):
        result = []
        listOfAuths = self.listOfKnownPersons[user]
        i = 0
        if(len(listOfAuths) == 0):
            result.append("[none]")
        else:
            for auth in listOfAuths:
                (username, host, userinfo) = auth
                result.append("%i. Username='%s', Host='%s', Userinfo='%s'" % (i, username, host,userinfo))
                i += 1
        return(result)

    def pmAuthInformationList(self, irclib, target, user):
        for line in self.getAuthInformationList(user):
            irclib.sendPrivateMessage(target, line)
            
    def informTargetOfAuthChanges(self, irclib, sourceAccount, targetAccount):
        # ignoring the result of sendMessage() here -- if it fails, no big thing...
        message = '%s changed your authentication information. Type "list %s" to see the new list.' % (sourceAccount, targetAccount)
        self.sendMessage(irclib.nickname, "@"+targetAccount, message, False, False, True)
        
        # DEBUG: Send a copy to @Cort
        self.sendMessage(irclib.nickname, "@Cort", message, False, False, True)

    @PluginInterface.Priorities.prioritized( PluginInterface.Priorities.PRIORITY_LOW )
    def onPrivateMessage(self, irclib, source, msg):
        # parse the command
        if(len(msg.split()) > 0):
            command = msg.split()[0]
        arguments = msg.split()[1:]
        
        # abort if we're not talking to a friend
        if(not self.isFriend(irclib, source) and not self.getCanonicalName(source) == "Cort"):
            irclib.sendPrivateMessage(source, "I don't know you, please leave me alone!")
            return
        
        # COMMAND: list
        if(command == "list" and len(arguments) == 0):
            list = self.listOfKnownPersons.keys()
            list.sort()
            irclib.sendPrivateMessage(source, "The following persons are my friends: " + string.join(list, ", "))
            irclib.sendPrivateMessage(source, 'Say "list <name>" to display the known authentication information.')

        elif(command == "list" and len(arguments) == 1):
            name = arguments[0]
            if(name in self.listOfKnownPersons):
                irclib.sendPrivateMessage(source, "Of %s, I have the following authentication expressions:" % (name))
                self.pmAuthInformationList(irclib, source, name)
                irclib.sendPrivateMessage(source, 'Say "add <name> <username-RE> <host-RE> <userinfo-RE>" to add authentication information to that user. The RE-syntax can be looked up on http://docs.python.org/lib/re-syntax.html')
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")

        # COMMAND: add
        if(command == "add" and len(arguments) == 0):
            irclib.sendPrivateMessage(source, 'To add a person to my list, say "add <name>". The name is just internally used and has nothing to do with the nick the user is currently using.')
            irclib.sendPrivateMessage(source, 'To add authentication information to my list, say "add <name> <username-RE> <host-RE> <userinfo-RE>". The RE-syntax can be looked up on http://docs.python.org/lib/re-syntax.html')
        elif(command == "add" and len(arguments) == 1):
            name = arguments[0]
            if(name in self.listOfKnownPersons):
                irclib.sendPrivateMessage(source, "That person is on my list already!")
            else:
                self.listOfKnownPersons[name] = []
                self.saveList()
                irclib.sendPrivateMessage(source, "Ok, I added %s. Please tell me about his authentication!" % (name))
                irclib.sendPrivateMessage(source, 'Say "add <name> <username-RE> <host-RE> <userinfo-RE>" to add authentication information to that user. The RE-syntax can be looked up on http://docs.python.org/lib/re-syntax.html')
                irclib.sendChannelEmote("adds " + name + " to his buddy-list.")
        elif(command == "add" and len(arguments) == 4):
            name = arguments[0]
            if(name in self.listOfKnownPersons):
                try:
                    re.compile(arguments[1])
                except re.error:
                    irclib.sendPrivateMessage(source, "That username-mask is not a valid RE!")
                    return
                try:
                    re.compile(arguments[2])
                except re.error:
                    irclib.sendPrivateMessage(source, "That host-mask is not a valid RE!")
                    return
                try:
                    re.compile(arguments[3])
                except re.error:
                    irclib.sendPrivateMessage(source, "That userinfo-mask is not a valid RE!")
                    return
                self.listOfKnownPersons[name].append((arguments[1], arguments[2], arguments[3]))
                self.saveList()
                irclib.sendPrivateMessage(source, "Ok, I added that authentication information. Here is the new list:")
                self.pmAuthInformationList(irclib, source, name)
                self.informTargetOfAuthChanges(irclib, self.isFriend(irclib, source), name)
                self.updateModes(irclib)
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")
    
        # COMMAND: remove
        if(command == "remove" and len(arguments) == 0):
            irclib.sendPrivateMessage(source, 'To completely remove a person from my list, say "remove <name>".')
            irclib.sendPrivateMessage(source, 'To remove only authentication information from my list, say "remove <name> <auth-id>". Say "list <name>" to see the available authentication information for a person.')
        elif(command == "remove" and len(arguments) == 1):
            name = arguments[0]
            if(name in self.listOfKnownPersons):
                irclib.sendPrivateMessage(source, "Ok, I removed %s!" % (name))
                irclib.sendPrivateMessage(source, "Here is the old authentication list for your protocol:")
                self.pmAuthInformationList(irclib, source, name)
                irclib.sendChannelEmote("removes %s from his buddy-list." % (name))
                del(self.listOfKnownPersons[name])
                self.saveList()
                self.updateModes(irclib)
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")
        elif(command == "remove" and len(arguments) == 2):
            name = arguments[0]
            try:
                authId = int(arguments[1])
            except ValueError:
                irclib.sendPrivateMessage(source, 'The correct syntax to remove authentication information from a user is "remove <name> <auth-id>"')
                return
            if(name in self.listOfKnownPersons):
                if(authId < len(self.listOfKnownPersons[name])):
                    del(self.listOfKnownPersons[name][authId])
                    self.saveList()
                    irclib.sendPrivateMessage(source, "Ok, I removed that authentication information from my list. Here is the new one:")
                    self.pmAuthInformationList(irclib, source, name)
                    self.informTargetOfAuthChanges(irclib, self.isFriend(irclib, source), name)
                    self.updateModes(irclib)
                else:
                    irclib.sendPrivateMessage(source, 'That auth-id is not on my list! Say "list <name>" to view the list.')
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")

    def onJoin( self, irclib, source ):
        if( source != irclib.nickname ):
            irclib.sendChannelMessage( self.getCanonicalName( source ) + "! 'yh" )
            self.updateModes(irclib)
            #self.makeOpIfKnown( irclib, source, source )

    def onUserMode( self, irclib, source, targets, flags ):
      if( ( flags == "+o" ) and ( targets[0] == irclib.nickname ) ):
          if( source == "L" ):
              if( not self.dontThankLNextTime ):
                  irclib.sendChannelMessage( "You op'ed me, L. But you're just a stupid bot, so I won't thank you. ;)" )
              self.dontThankLNextTime = False
          else:
              irclib.sendChannelMessage( "Hey, thank you, " + source + "! I like you..." )
          self.updateModes(irclib)
          #self.makeAllKnownPersonsOp( irclib )
      if( ( flags == "-o" ) and ( targets[0] == irclib.nickname ) ):
          if( source.lower().find( "gandalf" ) != -1 ):
              irclib.sendChannelMessage( "Ass." )
              irclib.sendChannelMessage( ";)" )
              self.makeMeOp( irclib )
              time.sleep( 1 )
              self.punish(irclib, source)
              irclib.sendChannelMessage( ":p" )
              self.updateModes(irclib)
          elif( self.getCanonicalName( source ).lower() == "cort" ):
              irclib.sendChannelMessage( "I guess you have your reasons... ;(" )
          else:
              irclib.sendChannelMessage( "Hey " + source + ", that's not nice... :(" )
              self.makeMeOp( irclib )
              time.sleep( 1 )
              self.punish(irclib, source)
              irclib.sendChannelMessage( ":p" )
              self.updateModes(irclib)

    def onChannelMessage(self, irclib, source, message):
        if(message == "punishlist"):
            irclib.sendChannelMessage("Currently in punish-mode: %s" % (string.join(self.listOfPunishedPersons, ", ")))
        elif((len(message.split()) >= 2) and (message.split()[0] == "!pardon")):
            name = message.split()[1]
            if(name in self.listOfPunishedPersons):
                if(self.isFriend(irclib, source)):
                    self.listOfPunishedPersons.remove(name)
                    irclib.sendChannelMessage("Yo.")
                else:
                    irclib.sendChannelMessage("What makes you think that I would accept a command from you? :P")



if __name__ == "__main__":
  pass
