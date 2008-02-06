import re, time, datetime, pickle, logging, md5
import UserDict
from modules import PluginInterface





class UserAccount:
    GROUP_NONE = None
    GROUP_RETURNINGVISITOR = "returningVisitor"
    GROUP_ADMIN = "admin"
    
    def __init__(self):
        self.encryptedPassword = None
        self.authInfoList = []
        self.group = UserAccount.GROUP_NONE

    def setPassword(self, password):
        self.encryptedPassword = md5.new(password).digest()
        
    def verifyPassword(self, password):
        return(self.encryptedPassword and self.encryptedPassword == md5.new(password).digest())
        
    def setGroup(self, group):
        self.group = group

    def addAuthInfo(self, usernameRE, hostRE, userinfoRE):
        self.authInfoList.append((usernameRE, hostRE, userinfoRE))

    def removeAuthInfo(self, username, authId):
        if(authId < self.getAuthInfoLength()):
            del(self.authInfoList[authId])

    def changeAuthInfo(self, authId, usernameRE, hostRE, userinfoRE):
        self.authInfoList[authId] = (usernameRE, hostRE, userinfoRE)

    def getAuthInfoLength(self):
        return(len(self.authInfoList))





class AccountList(UserDict.IterableUserDict):
    
    def __init__(self):
#===============================================================================
#        # ===== converting account database =====
#        file = open("resources/friends.lst", "rb")
#        users = pickle.load(file)
#        file.close()
#
#        self.data = {}
#        for (name, authList) in users.items():
#            self.addAccount(name)
#            account = self.data[name]
#            for auth in authList:
#                account.addAuthInfo(auth[0], auth[1], auth[2])
#            account.setGroup(UserAccount.GROUP_ADMIN)
#
#        self.save()
#        # ===== end of conversion =====
#===============================================================================

        try:
            file = open("resources/accounts.lst", "rb")
            self.data = pickle.load(file)
            file.close()
        except (EOFError, IOError):
            self.data = {}

    def save(self):
        file = open( "resources/accounts.lst", "wb" )
        pickle.dump(self.data, file)
        file.close()

    def isKnown(self, username):
        return(username in self.data)
        
    def getListOfNames(self):
        list = self.data.keys()
        list.sort()
        return(list)

    def addAccount(self, username):
        self.data[username] = UserAccount()

    def removeAccount(self, username):
        del(self.data[username])

    def reMatches(self, RE, input):
        try:
            return(re.compile("^" + RE + "$").match(input))
        except re.error:
            message = "ERROR: RegEx error in auth info ('%s'|'%s')!" % (RE, input)
            logging.debug(message)
            #self.sendMessage(irclib.nickname, "@Cort", message, False, False, True)
            return(False)

    def findAccountnameThatMatchesUser(self, user):
        for (name, account) in self.data.items():
            for auth in account.authInfoList:
                (usernameRE, hostRE, userinfoRE) = auth
                if(user.username and user.host and user.userinfo):
                    if(     self.reMatches(usernameRE, user.username)
                        and self.reMatches(hostRE, user.host)
                        and self.reMatches(userinfoRE, user.userinfo)):
                        return(name)
        return(None)

    def findUsersThatMatchAccount(self, account, userList):
        result = []
        for user in userList:
            name = self.findAccountnameThatMatchesUser(user)
            if(name):
                if(account == self.data[name]):
                    result.append(user)
        return(result)





class AuthenticationPlugin:
    ignoredNicks = ["L"]
    whoResultGracePeriod = 30            # in seconds
    whoRetryAttemptsThreshold = 3        # in attempts
    externalAuthenticationTimeout = 15   # in seconds

    # ==================================================
    # META-METHODS
    # ==================================================
    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface
        self.dontThankLNextTime = False
        self.accountList = AccountList()
        self.scheduledModeUpdates = []
        self.pendingAuthentications = {}

    def getVersionInformation( self ):
        return("$Id$")
    
    def sendMessage(self, sender, receiver, message, needDeliveryNotification, isDeliveryNotification, instantDelivery = False):
        mailboxPlugin = self.pluginInterfaceReference.getPlugin("MailboxPlugin")
        if(mailboxPlugin == None):
            logging.info("ERROR: AuthenticationPlugin didn't succeed at lookup of MailboxPlugin during execution of sendMessage()")
            return(False)
        else:
            mailboxPlugin.sendMessage(sender, receiver, message, needDeliveryNotification, isDeliveryNotification, instantDelivery)
            return(True)



    # ==================================================
    # VARIOUS METHODS
    # ==================================================
    def makeMeOp( self, irclib ):
        self.dontThankLNextTime = True
        irclib.sendPrivateMessage( irclib.getUserList()["L"], "OP " + irclib.channel )

    def determineNecessaryUpdate(self, targetFlags, currentFlags):
        result = ""
        # add necessary flags
        for flag in targetFlags:
            if((flag == 'o') and ('o' not in currentFlags)):
                result += "+o"
            elif((flag == 'v') and ('v' not in currentFlags)):
                result += "+v"
        # remove unnecessary flags
        for flag in currentFlags:
            if((flag == 'o') and ('o' not in targetFlags)):
                result += "-o"
            elif((flag == 'v') and ('v' not in targetFlags)):
                result += "-v"
        return(result)
 
    def getFormattedAuthInformationList(self, account):
        result = []
        i = 0
        if(len(account.authInfoList) == 0):
            result = ["[none]"]
        else:
            for auth in account.authInfoList:
                (username, host, userinfo) = auth
                result.append("%i. Username='%s', Host='%s', Userinfo='%s'" % (i, username, host, userinfo))
                i += 1
        return(result)
 
    def pmAuthInformationList(self, irclib, target, account):
        for line in self.getFormattedAuthInformationList(account):
            irclib.sendPrivateMessage(target, line)

    def informTargetOfAuthChanges(self, irclib, source, target):
        # ignoring the result of sendMessage() here -- if it fails, no big thing...
#        message = '%s changed your authentication information. Type "list %s" to see the new list.' % (sourceAccount, targetAccount)
#        self.sendMessage(irclib.nickname, "@"+targetAccount, message, False, False, True)

        # DEBUG: Send a copy to @Cort
#        self.sendMessage(irclib.nickname, "@Cort", message, False, False, True)
        pass

    def scheduleModeUpdate(self, nick, deltaFlags):
        for i in range(0, len(deltaFlags)/2):
            self.scheduledModeUpdates.append((nick, deltaFlags[i*2:i*2+2]))

    def issueScheduledModeUpdates(self, irclib):
        # create the lists of flags and users to set
        flagsToSet = ""
        usersToSet = []

        for (nick, modifier) in self.scheduledModeUpdates:
            flagsToSet += modifier
            usersToSet.append(nick)
        
        # apply the changes en bloc
        irclib.setModes(flagsToSet, usersToSet)
        
        # reset the list
        self.scheduledModeUpdates = []

#    def updateAuthStateAll(self, irclib):
#        for user in irclib.getUserList().values():
#            self.updateAuthState(irclib, user)

    def triggerAuthUpdate(self, irclib, usersOrAccount, updateModes = False):
        # get the user if necessary
        if(usersOrAccount.__class__ == UserAccount):
            users = self.accountList.findUsersThatMatchAccount(usersOrAccount, irclib.getUserList().values())
        elif(usersOrAccount.__class__ == list):
            users = usersOrAccount
        else:        # usersOrAccount is hopefully an instance of UserList.User
            users = [usersOrAccount]

        for user in users:
            # make sure this isn't the bot himself
            if((user.nick == irclib.nickname) or (user.nick in AuthenticationPlugin.ignoredNicks)):
                continue
            
            # try to auth via password
            username = user.dataStore.getAttributeDefault("authedAs", "")
            password = user.dataStore.getAttributeDefault("authedByPassword", "")
            if(username != "" and password != ""                # if the user has previously tried to auth by password
               and self.accountList.isKnown(username)              # ... and the given username exists in our account database
               and self.accountList[username].verifyPassword(password)):     # ... and the given password matches the one in our account database
                
                user.dataStore.setAttribute("timeOfLastAuth", datetime.datetime.utcnow())
                user.dataStore.setAttribute("group", self.accountList[username].group)
            else:
                # didn't work -- let's try to auth via hostmask
                name = self.accountList.findAccountnameThatMatchesUser(user)
                if(name):
                    user.dataStore.setAttribute("authedAs", name)
                    user.dataStore.setAttribute("timeOfLastAuth", datetime.datetime.utcnow())
                    user.dataStore.setAttribute("group", self.accountList[name].group)
                    user.dataStore.removeAttribute("authedByPassword")
                else:
                    user.dataStore.removeAttribute("authedAs")
                    user.dataStore.removeAttribute("authedByPassword")
                    user.dataStore.removeAttribute("group")
                    user.dataStore.removeAttribute("timeOfLastAuth")
            
            if(updateModes):
                self.triggerModeUpdate(irclib, user)
        
        if(updateModes):
            self.issueScheduledModeUpdates(irclib)

    # Verify that all nicks in the channel have their appropriate modes by calling updateNickMode()
    # on all of them.
    def triggerModeUpdatesAll(self, irclib):
        # iterate over all active nicks
        userList = irclib.getUserList()
        for (nick, user) in userList.items():
            # update this nick
            self.triggerModeUpdate(irclib, user)
            
        # issue the changes
        self.issueScheduledModeUpdates(irclib)

    # Update the modes of a given nick based on authentication information previously set. This method
    # is *not* doing any authentication checks!
    def triggerModeUpdate(self, irclib, user):
        # This method is relying on other parts of the AuthPlugin having already added the necessary
        # auth info to the user object of the nick. We're just generating the right mode from the
        # existing information. We're *not* doing any authentication checks here!

        # make sure we're neither talking about the bot himself nor about some nick that is taboo (e.g. L)
        if((user.nick != irclib.nickname) and (user.nick not in AuthenticationPlugin.ignoredNicks)):
            # make sure this user isn't in the grace period before put under MODE control -- if she/he is,
            # issue a new WHO if necessary or give up if necessary
            timeOfLastWhoAttempt = user.dataStore.getAttributeDefault("timeOfLastWhoAttempt", None)
            numberOfWhoAttempts = user.dataStore.getAttributeDefault("numberOfWhoAttempts", None)
            if(timeOfLastWhoAttempt != None and numberOfWhoAttempts != None):
                currentTime = datetime.datetime.utcnow()
                deltaTime = currentTime - timeOfLastWhoAttempt
                if(deltaTime.days == 0 and deltaTime.seconds < AuthenticationPlugin.whoResultGracePeriod):
                    return
                elif(numberOfWhoAttempts < AuthenticationPlugin.whoRetryAttemptsThreshold):
                    irclib.doWho(user)
                    user.dataStore.setAttribute("timeOfLastWhoAttempt", currentTime)
                    user.dataStore.setAttribute("numberOfWhoAttempts", numberOfWhoAttempts+1)
                    return

            # retrieve the data we need
            targetFlags = ""
            isMuted = user.dataStore.getAttributeDefault("isMuted", False)
            isPunished = user.dataStore.getAttributeDefault("isPunished", False)
            isAuthed = user.isAuthed()
            if(isAuthed):
                isAdmin = user.isAdmin()
                isReturningVisitor = user.isAuthed and not user.isAdmin()
            else:
                isAdmin = False
                isReturningVisitor = False

            # determine the target flags for this nick
            if(isMuted):
                targetFlag = ''
            elif(not isPunished and isAdmin):
                targetFlag = 'o'
            elif(isAuthed):
                targetFlag = 'v'
            else:
                targetFlag = ''

            # determine what needs to be changed to get to the target flags and schedule it
            deltaFlags = self.determineNecessaryUpdate(targetFlag, user.mode)
            if(deltaFlags):
                self.scheduleModeUpdate(user.nick, deltaFlags)

#    def updateAccount(self, irclib, account):
#        for user in irclib.getUserList().values():
#            if(self.accountList.findAccountThatMatchesAuthInfo(user) == account):
#                self.updateAuthState(irclib, user)
#                self.updateNickModes(irclib, user)

    def triggerChannelModeUpdate(self, irclib):
        # set the appropriate channel mode
        if(self.hasAnyMutees(irclib.getUserList().values())):
            if('m' not in irclib.channelModes):
                irclib.setChannelMode("+m")
        else:
            if('m' in irclib.channelModes):
                irclib.setChannelMode("-m")

    def verifyValidREs(self, irclib, source, usermaskRE, hostmaskRE, userinfoRE):
        try:
            re.compile(usermaskRE)
        except re.error:
            irclib.sendPrivateMessage(source, "That username-mask is not a valid RE!")
            return(False)
        try:
            re.compile(hostmaskRE)
        except re.error:
            irclib.sendPrivateMessage(source, "That host-mask is not a valid RE!")
            return(False)
        try:
            re.compile(userinfoRE)
        except re.error:
            irclib.sendPrivateMessage(source, "That userinfo-mask is not a valid RE!")
            return(False)
        return(True)

    def hasAnyMutees(self, userList):
        for user in userList:
            if(user.dataStore.getAttributeDefault("isMuted", False)):
                return(True)
        return(False)

    def parseAuthentication(self, message):
        message_words = message.split()
        if(len(message_words) == 3):
            if(message_words[0] == "authenticate"):
                name = message_words[1]
                password = message_words[2]
                
                if(self.accountList.has_key(name) and self.accountList[name].verifyPassword(password)):
                    return((name, password))
                else:
                    return(None)

    def punish(self, irclib, nick):
        if(nick in irclib.getUserList().keys()):
            irclib.getUserList()[nick].dataStore.setAttribute("isPunished", True)

    # ==================================================
    # EVENT HANDLERS
    # ==================================================
    def onTimer(self, irclib):
        if(irclib.getUserList()[irclib.nickname].hasOp()):
            self.triggerModeUpdatesAll(irclib)
            self.issueScheduledModeUpdates(irclib)
            self.triggerChannelModeUpdate(irclib)
            
        # clear pending authentications
        for (nick, data) in self.pendingAuthentications.items():
            issuedAt = data[2]
            deltatime = datetime.datetime.utcnow() - issuedAt
            if((deltatime.days != 0) or (deltatime.seconds > AuthenticationPlugin.externalAuthenticationTimeout)):
                del self.pendingAuthentications[nick]

    def onChangeNick(self, irclib, source, target):
        pass

    def onJoin(self, irclib, source):
        # we're not doing any authing here, we're waiting for the user to send a password
        # or for the WHO to return so we can auth by hostmask
        
        # source should never be the bot itself, but can't hurt to check
        if(source.nick != irclib.nickname):
            # welcome the joiner
            irclib.sendChannelMessage( source.getCanonicalNick() + "! 'yh" )
            
            # take a note that we're waiting for the 
            source.dataStore.setAttribute("timeOfLastWhoAttempt", datetime.datetime.utcnow())
            source.dataStore.setAttribute("numberOfWhoAttempts", 1)
            
            # check if the user has already been authed by external notice
            if(source.nick in self.pendingAuthentications):
                name = self.pendingAuthentications[source.nick][0]
                password = self.pendingAuthentications[source.nick][1]
                authedAt = self.pendingAuthentications[source.nick][2]
                source.dataStore.setAttribute("authedAs", name)
                source.dataStore.setAttribute("authedByPassword", password)
                source.dataStore.setAttribute("timeOfLastAuth", authedAt)
                del self.pendingAuthentications[source.nick]
                self.triggerAuthUpdate(irclib, source, True)

    def onUserMode( self, irclib, source, targets, flags ):
      if( ( flags == "+o" ) and ( targets[0] == irclib.nickname ) ):
          if( source == "L" ):
              if( not self.dontThankLNextTime ):
                  irclib.sendChannelMessage( "You op'ed me, L. But you're just a stupid bot, so I won't thank you. ;)" )
              self.dontThankLNextTime = False
          else:
              irclib.sendChannelMessage( "Hey, thank you, " + source.getCanonicalNick() + "! I like you..." )
          self.triggerModeUpdatesAll(irclib)
          self.issueScheduledModeUpdates(irclib)
      if( ( flags == "-o" ) and ( targets[0] == irclib.nickname ) ):
          if( source.getCanonicalNick().lower() == "cort" ):
              irclib.sendChannelMessage("I guess you have your reasons... ;(")
          else:
              irclib.sendChannelMessage("Hey " + source.getCanonicalNick() + ", that's not nice... :(")
              self.makeMeOp( irclib )
              time.sleep(1)
              self.punish(irclib, source.nick)
              irclib.sendChannelMessage(":p")

    def onWhoResult(self, irclib, user):
        # remove her/his who attempt tracking attributes
        user.dataStore.removeAttribute("timeOfLastWhoAttempt")
        user.dataStore.removeAttribute("numberOfWhoAttempts")
        
        # let's try to auth him
        self.triggerAuthUpdate(irclib, user, False)

    @PluginInterface.Priorities.prioritized( PluginInterface.Priorities.PRIORITY_LOW )
    def onPrivateMessage(self, irclib, source, message):
        # parse the command
        if(len(message.split()) > 0):
            command = message.split()[0]
        arguments = message.split()[1:]
        
        # COMMAND: set password (this command can be performed without being authed!)
        if(command == "set" and len(arguments) == 2):
            if(arguments[0] == "password"):
                passwordSetAuthorization = source.dataStore.getAttributeDefault("passwordSetAuthorization")
                if(passwordSetAuthorization):
                    timestamp = passwordSetAuthorization["timestamp"]
                    name = passwordSetAuthorization["account"]
                    sender = passwordSetAuthorization["sender"]
                    if(not self.accountList.isKnown(name)):
                        irclib.sendPrivateMessage(source, "The account you're trying to set a password for no longer exists!")
                        return
                    account = self.accountList[name]
                    source.dataStore.removeAttribute("passwordSetAuthorization")
                    account.setPassword(arguments[1])
                    self.accountList.save()
                    irclib.sendPrivateMessage(source, "The password has been set on the account '%s'." % (name))
                    irclib.sendPrivateMessage(source, "You can now authenticate anytime by sending me a notice with the content 'authenticate <name/> </password/>', e.g. by typing \"/notice RTBot authenticate %s mysecretpassword\"." % (name))
                    return    # need to return here to prevent the "don't know you" message
                else:
                    irclib.sendPrivateMessage(source, "You are not granted to set a password at this time!")
                    return

        # abort if we're not talking to a friend, set sourceUser otherwise
        if(not source.isAdmin() and source.nick != "Cort"):
            irclib.sendPrivateMessage(source, "I don't know you, please leave me alone!")
            return
        else:
            sourceName = source.getName()

        # COMMAND: list
        if(command == "list" and len(arguments) == 0):
            listAdmins = sorted([name for (name, account) in self.accountList.items() if account.group == UserAccount.GROUP_ADMIN])
            listVisitors = sorted([name for (name, account) in self.accountList.items() if account.group == UserAccount.GROUP_RETURNINGVISITOR])
            listOthers = sorted([name for (name, account) in self.accountList.items() if (account.group != UserAccount.GROUP_ADMIN and account.group != UserAccount.GROUP_RETURNINGVISITOR)])
            if(len(listAdmins) > 0):
                irclib.sendPrivateMessage(source, "The following persons are in the group 'admins': %s" % (", ".join(listAdmins)))
            if(len(listVisitors) > 0):
                irclib.sendPrivateMessage(source, "The following persons are in the group 'visitors': %s" % (", ".join(listVisitors)))
            if(len(listOthers) > 0):
                irclib.sendPrivateMessage(source, "The following persons are not in a group: %s" % (", ".join(listOthers)))
            irclib.sendPrivateMessage(source, 'Say "list <name>" to display the known authentication information.')

        elif(command == "list" and len(arguments) == 1):
            name = arguments[0]
            if(self.accountList.isKnown(name)):
                irclib.sendPrivateMessage(source, "Of %s, I have the following authentication expressions:" % (name))
                account = self.accountList[name]
                self.pmAuthInformationList(irclib, source, account)
                hasPasswortSetString = ""
                if(not account.encryptedPassword):
                    hasPasswortSetString = "not "
                if(account.group == UserAccount.GROUP_ADMIN):
                    groupString = "a member of the group 'admins'"
                elif(account.group == UserAccount.GROUP_RETURNINGVISITOR):
                    groupString = "a member of the group 'visitors'"
                else:
                    groupString = "not a member of a group"
                irclib.sendPrivateMessage(source, 'This account does %shave a password set and is %s.' % (hasPasswortSetString, groupString))
                irclib.sendPrivateMessage(source, 'Say "add <name> <username-RE> <host-RE> <userinfo-RE>" to add authentication information to that user. The RE-syntax can be looked up on http://docs.python.org/lib/re-syntax.html')
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")

        # COMMAND: debuglist
        if(command == "debuglist"):
            list = irclib.getUserList().keys()
            irclib.sendPrivateMessage(source, str([(nick, nick.authedAs, nick.authedWithPassword, group) for nick in list if nick.isAuthed()]))

        # COMMAND: set password
        if(command == "grant" and len(arguments) >= 2):
            if(arguments[0] == "password"):
                # determine the account name the password setting is granted for
                name = arguments[1]
                if(not self.accountList.isKnown(name)):
                    irclib.sendPrivateMessage(source, "I don't know the account '%s'" % (name))
                    return
                
                # determine the nick the request should be sent to
                if(len(arguments) >= 3):
                    nick = arguments[2]
                else:
                    nick = name
                    
                # check that the user isn't trying to grant a password to his own account or nick
                if(name == source.dataStore.getAttribute("authedAs") or nick == source.nick):
                    irclib.sendPrivateMessage(source, "You're not allowed to grant yourself a password. Ask another admin!")
                    return

                # make sure the target nick is aroundwant
                if(not irclib.getUserList().isOnline(nick)):
                    irclib.sendPrivateMessage(source, "%s isn't around. Say \"grant password <account> [<nick>]\" to grant somebody a password." % (nick))
                    return
                
                # save the authorization in the dataStore of the target user
                targetuser = irclib.getUserList()[nick]
                passwordSetAuthorization = {"timestamp": datetime.datetime.utcnow(), "account": name, "sender": source.nick}
                targetuser.dataStore.setAttribute("passwordSetAuthorization", passwordSetAuthorization)

                # send message to the nick
                irclib.sendPrivateMessage(targetuser, '%s has allowed you to set a password. Say "set password <password>" to set it."' % (source.nick))
                irclib.sendPrivateMessage(targetuser, 'This password can not be retrieved. If you forget it, you need to ask an admin to grant you a new one.')
                irclib.sendPrivateMessage(source, '%s has been allowed to set a password for the account %s.' % (targetuser.nick, name))

        # COMMAND: status
        if(command == "status" and len(arguments) == 1):
            nick = arguments[0]
            if(irclib.getUserList().has_key(nick)):
                user = irclib.getUserList()[nick]
                if(user.isAuthed()):
                    authedAs = user.dataStore.getAttribute("authedAs")
                    timeOfLastAuth = user.dataStore.getAttribute("timeOfLastAuth").strftime("%A, %d %b %Y %H:%M:%S")
                    group = user.dataStore.getAttribute("group")
                    if(user.dataStore.getAttributeDefault("authedByPassword")):
                        irclib.sendPrivateMessage(source, "%s has authed as %s on %s using a password and is a member of the group '%s'." % (nick, authedAs, timeOfLastAuth, group))
                    else:
                        irclib.sendPrivateMessage(source, "%s has authed as %s on %s by DNS name and is a member of the group '%s'." % (nick, authedAs, timeOfLastAuth, group))
                else:
                    irclib.sendPrivateMessage(source, "%s isn't authed." % (nick))

                # print punish and mute report
                if user.dataStore.getAttributeDefault("isPunished"): isPunishedStr = ""
                else: isPunishedStr = "not "
                if user.dataStore.getAttributeDefault("isMuted"): isMutedStr = ""
                else: isMutedStr = "not "
                irclib.sendPrivateMessage(source, "%s is %spunished and %smuted." % (nick, isPunishedStr, isMutedStr))
            else:
                irclib.sendPrivateMessage(source, "The nick you're trying to check isn't in the channel!")
        
        # COMMAND: set group
        if(command == "set" and len(arguments) == 3):
            if(arguments[0] == "group"):
                name = arguments[1]
                group = arguments[2]
                if(self.accountList.isKnown(name)):
                    account = self.accountList[name]
                    if(group == "RT"):
                        account.group = UserAccount.GROUP_ADMIN
                        self.accountList.save()
                        irclib.sendPrivateMessage(source, "The account %s has been set to group '%s'." % (name, account.group))
                        self.triggerAuthUpdate(irclib, account, False)
                    elif(group == "visitor"):
                        account.group = UserAccount.GROUP_RETURNINGVISITOR
                        self.accountList.save()
                        irclib.sendPrivateMessage(source, "The account %s has been set to group '%s'." % (name, account.group))
                        self.triggerAuthUpdate(irclib, account, False)
                    else:
                        irclib.sendPrivateMessage(source, "The group you're trying to set is unknown.")
                else:
                    irclib.sendPrivateMessage(source, "The account you're trying to set a group for no longer exists!")

        # COMMAND: add
        if(command == "add" and len(arguments) == 0):
            irclib.sendPrivateMessage(source, 'To add a person to my list, say "add <name>". The name is just internally used and has nothing to do with the nick the user is currently using.')
            irclib.sendPrivateMessage(source, 'To add authentication information to my list, say "add <name> <username-RE> <host-RE> <userinfo-RE>". The RE-syntax can be looked up on http://docs.python.org/lib/re-syntax.html')
        elif(command == "add" and len(arguments) == 1):
            name = arguments[0]
            if(self.accountList.isKnown(name)):
                irclib.sendPrivateMessage(source, "That person is on my list already!")
            else:
                self.accountList.addAccount(name)
                irclib.sendPrivateMessage(source, "Ok, I added %s. Please tell me about his authentication!" % (name))
                irclib.sendPrivateMessage(source, 'Say "add <name> <username-RE> <host-RE> <userinfo-RE>" to add authentication information to that user. The RE-syntax can be looked up on http://docs.python.org/lib/re-syntax.html')
                irclib.sendChannelEmote("adds " + name + " to his buddy-list.")
                self.accountList.save()
        elif(command == "add" and len(arguments) == 4):
            name = arguments[0]
            if(self.accountList.isKnown(name)):
                if(self.verifyValidREs(irclib, source, arguments[1], arguments[2], arguments[3])):
                    account = self.accountList[name]
                    account.addAuthInfo(arguments[1], arguments[2], arguments[3])
                    self.accountList.save()
                    irclib.sendPrivateMessage(source, "Ok, I added that authentication information. Here is the new list:")
                    self.pmAuthInformationList(irclib, source, account)
                    self.informTargetOfAuthChanges(irclib, source, account)
                    self.triggerAuthUpdate(irclib, account, True)
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")

        # COMMAND: remove
        if(command == "remove" and len(arguments) == 0):
            irclib.sendPrivateMessage(source, 'To completely remove a person from my list, say "remove <name>".')
            irclib.sendPrivateMessage(source, 'To remove only authentication information from my list, say "remove <name> <auth-id#>". Say "list <name>" to see the available authentication information for a person.')
        elif(command == "remove" and len(arguments) == 1):
            name = arguments[0]
            if(self.accountList.isKnown(name)):
                irclib.sendPrivateMessage(source, "Ok, I removed %s!" % (name))
                irclib.sendPrivateMessage(source, "Here is the old authentication list for your protocol:")
                self.pmAuthInformationList(irclib, source, self.accountList[name])
                irclib.sendChannelEmote("removes %s from his buddy-list." % (name))
                concernedUsers = self.accountList.findUsersThatMatchAccount(self.accountList[name], irclib.getUserList().values())
                self.accountList.removeAccount(name)
                self.accountList.save()
                self.triggerAuthUpdate(irclib, concernedUsers, True)
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")
        elif(command == "remove" and len(arguments) == 2):
            name = arguments[0]
            try:
                authId = int(arguments[1])
            except ValueError:
                irclib.sendPrivateMessage(source, 'The correct syntax to remove authentication information of a user is "remove <name> <auth-id#>"')
                return
            if(self.accountList.isKnown(name)):
                account = self.accountList[name]
                if(authId < account.getAuthInfoLength()):
                    concernedUsers = self.accountList.findUsersThatMatchAccount(account, irclib.getUserList().values())
                    account.removeAuthInfo(name, authId)
                    self.accountList.save()
                    irclib.sendPrivateMessage(source, "Ok, I removed that authentication information from my list. Here is the new one:")
                    self.pmAuthInformationList(irclib, source, account)
                    self.informTargetOfAuthChanges(irclib, source, name)
                    self.triggerAuthUpdate(irclib, concernedUsers, True)
                else:
                    irclib.sendPrivateMessage(source, 'That auth-id# is not on my list! Say "list <name>" to view the list.')
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")

        # COMMAND: change
        if(command == "change" and len(arguments) == 0):
            irclib.sendPrivateMessage(source, 'To change an authentication information, say "change <name> <auth-id#> <username-RE> <host-RE> <userinfo-RE>".')
            irclib.sendPrivateMessage(source, 'To retrieve a template change line, say "change <name> <auth-id#>')
        elif(command == "change" and len(arguments) == 2):
            name = arguments[0]
            try:
                authId = int(arguments[1])
            except ValueError:
                irclib.sendPrivateMessage(source, 'The correct syntax to change authentication information is "change <name> <auth-id#> <username-RE> <host-RE> <userinfo-RE>"')
                return
            if(self.accountList.isKnown(name)):
                account = self.accountList[name]
                if(authId < account.getAuthInfoLength()):
                    command = "change %s %i %s %s %s" % (name, authId, account.authInfoList[authId][0], account.authInfoList[authId][1], account.authInfoList[authId][2])
                    irclib.sendPrivateMessage(source, 'The required line to change this authentication information is:')
                    irclib.sendPrivateMessage(source, command)
                else:
                    irclib.sendPrivateMessage(source, 'That auth-id# is not on my list! Say "list <name>" to view the list.')
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")
        elif(command == "change" and len(arguments) == 5):
            name = arguments[0]
            try:
                authId = int(arguments[1])
            except ValueError:
                irclib.sendPrivateMessage(source, 'The correct syntax to change authentication information is "change <name> <auth-id#> <username-RE> <host-RE> <userinfo-RE>"')
                return
            if(self.accountList.isKnown(name)):
                account = self.accountList[name]
                if(authId < account.getAuthInfoLength()):
                    if(self.verifyValidREs(irclib, source, arguments[2], arguments[3], arguments[4])):
                        # get a list of all users that are currently authed with this account (because they might not longer be after the change)
                        concernedUsers = self.accountList.findUsersThatMatchAccount(account, irclib.getUserList().values())
                        # now apply the change
                        account.changeAuthInfo(authId, arguments[2], arguments[3], arguments[4])
                        self.accountList.save()
                        # inform the user about the new list
                        irclib.sendPrivateMessage(source, "Ok, I changed that authentication information. Here is the new list:")
                        self.pmAuthInformationList(irclib, source, account)
                        self.informTargetOfAuthChanges(irclib, source, account)
                        # now update all users that were previously authed with this account and all that are now authed with it
                        self.triggerAuthUpdate(irclib, concernedUsers, True)
                        self.triggerAuthUpdate(irclib, account, True)
                else:
                    irclib.sendPrivateMessage(source, 'That auth-id# is not on my list! Say "list <name>" to view the list.')
            else:
                irclib.sendPrivateMessage(source, "That person is not on my list!")


    @PluginInterface.Priorities.prioritized( PluginInterface.Priorities.PRIORITY_LOW )
    def onNotice(self, irclib, source, message):
        result = self.parseAuthentication(message)
        if(result):
            (name, password) = result
            source.dataStore.setAttribute("authedAs", name)            # NOTE: At this point, it temporary looks as if the user was authed even if that's not completely the case (the other attributes aren't set yet) -- this temporary situation will be resolved by updateAuthState() though
            source.dataStore.setAttribute("authedByPassword", password)
            irclib.sendPrivateNotice(source, "You have successfully authenticated as user %s!" % (name))

            # do the authing
            self.triggerAuthUpdate(irclib, source, True)
        else:
            irclib.sendPrivateNotice(source, "Authentication failed, username or password incorrect!")

    def onExternalNotice(self, irclib, sourceNick, message):
        result = self.parseAuthentication(message)
        if(result):
            (name, password) = result
            self.pendingAuthentications[sourceNick] = (name, password, datetime.datetime.utcnow())
            irclib.sendExternalNotice(sourceNick, "You have successfully authenticated as user %s!" % (name))
            irclib.sendExternalNotice(sourceNick, "This authentication will expire if you don't join the channel in the next %i seconds." % (AuthenticationPlugin.externalAuthenticationTimeout))
        else:
            irclib.sendExternalNotice(sourceNick, "Authentication failed, username or password incorrect!")



    def onChannelMessage(self, irclib, source, message):
        if(message == "!punishlist"):
            listOfPunishedUsers = [user.nick for user in irclib.getUserList().values() if user.dataStore.getAttributeDefault("isPunished", False)]
            irclib.sendChannelMessage("Currently in punish-mode: %s" % (", ".join(listOfPunishedUsers)))
        elif((len(message.split()) >= 2) and (message.split()[0] == "!punish")):
            name = message.split()[1]
            self.punish(irclib, name)
        elif((len(message.split()) >= 2) and (message.split()[0] == "!pardon")):
            listOfPunishedUsers = [user.nick for user in irclib.getUserList().values() if user.dataStore.getAttributeDefault("isPunished", False)]
            name = message.split()[1]
            if(name in listOfPunishedUsers):
                if(source.isAdmin() and source.nick != name):
                    irclib.getUserList()[name].dataStore.removeAttribute("isPunished")
                    irclib.sendChannelMessage("Yo.")
                else:
                    irclib.sendChannelMessage("What makes you think that I would accept a command from you? :P")



if __name__ == "__main__":
    pass
