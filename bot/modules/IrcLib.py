"""IrcLib.py

This file manages the IRC connection with the server via the
LowlevelIrcLib class.
"""

import socket, select, re, sys, time, datetime, logging, string
import util, UserList

timeout = 1
_linesep_regexp = re.compile("\r?\n")

class AuthorizationError(Exception):
    pass

class ServerConnectionError(Exception):
    pass

class IrcError(Exception):
    pass





class LowlevelIrcLib:
    """IRC client code.

    This class handles the low-level interaction with the IRC
    server.
    """

    reIncomingGenericMessage = re.compile("(:(.*?)\\s)?(\\S*)([^:]*)(:(.*))?")
    reFilterFormatCodes = re.compile(r"(?:\x02|\x16|\x1F|\x03(?:\d{1,2}(?:,\d{1,2})?)?)")

    def __init__(self):
        """Initialise the LowlevelIrcLib.

        Internal use.
        """
        self.socket = None
        self.connected = False
        self.previous_buffer = ""
        self.eventTarget = None
        self.nickname = None
        self.channel = None
        self.channelTopic = None
        self.userLists = {}
        self.messageTimer = 0
        self.channelModes = ""
        self.hasProperName = True # True if there were no nick-conflicts (= we can ident)
        self.shutdownInitiated = False
        self.receivingNAMESResult = False
        self.namesBuffer = []
    
    # Decorator for methods that require channel operator privileges
    @util.decorator
    def requirePrivileges(func, self, *args, **kwargs):
        """Warn when function expects +o mode but this isn't true.

        Raises an exception when func is called and expects RTBot
        to have +o mode, while this isn't the case.

        Debug/Logging use.
        """
        if not self.isOp():
            raise AuthorizationError("Tried to call " + func.__name__ + " without channel operator privileges")
        func(self, *args, **kwargs)
        
    #---------------------------------------------------------------------------------
    #                      PUBLIC METHODS
    #---------------------------------------------------------------------------------        
        
    def connect(self, server, port, nickname, username, realname):
        """Connect to IRC.

        Connects the Bot to the IRC server using the provided settings.
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind(("", 0))
            self.socket.connect((server, port))
            logging.info("CONNECTED")
        except socket.error, x:
            self.socket.close()
            self.socket = None
            raise ServerConnectionError, "Couldn't connect to socket: %s" % x
        self.connected = True
        self.changeNick(nickname)
        self.changeUser(username, realname)

    def disconnect(self):
        """Disconnect from IRC.

        Closes the socket to the IRC server.
        """
        logging.info("Closing socket...")
        if(self.socket):
            self.socket.close()

    def quit(self, message):
        """/quit <message>

        Sends the /quit command to the IRC server.
        """
        try:
            self.shutdownInitiated = True
            self.sendRawMsg("QUIT " + message)
            logging.info("QUIT SENT")
        except:
            logging.debug("tried to quit, but failed")

    def changeNick(self, nickname):
        """/nick <nickname>

        Changes the bot's nickname. Required for nickname collisions.
        """
        self.sendRawMsg("NICK " + nickname)
        logging.info("NICK SENT")
        self.nickname = nickname

    def changeUser(self, username, realname):
        """/user <username> 0 * :<realname>

        Changes the bot's username and realname info.
        """
        self.sendRawMsg("USER %s 0 * :%s" % (username, realname))
        logging.info("USER SENT")

    def joinChannel(self, channel):
        """/join <channel>

        Makes the bot join a channel and prepare a UserList for it.
        If the channel is passworded (+k), it SHOULD be possible to
        join it via setting the channel par to "#channel password".
        """
        # create a new user list for this channel
        self.userLists[channel] = UserList.UserList()
        
        # send the JOIN request
        logging.info("JOIN SENT")
        self.sendRawMsg("JOIN :%s" % (channel))
        self.channel = channel

    def getUserList(self):
        """Return the channel userlist.

        Provides access to a channel's UserList.
        """
        if(self.channel):
            return(self.userLists[self.channel])
        else:
            return(None)

    def getChannelModes(self):
        """Return the channel modes.

        Provides access to channelModes.
        """
        return(self.channelModes)

    def sendChannelMessage(self, msg):
        """Send <msg> to the channel

        Raises exception when:
                * no channel has been joined yet
                * the bot tried to send a message to a non-trusted ("suspicious") channel (hardcoded values)

        Sets the RTBot text colour to 10 (light blue).
        """
        if(self.channel == None):
            raise Exception("ERROR: Tried to send channel message without being in a channel yet.")
        elif not (self.channel == "#RollingThunder" or self.channel == "#RollingThunder.test" or self.channel == "#RT.development"):
            raise Exception("ERROR: Tried to send channel message to a suspicious channel: " + self.channel)
        else:
            logging.info("%s-->#: %s" % (self.nickname, msg))
            for line in self.splitLongMessages(msg):
                self.sendRawMsg("PRIVMSG %s :\x0310%s" % (self.channel, line))

    # target: User object
    def sendPrivateMessage(self, target, msg):
        """Send <msg> to <target> via /msg
    
        Raises exception when:
                * the bot tries to /msg "none"
        
        No colour code is applied here, differently from sendChannelMessage. 
        """
        if(str(target.nick).lower() == "none"):
            logging.debug(
                "========================================\n"
                "TRIED TO PM 'NoNe'!\n"
                "========================================")
            raise Exception("TRIED TO PM 'NoNe'!")
        logging.info("%s-->%s: %s" % (self.nickname, target.nick, msg))
        for line in self.splitLongMessages(msg):
            self.sendRawMsg("PRIVMSG %s :%s" % (target.nick, line)) # Where's the colour code? XXX

    # target: User object
    def sendPrivateNotice(self, target, msg):
        """Send <msg> to <target> via /notice

        No colour code is applied here, differently from sendChannelMessage.
        See also: sendExternalNotice
        """
        for line in self.splitLongMessages(msg):
            self.sendRawMsg("NOTICE %s :%s" % (target.nick, line)) # Where's the colour code? XXX

    # target: nick
    def sendExternalNotice(self, targetNick, msg):
        """Send <msg> to <targetNick> via /notice

        No colour code is applied here, differently from sendChannelMessage.
        This function only expects a nickname and can be used to /notice people
        not in the channel. This is used e.g. by the AuthenticationPlugin.
        """
        for line in self.splitLongMessages(msg):
            self.sendRawMsg("NOTICE %s :%s" % (targetNick, line)) # Where's the colour code? XXX

    def sendChannelEmote(self, emote):
        """/me <emote>

        Makes the bot say it's doing something.
        """
        logging.info("%s-->#: * %s" % (self.nickname, emote))
        self.sendRawMsg("PRIVMSG %s :\x01ACTION %s\x01" % (self.channel, emote))

    # target: User object
    def sendPrivateEmote(self, target, emote):
        """/me <emote>, over /msg <target>

        Makes the bot say it's doing something in private /msg chat.
        """
        logging.info("%s-->%s: * %s" % (self.nickname, target.nick, emote))
        self.sendRawMsg("PRIVMSG %s :\x01ACTION %s\x01" % (target.nick, emote))

    # targets: List of strings (nicks)
        # XXX requires decoration?
    def setModes(self, flagModifiers, targets):
        """/mode channel <flagModifiers> <targets>

        Sets channel ops. NOT decorated -- won't fire RequirePrivileges.
        Does nothing if the bot isn't opped. Inconsistent with setChannelMode.

        This updates the channel's userList -- use setChannelMode for channel modes (like +k).
        """
        if(self.getUserList()[self.nickname].hasOp()):
            for startingIndex in range(0, len(targets), 6): # ?!
                currentFlagModifiers = flagModifiers[startingIndex*2:(startingIndex+6)*2] # ?!
                currentTargets = targets[startingIndex:(startingIndex+6)]
                logging.info("* Mode changed: %s %s" % (currentFlagModifiers, currentTargets))
                self.sendRawMsg("MODE %s %s %s" % (self.channel, currentFlagModifiers, string.join(currentTargets, " ")))
                self.userLists[self.channel].onMode(self.nickname, currentTargets, currentFlagModifiers, self.channel)

#    def setUserMode(self, flags, target):
#        assert re.match(r"[-+][diRwx]", flags) # available quakenet user modes
#        logging.info("* Mode changed: %s-->%s" % (target, flags))
#        self.sendRawMsg("MODE %s %s" % (target, flags))
#        self.userLists[self.channel].onUserMode(self.nickname, [target], flags, self.channel)

#    @requirePrivileges
    def setChannelMode(self, flags, target = ""):
        """/mode channel <flagModifiers> <targets>

        Sets channel ops. IS decorated -- will fire RequirePrivileges.
        Raises an exception if the bot isn't opped. Inconsistent with setModes.

        Does NOT update the channel's userList -- use setModes for user modes (like +o).
        """
#        assert re.match(r"[-+][bcCdDiklmnNoprstuv]", flags) # available quakenet channel modes
        logging.info("* Mode changed: %s %s-->%s" % (self.channel, target, flags))
        self.sendRawMsg("MODE %s %s %s" % (self.channel, flags, target))

    # target: User object
    def kick(self, target, reason):
        """/kick <target> <reason>

        Is decorated: raises an exception if the bot isn't opped.
        """
        self.sendRawMsg("KICK %s %s :%s" % (self.channel, target.nick, reason))

    # target: User object
#    @requirePrivileges
#    def unOp(self, target):
#        self.setChannelMode("-o", target.nick)

#    def isOp(self, target = None):
#        if(target == None):
#            target = self.nickname
#        return(self.userLists[self.channel].areAllFlagsSet(target, 'o'))
    
    # target: User object
    def doWho(self, target):
        """/who <target>

        Expects a user object -- use only on people in the channel.
        See also doExternalWho.
        """
        self.sendRawMsg("WHO %s" % (target.nick))

    # target: nick
    def doExternalWho(self, targetNick):
        """/who <targetNick>

        Expects a nickname -- use only for people NOT in the channel.
        See also doWho.
        """
        self.sendRawMsg("WHO %s" % (targetNick))

    # target: User object
    def doWhois(self, target):
        """/whois <target>

        Expects a user object -- use only on people in the channel.
        See also doExternalWhois.
        """
        self.sendRawMsg("WHOIS %s" % (target.nick))

    # target: nick
    def doExternalWhois(self, targetNick):
        """/who <targetNick>

        Expects a nickname -- use only for people NOT in the channel.
        See also doWho.
        """
        self.sendRawMsg("WHOIS %s" % (targetNick))

        #XXX Not decorated!
    def setChannelTopic(self, topic):
        """/topic <topic>

        Not decorated: undocumented behaviour when the bot is not opped.
        """
        self.sendRawMsg("TOPIC %s :%s" % (self.channel, topic))

    def registerEventTarget(self, newEventTarget):
        """Required for event driven programming.
        """
        self.eventTarget = newEventTarget

    def unregisterEventTarget(self):
        """Required for event driven programming.
        """
        self.eventTarget = None

    def requestChannelModesUpdate(self):
        """/mode channel

        No real use, if one had to guess. Proably forces UserList to update.
        """
        self.sendRawMsg("MODE :%s" % (self.channel))

    #---------------------------------------------------------------------------------
    #                      INTERNAL METHODS
    #---------------------------------------------------------------------------------
    
    def decodeGenericMessage(self, message):
        """Decodes incoming messages.

        Internal use.
        """
        message = self.reFilterFormatCodes.sub("", message)
        reResult = self.reIncomingGenericMessage.match(message)
        return((reResult.group(2), reResult.group(3), (reResult.group(4)[1:]).strip().split(" "), reResult.group(6)))

    def extractSource(self, raw):
        return(raw.split("!")[0])

    def processMessage(self, line):
        message = self.decodeGenericMessage(line)
        if(message):
            (prefix, command, arguments, trailing) = message
            #logging.debug("--> Message: [Prefix: %s, Command: %s, Arguments: %s, Trailing: %s]" % (prefix, command, arguments, trailing))

            if(prefix != None):
                source = self.extractSource(prefix)
            else:
                source = ""

        # else: shouldn't occur
        else:
            logging.debug("--> Error: couldn't decode message")
            return

        # Process message
        self.handleIncomingMessage(source, command, arguments, trailing)

    def handleIncomingMessage(self, source, command, arguments, trailing):
        """Translates incoming messages to events.

        Internal use. Lots of magic numbers.
        """
        # try decoding chat message
        if(command == "PING"):             
            self.sendPong(trailing)
        elif(command == "376"):        # End of /MOTD command
            self.eventTarget.onConnected()
        elif(command == "MODE"):
            # if the first character of the target argument is a #, then it's a channel MODE, otherwise a user MODE
            if(arguments[0][0] == '#' and len(arguments)==2):
                self.requestChannelModesUpdate()
                self.eventTarget.onChannelMode(self.getUserList()[source], arguments[1], arguments[0])
            elif((arguments[0] == self.nickname) or (arguments[1] == self.nickname)):
                # sometimes, servers are MODEing users for registration even before they have joined a channel
                # we'll ignore those
                pass
            else:
                self.userLists[self.channel].onMode(source, arguments[2:], arguments[1], arguments[0])
                if(self.getUserList().has_key(source)):
                    self.eventTarget.onUserMode(self.getUserList()[source], arguments[2:], arguments[1], arguments[0])
                else:
                    self.eventTarget.onExternalUserMode(source, arguments[2:], arguments[1], arguments[0])
        elif(command == "324"):
            if(len(arguments) > 2):
                self.channelModes = arguments[2]
            else:
                logging.debug("Error: MODE response without third argument!")
        elif(command == "353"):        # part of NAMES result
            # Adding more names
            self.receivingNAMESResult = True
            self.namesBuffer.append(trailing)
        elif(command == "366"):        # terminator of NAMES result
            # Finished new list
            self.receivingNAMESResult = False
            self.userLists[self.channel].rebuildUserList(self.namesBuffer)
            for user in self.userLists[self.channel].values():
                user.dataStore.setAttribute("timeOfLastWhoAttempt", datetime.datetime.utcnow())
                user.dataStore.setAttribute("numberOfWhoAttempts", 1)
                self.doWho(user)
            self.namesBuffer = []
        elif(command == "433"):     #Nickname is already in use.
            self.changeNick(self.nickname + "_")
        elif(command == "352"):            # first part of a WHOIS result, 2nd part is channels as 319, 3rd part is server as 312, 4th part is idle time as 317, 5th part is EOL as 318
            if(len(arguments) >= 5):
                username = arguments[2]
                host = arguments[3]
                server = arguments[4]
                nick = arguments[5]
                unknown = arguments[6]
                userinfo = trailing[2:]
                self.userLists[self.channel].reportWho(nick, username, host, userinfo)
                if(self.getUserList().has_key(nick)):        # the user might have left the channel already!
                    self.eventTarget.onWhoResult(self.getUserList()[nick])
                else:
                    self.eventTarget.onExternalWhoResult(nick, username, host, userinfo)
            else:
                logging.debug("Error: WHOIS response with less than four arguments!")
        elif(command == "311"):            # first part of a WHOIS result, 2nd part is channels as 319, 3rd part is server as 312, 4th part is idle time as 317, 5th part is EOL as 318
            if(len(arguments) >= 5):
                nick = arguments[1]
                username = arguments[2]
                host = arguments[3]
                unknown = arguments[4]
                userinfo = trailing
                self.userLists[self.channel].reportWhois(nick, username, host, userinfo)
                if(self.getUserList().has_key(nick)):        # the user might have left the channel already!
                    self.eventTarget.onWhoisResult(self.getUserList()[nick])
                else:
                    self.eventTarget.onExternalWhoisResult(nick, username, host, userinfo)
            else:
                logging.debug("Error: WHOIS response with less than four arguments!")
        elif(command == "401"):        # WHOIS: "no such nick"
            nick = arguments[1]
            logging.debug("WHOIS: no such nick (%s)" % (nick))
            self.eventTarget.onExternalWhoisResult(nick, None, None, None)
        elif(command == "NOTICE"):
            # IRC nick names are not case sensitive. Neither are channel names
            if(arguments[0].lower() == self.nickname.lower()):
                # if the notice contains a dot (e.g. underworld.no.quakenet.org) then we assume the message
                # comes from the IRC server, because at least Quakenet doesn't allow dots in nicknames
                if(not self.getUserList()):
                    self.eventTarget.onServerMessage(source, trailing)
                elif(self.getUserList().has_key(source)):
                    self.eventTarget.onNotice(self.getUserList()[source], trailing)
                else:
                    self.eventTarget.onExternalNotice(source, trailing)
        elif(command == "PRIVMSG"):
            # IRC nick names are not case sensitive. Neither are channel names
            if(arguments[0].lower() == self.nickname.lower()):
                #print "|%s|%s|%s|%s|" % (trailing, trailing[:8], trailing[-1], trailing[8:-1])
                if((trailing[:8] == "\x01ACTION ") and (trailing[-1] == "\x01")):
                    if(self.getUserList().has_key(source)):
                        self.eventTarget.onPrivateEmote(self.getUserList()[source], trailing[8:-1])
                    else:
                        self.eventTarget.onExternalPrivateEmote(source, trailing[8:-1])
                else:
                    if(self.getUserList().has_key(source)):
                        self.eventTarget.onPrivateMessage(self.getUserList()[source], trailing)
                    else:
                        self.eventTarget.onExternalPrivateMessage(source, trailing)
            elif(arguments[0].lower() == self.channel.lower()):
                #print "|%s|%s|%s|%s|" % (trailing, trailing[:8], trailing[-1], trailing[8:-1])
                if((trailing[:8] == "\x01ACTION ") and (trailing[-1] == "\x01")): 
                    self.eventTarget.onChannelEmote(self.getUserList()[source], trailing[8:-1])
                else:
                    self.eventTarget.onChannelMessage(self.getUserList()[source], trailing, arguments[0])
            else:
                logging.error("Received a message not meant for me! arguments: %s. source: %s. trailing: %s" % (arguments, source, trailing))
        elif(command == "JOIN"):
            if(source == self.nickname):
                self.eventTarget.onJoinedChannel()
            else:
                self.userLists[self.channel].onJoin(source, arguments[0])
                self.doWho(self.userLists[self.channel][source])
                self.eventTarget.onJoin(self.getUserList()[source], arguments[0])
            self.requestChannelModesUpdate()
        elif(command == "NICK"):
            self.userLists[self.channel].onChangeNick(source, trailing)
            self.eventTarget.onChangeNick(source, self.getUserList()[trailing])
        elif(command == "PART"):
            if(trailing == None):
                self.eventTarget.onLeave(self.getUserList()[source], arguments[0], "")
                self.userLists[self.channel].onLeave(source, arguments[0], "")
            else:
                self.eventTarget.onLeave(self.getUserList()[source], arguments[0], trailing)
                self.userLists[self.channel].onLeave(source, arguments[0], trailing)
        elif(command == "QUIT"):
            self.eventTarget.onQuit(self.getUserList()[source], trailing)
            self.userLists[self.channel].onQuit(source, trailing)
        elif(command == "KICK"):
            if(arguments[0] == self.channel and arguments[1] == self.nickname):
                channel = self.channel
                self.channel = None
                self.joinChannel(channel)
            else:
                self.eventTarget.onKick(self.getUserList()[source], self.getUserList()[arguments[1]], trailing, arguments[0])
                self.userLists[self.channel].onKick(source, arguments[1], trailing, arguments[0])
        elif(command == "TOPIC"):
            if(arguments[0] == self.channel):
                self.channelTopic = trailing
                self.eventTarget.onChannelTopicChange(self.getUserList()[source], arguments[0])
            else:
                raise IrcError("IrcError: unrecognised incoming TOPIC message!")
        elif(command == "ERROR"):
            #logging.debug("Error ERROR-command in handleIncomingMessage()!")
            raise IrcError("ERROR: ERROR-command in handleIncomingMessage() ('%s')" % (str((source, command, arguments, trailing))))
        return
    
    def sendRawMsg(self, rawmsg):     # throws: socket.error
        """Sends a raw message through the socket.

        Adds Windows-style line delimiters (just to be on the safe
        side of things?). Internal use.
        """
        self.waitUntilReadyToSend()
        if self.socket is None:
            raise ServerConnectionError, "LowLevelIrcLib.sendRawMsg(): We're not connected! (self.socket==None)"
        s = rawmsg + "\r\n"
        self.socket.sendall(s)

    def sendPong(self, id):
        """Pongs pings.

        Teorethically handles ping requests. Internal use.
        """
        self.sendRawMsg("PONG :" + id) # XXX RTBot never seems to pong back. Any idea?

    def receiveDataLooped(self):  # throws: socket.error, ServerConnectionError, KeyboardInterrupt
        """Keeps the bot running. Only stops when the bot is disconnected.

        The three kind of exception that make receiveDataLooped end are:

                * socket.error -- Not connected to Internet. (?)
                * ServerConnectionError -- Connection with the server lost (?)
                * KeyboardInterrupt -- The bot is closing.

        Internal use.
        """
        if(self.eventTarget):
            LastMessageTime = datetime.datetime.now()
            while True:
                try:
                    try:
                        # wait for socket
                        (i, o, e) = select.select([self.socket], [], [], timeout)        # throws?
                        if(len(i) == 0):
                            if datetime.datetime.now() - LastMessageTime > datetime.timedelta(seconds = 60*5):
                                raise ServerConnectionError, "No message received for 2 minutes!"
                            continue
                        new_data = self.socket.recv(2**14)      # throws: socket.error
                        LastMessageTime = datetime.datetime.now()
                    except socket.error, x:
                        raise ServerConnectionError, "LowLevelIrcLib.receiveDataLooped(): select.select() or self.socket.recv() threw a socket.error, the connection must be lost!"
                    if not new_data:
                        # Read nothing: connection must be down.
                        if(self.shutdownInitiated):
                            logging.debug("LowlevelIrcLib.receiveDataLooped(): self.socket.recv() returned without new data, the connection must be down, but we recently sent QUIT, so the server probably just closed the connection as requested.")
                            return
                        else:
                            raise ServerConnectionError, "LowLevelIrcLib.receiveDataLooped(): self.socket.recv() returned without new data, the connection must be lost!"

                    lines = _linesep_regexp.split(self.previous_buffer + new_data)
    
                    # Save the last, unfinished line.
                    self.previous_buffer = lines[-1]
                    lines = lines[:-1]
    
                    for line in lines:
                        logging.debug(line)
                        # Add message to queue
                        try:
                            self.processMessage(line)
                        except socket.error, x:
                            raise ServerConnectionError, "LowLevelIrcLib.receiveDataLooped(): seems like self.socket.sendall() threw a socket.error, the connection must be lost!"

                except KeyboardInterrupt, x:
                    logging.exception("Exception: KeyboardInterrupt in LowLevelIrcLib.receiveDataLooped(), calling the onKeyboardInterrupt event now...")
                    self.eventTarget.onKeyboardInterrupt()
    
    def splitLongMessages(self, message):
        result = []
        while (len(message) > 100):
            splitpos = 0
            contpos = 0
            for i in range(0, 50):
              if(message[99-i] == " "):
                splitpos = i
                contpos = i-1
                break
            result.append(message[:99-splitpos])
            message = message[99-contpos:]
        if(len(message) > 0):
            result.append(message)
        return(result)
    
    def waitUntilReadyToSend(self):
        if self.messageTimer < time.time():
            self.messageTimer = time.time()
        while(self.messageTimer > time.time() + 10):
            time.sleep(0.5)
        self.messageTimer += 2
            




#class LibTestBot:
#               """Dummy bot
#
#               Probably used in the very early development, this bot doesn't seem to work,
#           even by isolating IrcLib.py, Utils.py and moving this to LibTestBot.py. (What I tried)
#
#               Undocumented.
#               """
##    keepRunning = True
#    irc = None
#
#    def run(self):
#        self.irc = LowlevelIrcLib()
#        self.irc.connect("de.quakenet.org", 6667, "LibTestBot", "libtestbot", "LibTestBot")
#        self.irc.registerEventTarget(self)
#        self.irc.run()
#        while True:
#            time.sleep(1)
#
#    def onConnected(self):
#        self.irc.joinChannel("#RollingThunder")
#
#    def onJoinedChannel(self):
#        #self.irc.sendRawMsg("PRIVMSG " + "#RollingThunder" + " :" + "test")
#        pass
#
#    def onPrivateMessage(self, source, message):
#        logging.debug("%s sent a private message: %s" % (source, message))
#        if(message == "quit"):
#            self.irc.quit("test2")
#            raise SystemExit()
#
#    def onChannelMessage(self, source, message, channel):
#        logging.debug("%s sent this to the channel %s message: %s" % (source, channel, message))
#
#    def onNick(self, source, newnick):
#        logging.debug("%s changed nick to %s" % (source, newnick))
#
#    def onKick(self, source, target, channel, reason):
#        logging.debug("%s kicked %s from %s, reason: %s" % (source, target, channel, reason))
#
#    def onMode(self, source, target, flags, channel):
#        logging.debug("%s changed %s's mode to %s in channel %s" % (source, target, flags, channel))
#
#    def onJoin(self, source, channel):
#        logging.debug("%s joined the channel %s" % (source, channel))
#
#    def onLeave(self, source, channel, reason):
#        logging.debug("%s left the channel %s, reason: %s" % (source, channel, reason))
#
#
#
#
#
#if __name__ == "__main__":
#    bot = LibTestBot()
#    bot.run()
