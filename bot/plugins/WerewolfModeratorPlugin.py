import random, logging, UserList, datetime

class WerewolfModeratorPlugin:

    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface

    def getVersionInformation(self):
        return("$Id: WerewolfModeratorPlugin.py 315 2007-06-06 15:24:26Z terralthra $")

    @classmethod
    def getDependencies(self):
      return(["AuthenticationPlugin"])

    timerStart = 0  
    players = []
    werewolves = []
    seer = []
    deadplayers = []
    gameState = "idle"
    gamePhase = "night"
    seerHasAsked = False
    werewolfTarget = {}
    werewolfJointTarget = False
    lynchTarget = {}
    timerTotalSeconds = 20

    def endGame( self, irclib ):
        allplayers = self.deadplayers + self.players + self.seer + self.werewolves
        for i in allplayers:
            if( irclib.getUserList().findByNameDefault( i ) ):
                irclib.sendPrivateNotice( irclib.getUserList().findByName( i ), "The game has ended.")
        self.deadplayers = []
        self.gameState = "idle"
        self.players = []
        self.werewolves = []
        self.seer = []
        seerHasAsked = False
        werewolfTarget = {}
        werewolfJointTarget = False
        lynchTarget = {}
                    
    def onTimer( self, irclib ):
        if( self.gameState == "playing" and self.gamePhase == "sunset" ):
            deltatime = datetime.datetime.utcnow() - self.timerStart
            if(( deltatime.days != 0 ) or ( deltatime.seconds >  self.timerTotalSeconds ) ):
                irclib.sendChannelMessage("Time's up.")
                self.gamePhase = "night"
                self.processNightPhase( irclib )

    def echoRemainingPlayers( self, irclib ):
        playersLeft = self.players + self.werewolves + self.seer
        playersLeft.sort()
        irclib.sendChannelMessage( "Remaining players (" + str( len( playersLeft ) ) + ") are: " + str( playersLeft ) )
        irclib.sendChannelMessage( "Corpses (" + str( len( self.deadplayers ) )+ "): " + str( self.deadplayers ) )

    def didWerewolvesWin( self ):
        if( len( self.werewolves ) >= len( self.seer + self.players ) ):
            return True
        else:
            return False

    def reportWerewolfWin( self, irclib ):
        irclib.sendChannelMessage("The werewolves change shape and overpower the remaining villagers! Werewolves win!")
        irclib.sendChannelMessage("Werewolf survivor(s): " + str( self.werewolves ) )
        if( len( self.seer ) > 0 ):
            irclib.sendChannelMessage("Seer (if alive): "  + str( self.seer ) )
        irclib.sendChannelMessage("Final villager(s): " + str( self.players ) )
        irclib.sendChannelMessage("Corpses: " + str( self.deadplayers ) )
        self.endGame( irclib )

    def didPlayersWin( self ):
        if( len( self.werewolves ) == 0 ):
            return True
        else:
            return False

    def reportPlayerWin( self, irclib ):
        irclib.sendChannelMessage("You killed both werewolves! Villagers win!")
        if( len( self.seer ) > 0 ):
            irclib.sendChannelMessage("Seer (if alive): "  + str( self.seer ) )
        irclib.sendChannelMessage("Final villager(s): " + str( self.players ) )
        irclib.sendChannelMessage("Corpses: " + str( self.deadplayers ) )
        self.endGame( irclib )
        

    def processNightPhase( self, irclib ):
        irclib.sendChannelMessage( "Night falls, and with it comes the baying of wolves!" )
        self.echoRemainingPlayers( irclib )
        self.seerHasAsked = False
        self.werewolfJointTarget = False
        self.werewolfTarget = {}
        for i in self.werewolves:
            irclib.sendPrivateNotice( irclib.getUserList().findByName( i ), "Please choose which villager to eat. /notice " + irclib.nickname + " eat <player name> to vote.")
        if( len( self.seer )> 0 ):
            irclib.sendPrivateNotice( irclib.getUserList().findByName( self.seer[0] ), "Please choose a villager about which to dream. /notice " + irclib.nickname + " dream <player name> to choose.")
        else:
            self.seerHasAsked = True

    def isSomeoneAPlayer(self, name ):
        players = self.werewolves + self.seer + self.players
        if( name in players ):
            return True
        else:
            return False

    def isSomeoneAWerewolf( self, name ):
        if( name in self.werewolves ):
            return True
        else:
            return False
            
    def beginDayPhase(self, irclib):
        self.lynchTarget = {}
        irclib.sendChannelMessage( "Dawn breaks, and the villagers discover that the werewolves have eaten: " + self.werewolfJointTarget + ".")
        if( self.werewolfJointTarget in self.seer ):
            self.seer.remove( self.werewolfJointTarget )
            irclib.sendChannelMessage("He or she was the seer! OMFG!")
        else:
            self.players.remove( self.werewolfJointTarget )
            irclib.sendChannelMessage("He or she was a normal villager.")
        self.deadplayers.append( self.werewolfJointTarget )
        remainingPlayers = self.players + self.seer + self.werewolves
        for i in remainingPlayers:
            irclib.sendPrivateNotice( irclib.getUserList().findByName( i ), "The night has ended.")
            self.lynchTarget[ i ] = None
        if( self.didWerewolvesWin() ):
            self.reportWerewolfWin( irclib )
        else:
            irclib.sendChannelMessage( "Your soul cries out for vengeance! Type '!lynch <player name>' once you are sure who you want to lynch. Simple majority wins." )
            irclib.sendChannelMessage( "Remember, all conversation during the day must be in public. No side conversations, and dead players must remain silent on the subject of the game.")
            self.echoRemainingPlayers(irclib)


    def processSeerNotice( self, irclib, source, message ):
        if( self.seerHasAsked ):
            irclib.sendPrivateNotice(source, "You can't ask twice in one night!")
        else:
            if( message[:len("dream ")] == "dream "):
                dreamTarget = message[len("dream "):]
                if( self.isSomeoneAPlayer( dreamTarget ) ):
                    self.seerHasAsked = True
                    if( self.isSomeoneAWerewolf( dreamTarget ) ):
                        irclib.sendPrivateNotice( source, "Yes, " + message[len("dream "):] + " is a werewolf.")
                    else:
                        irclib.sendPrivateNotice( source, "No, " + message[len("dream "):] + " is not a werewolf.")
                else:
                    irclib.sendPrivateNotice( source, "That's not a player!" )
            else:
                irclib.sendPrivateNotice( source, "Malformed request. Proper syntax is '/notice " +irclib.nickname + " dream <player name>" )

    def processWerewolfNotice( self, irclib, source, message):
        if( message[:len("eat ")] == "eat "):
            eatTarget =  message[len("eat "):]
            if( self.isSomeoneAPlayer( eatTarget ) ):
                if( self.isSomeoneAWerewolf( eatTarget ) ):
                    irclib.sendPrivateNotice( source, "You can't eat a werewolf." )
                    return False
                else:
                    self.werewolfTarget[ source.getName() ] = eatTarget
                    return True
            else:
                irclib.sendPrivateNotice( source, "That is not a valid target." )
                return False
        else:
            irclib.sendPrivateNotice( source, "Malformed request. Proper syntax is '/notice " + irclib.nickname + " eat <player name>")
            return False

    def handleWerewolfTargets( self, irclib, source, message ):
        if( self.werewolfTarget.values().count( message[len("eat "):] ) == len( self.werewolves ) ):
            self.werewolfJointTarget  = self.werewolfTarget[ source.getName() ]
            for i in self.werewolves:
                irclib.sendPrivateNotice( irclib.getUserList().findByName( i ), "Rah! You eat: " + self.werewolfJointTarget + "!" )
        else:
            for i in self.werewolves:
                if( len( self.werewolfTarget.values() ) == len( self.werewolves ) ):
                    irclib.sendPrivateNotice( irclib.getUserList().findByName( i ), "There is a disagreement about who to eat! A listing of potential targets follows, please reach a decision and vote again if necessary.")
                irclib.sendPrivateNotice( irclib.getUserList().findByName( i ), self.werewolfTarget )

    def handleLynchVote( self, irclib, source, message ):
        if( self.isSomeoneAPlayer( source.getName() ) ):
            if( self.isSomeoneAPlayer( message[len("!lynch "):] ) ):
                    if( source.getName() == message[len("!lynch "):] ):
                        irclib.sendChannelMessage( "You can't vote for yourself, " + source.getName() + ".")
                        return False
                    else:
                        if( self.lynchTarget[ source.getName() ] ):
                            irclib.sendChannelMessage( "Vote changed, " + source.getName() + ".")
                        else:
                            irclib.sendChannelMessage( "Vote recorded, " + source.getName() + ".")
                        self.lynchTarget[ source.getName() ] = message[ len("!lynch "): ]
            else:
                irclib.sendChannelMessage( message[len("!lynch "):] + " is not a player." )
        else:
            if( source.isAuthed() ):
                irclib.sendChannelMessage("You can't vote, " + source.getName() + ", you aren't playing!" )
            else:
                irclib.sendChannelMessage("You can't vote, " + source.getCanonicalNick() + ", you aren't playing!" )
        
    def handleUnlynch( self, irclib, source, message ):
        if( self.isSomeoneAPlayer( source.getName() ) ):
            self.lynchTarget[ source.getName() ] = None
            irclib.sendChannelMessage("Lynch vote rescinded, " + source.getName() +".")
        else:
            if( source.isAuthed() ):
                irclib.sendChannelMessage("You can't unlynch, " + source.getName() + ", you aren't playing!" )
            else:
                irclib.sendChannelMessage("You can't unlynch, " + source.getCanonicalNick() + ", you aren't playing!" )
            

    
    def processLynchVotes( self, irclib ):
        for i in self.lynchTarget.keys():
            remainingPlayers = self.seer + self.players + self.werewolves
            if( self.lynchTarget[ i ] and self.lynchTarget.values().count( self.lynchTarget[ i ] ) >  len( remainingPlayers ) / 2 ):
                self.lynchTarget[ "final" ] = self.lynchTarget[ i ]
                irclib.sendChannelMessage("You have decided to lynch " + self.lynchTarget[ "final" ] + "!")
                lynchees = set(self.lynchTarget.values())
                hate_list = dict([ (lynchee, [k for k, v in self.lynchTarget.items() if v == lynchee]) for lynchee in lynchees ] )
                for k, v in hate_list.items():
                    irclib.sendChannelMessage( '%s <-- %s' % (k, ', '.join(v)) )                
                if( self.lynchTarget[ "final" ] in self.players ):
                    self.players.remove( self.lynchTarget[ "final" ] )
                    irclib.sendChannelMessage("He or she was a villager. You paranoid gits!" )
                elif( self.lynchTarget[ "final" ] in self.werewolves ):
                    self.werewolves.remove( self.lynchTarget[ "final"  ] )
                    irclib.sendChannelMessage("He or she was a werewolf. Good call!" )
                elif( self.lynchTarget[ "final" ] in self.seer ):
                    self.seer.remove( self.lynchTarget[ "final" ] )
                    irclib.sendChannelMessage("That was the SEER! OMFG!")
                self.deadplayers.append( self.lynchTarget[ "final" ] )
                return True
                    
        
    def onNotice( self, irclib, source, message ):
        if( self.gamePhase == "night" and self.gameState == "playing"):
            if( message[ :len( "authenticate" ) ] == "authenticate" ):
                return False
            else:
                if( source.getName() in self.seer ):
                    self.processSeerNotice( irclib, source, message )
                elif( self.isSomeoneAWerewolf( source.getName() ) ):
                    if( self.processWerewolfNotice( irclib, source, message ) ):
                        self.handleWerewolfTargets( irclib, source, message )
                if( self.werewolfJointTarget and self.seerHasAsked ):
                    self.gamePhase = "day"
                    self.beginDayPhase( irclib )
                return True


    
    def initGame(self, irclib):
        #random.seed()
        self.players.sort()
        werewolf1 = random.choice( self.players )
        self.players.remove( werewolf1 )
        self.werewolves.append( werewolf1 )
        werewolf2 = random.choice( self.players )
        self.players.remove( werewolf2 )
        self.werewolves.append( werewolf2 )
        seer = random.choice( self.players )
        self.players.remove( seer )
        self.seer.append( seer )
        irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 0 ] ), "You are a werewolf, along with your fellow villager, " + self.werewolves[ 1 ] + "! You thirst for the blood of your fellow villagers!" )            
        irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 1 ] ), "You are a werewolf, along with your fellow villager, " + self.werewolves[ 0 ] + "! You thirst for the blood of your fellow villagers!" )            
        for i in self.seer:
            irclib.sendPrivateNotice( irclib.getUserList().findByName( self.seer[ 0 ] ), "You are a Seer! Your prophetic dreams allow you to identify werewolves!")
        for i in self.players:
            irclib.sendPrivateNotice( irclib.getUserList().findByName( i ), "You are a villager! Nothing special, but you'd like to keep living.")
        self.gameState = "playing"
        irclib.sendChannelMessage("Night will begin in 20 seconds. Any player talking during night will be disqualified.")
        self.timerStart = datetime.datetime.utcnow()
        self.gamePhase = "sunset"
        

    def onChannelMessage(self, irclib, source, message):
        if( self.gameState == "playing" ):
            if( message == "players?" ):
                self.echoRemainingPlayers(irclib)

        if( self.gameState == "playing" and self.gamePhase == "day" ):
            if( message[:len("!lynch ")] == "!lynch " ):
                self.handleLynchVote( irclib, source, message )
                if( self.processLynchVotes( irclib ) ):
                    if( self.didWerewolvesWin() ):
                        self.reportWerewolfWin( irclib )
                    elif( self.didPlayersWin() ):
                        self.reportPlayerWin( irclib )
                    else:
                        self.gamePhase = "postlynch"
                        irclib.sendChannelMessage("Type !sunset to continue to the next night.")
        if( self.gameState == "playing" and self.gamePhase == "day" ):
            if( message[:len("!unlynch")] == "!unlynch" ):
                self.handleUnlynch( irclib, source, message )


        if( self.gamePhase == "postlynch" ):
            if( message == "!sunset" ):
                self.gamePhase = "sunset"
                irclib.sendChannelMessage("Night will begin in 20 seconds. Any player talking during night will be disqualified.")
                self.timerStart = datetime.datetime.utcnow()

        if( self.gamePhase == "night" and self.gameState == "playing" ):
            if( source.getName() in self.players ):
                self.players.remove( source.getName() )
                irclib.sendChannelMessage("Disqualifying you from the game for talking, " + source.getName() + ". You were a perfectly normal villager.")
            if( source.getName() in self.seer ):
                self.seer.remove( source.getName() )
                irclib.sendChannelMessage("Disqualifying you from the game for talking, " + source.getName() + ". You were the seer.")
            if( source.getName() in self.werewolves ):
                self.werewolves.remove( source.getName() )
                irclib.sendChannelMessage("Disqualifying you from the game for talking, " + source.getName() + ". You were a werewolf.")
            if( len( self.players + self.werewolves + self.seer ) == 0 ):
                irclib.sendChannelMessage("Wow. This game is full of phail. Aborting.")
                self.endGame( irclib )
            else:
                if( self.didWerewolvesWin() ):
                    self.reportWerewolfWin( irclib )
                elif( self.didPlayersWin() ):
                    self.reportPlayerWin( irclib )

        if( self.gameState == "playing" and self.gamePhase == "day"):
            if( message == "lynchvotes?" ):
                #irclib.sendChannelMessage( str( self.lynchTarget ) )
                lynchees = set(self.lynchTarget.values())
                hate_list = dict([ (lynchee, [k for k, v in self.lynchTarget.items() if v == lynchee]) for lynchee in lynchees ] )
                for k, v in hate_list.items():
                    irclib.sendChannelMessage( '%s <-- %s' % (k, ', '.join(v)) )
       
        if( self.gameState == "idle" ):
            if( message == "In Quas Corp Xen!" ):
                self.gameState = "adding"
                self.players.append( source.getName() )
                irclib.sendChannelMessage( "Beginning a game of werewolf. Type '!addme' to play, 'players?' to list the players, and 'Por!' to begin the game." )

        
        
        if( self.gameState == "adding"):
            if( message == "!removeme" ):
                if( source.getName() in self.players):
                    self.players.remove( source.getName() )
                    irclib.sendChannelMessage("You've been removed, " + source.getName() + ". There are now " + str( len( self.players) ) + " players.")
            if( message == "!addme" ):
                dontAddMe = False
                for i in self.players:
                    if ( source.getName() == i ):
                        irclib.sendChannelMessage( "You are already playing, " + source.getName() + ".")
                        dontAddMe = True
                if( source.isAuthed() == False ):
                    irclib.sendChannelMessage( "You must be authed to play, " + source.getCanonicalNick() + "." )
                    dontAddMe = True
                if( dontAddMe == False ):
                    self.players.append( source.getName() )
                    irclib.sendChannelMessage( "Adding you to the game, " + source.getName() + ". There are now " + str( len( self.players) ) + " players.")
            if( message == "players?" ):
                self.players.sort()
                irclib.sendChannelMessage( "Players so far (" + str( len( self.players ) ) + ") are: " + str( self.players ) )
            if( message == "Por!" ):
                if( len( self.players ) < 6 ):
                    irclib.sendChannelMessage("Fewer than the recommended amount of players. 'Ex!' to override." )
                else:
                    self.gameState = "playing"
                    self.initGame(irclib)
            if( message == "Ex!" ):
                if( len(self.players ) < 3 ):
                    irclib.sendChannelMessage("You can't even play a fake game with less than 3 players." )
                else:
                    self.gameState = "playing"
                    self.initGame(irclib)
                    irclib.sendPrivateMessage( irclib.getUserList().findByName( "Terralthra" ), "This is a test message. Werewolves: " + str( self.werewolves ) + ". Seer: " + str( self.seer ) )
        if( self.gameState != "idle" ):
            if( message == "An Quas Corp Xen!" ):
                irclib.sendChannelMessage( "Game is over because it was manually aborted." )
                self.endGame( irclib )
