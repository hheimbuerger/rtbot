import random, logging, UserList

class WerewolfModeratorPlugin:

    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface

    def getVersionInformation(self):
        return("$Id: WerewolfModeratorPlugin.py 315 2007-06-06 15:24:26Z terralthra $")

    players = []
    werewolves = []
    seer = []
    gameState = "idle"
    gamePhase = "night"
    seerHasAsked = False
    werewolfTarget = {0: 0, 1: 1, 2: False}
    lynchTarget = {}

    def endGame(self):
        self.gameState = "idle"
        self.players = []
        self.werewolves = []
        self.seer = []
                    

    def echoRemainingPlayers( self, irclib ):
        playersLeft = self.players + self.werewolves + self.seer
        playersLeft.sort()
        irclib.sendChannelMessage( "Remaining players are: " + str( playersLeft ) )

    def didWerewolvesWin( self ):
        if( len( self.werewolves ) >= len( self.seer + self.players ) ):
            return True
        else:
            return False

    def reportWerewolfWin( self, irclib)
        irclib.sendChannelMessage("The werewolves change shape and overpower the remaining villagers! Werewolves win!")
        irclib.sendChannelMessage("Werewolf survivor(s): " + self.werewolves )
        if( len( self.seer ) > 0 ):
            irclib.sendChannelMessage("Seer (if alive): "  + self.seer )
        irclib.sendChannelMessage("Final villagers: " + self.players )
        self.endGame()

    def didPlayersWin( self ):
        if( len( self.werewolves ) == 0 ):
            return True
        else:
            return False

    def reportPlayerWin( self, irclib ):
        irclib.sendChannelMessage("You killed both werewolves! Villagers win!")
        if( len( self.seer ) > 0 ):
            irclib.sendChannelMessage("Seer (if alive): "  + self.seer )
        irclib.sendChannelMessage("Final villagers: " + self.players )
        self.endGame()
        

    def processNightPhase( self, irclib ):
        irclib.sendChannelMessage( "Night falls, and with it comes the baying of wolves!" )
        self.echoRemainingPlayers( irclib )
        self.seerHasAsked = False
        self.werewolfTarget["agreed"] = False
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
        elif:
            return False
            
    def beginDayPhase(self, irclib):
        self.gamePhase = "day"
        self.lynchTarget = {}
        if( self.werewolfTarget[ "agreed" ] in self.seer ):
            self.seer.remove( self.werewolfTarget[ "agreed" ] )
        else:
            self.players.remove( self.werewolfTarget[ "agreed" ] )
        irclib.sendChannelMessage( "Dawn breaks, and the villagers discover that the werewolves have eaten: " + self.werewolfTarget[ "agreed" ] + "." )
        if( self.didWerewolvesWin() ):
            self.reportWerewolfWin( irclib )
        else:
            irclib.sendChannelMessage( "Your soul cries out for vengeance! Type '!lynch <player name>' once you are sure who you want to lynch. Simple majority wins." )        
            self.echoRemainingPlayers(irclib)


    def processSeerNotice( self, irclib, source, message ):
        if( self.seerHasAsked ):
            irclib.sendPrivateNotice(source, "You can't ask twice in one night!")
        else:
            if( message[:len("dream ")] == "dream "):
                dreamTarget = message[len("dream "):]
                if( isSomeoneAPlayer( dreamTarget ) ):
                    self.seerHasAsked = True
                    if( isSomeoneAWerewolf( dreamTarget ) ):
                        irclib.sendPrivateNotice( source, "Yes, " + message[len("dream "):] + " is a werewolf.")
                    else:
                        irclib.sendPrivateNotice( source, "No, " + message[len("dream "):] + " is not a werewolf.")
                    if( self.werewolfTarget["agreed"] ):
                        self.beginDayPhase(irclib)
                    else:
                        irclib.sendPrivateNotice( source, "That's not a player!" )
            else:
                irclib.sendPrivateNotice( source, "Malformed request. Proper syntax is '/notice " +irclib.nickname + " dream <player name>" )

        
    def onNotice( self, irclib, source, message ):
        if( self.gamePhase == "night" and self.gameState == "playing"):
            if( message[ :len( "authenticate" ) ] == "authenticate" ):
                return False
            else:
                if( source.getName() in self.seer ):
                    self.processSeerNotice( irclib, source, message )
                elif( source.getName() == self.werewolves[0] and len( self.werewolves ) > 1):
                    if( message[:len("eat ")] == "eat " ):
                        if( message[len("eat "):] in ( self.players + self.seer ) ):
                            self.werewolfTarget[ 0 ] = message[len("eat "):]
                            if( self.werewolfTarget[ 0 ] == self.werewolfTarget[ 1 ] ):
                                self.werewolfTarget[ 2 ] = self.werewolfTarget[ 0 ]
                                irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 0 ] ), "Rah! You eat: " + str(self.werewolfTarget[ 2 ]) + "." )
                                irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 1 ] ), "Rah! You eat: " + str(self.werewolfTarget[ 2 ]) + "." )
                                if( self.seerHasAsked == True ):
                                    self.beginDayPhase(irclib)
                            else:
                                irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 1 ] ), "The other werewolf, " + self.werewolves[ 0 ] + ", has selected: " + str(self.werewolfTarget[ 0 ]) + ".")
                        elif( message[len("eat "):] in ( self.werewolves ) ):
                            irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 0 ] ), "You can't eat the other werewolf or yourself!" )
                        else:
                            irclib.sendPrivateNotice( source, "That's not a player!" )
                    else:
                        irclib.sendPrivateNotice( source, "Malformed request. Proper syntax is '/notice " + irclib.nickname + " eat <player name>" )
                    return True
                elif( source.getName() == self.werewolves[0] and len( self.werewolves ) == 1):
                    if( message[:len("eat ")] == "eat " and message[len("eat "):] in ( self.players + self.seer ) ):
                        self.werewolfTarget[ "agreed" ] = message[len("eat "):]
                        irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 0 ] ), "Rah! You eat: " + str(self.werewolfTarget[ 2 ]) + "." )
                        if( self.seerHasAsked == True ):
                                self.beginDayPhase(irclib)
                    else:
                        irclib.sendPrivateNotice( source, "That's not a player!" )
                    return True
                elif( len( self.werewolves) > 1 and source.getName() ==  self.werewolves[ 1 ] ):
                    if( message[:len("eat ")] == "eat " ):
                        if( message[len("eat "):] in ( self.players + self.seer ) ):
                            self.werewolfTarget[ 1 ] = message[len("eat "):]
                            if( self.werewolfTarget[ 0 ] == self.werewolfTarget[ 1 ] ):
                                self.werewolfTarget[ "agreed" ] = self.werewolfTarget[ 0 ]
                                irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 0 ] ), "Rah! You eat: " + str(self.werewolfTarget[ 2 ]) + "." )
                                irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 1 ] ), "Rah! You eat: " + str(self.werewolfTarget[ 2 ]) + "." )
                                if( self.seerHasAsked == True ):
                                    self.beginDayPhase(irclib)
                            else:
                                irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 0 ] ), "The other werewolf, " + self.werewolves[ 1 ] + ", has selected: " + str(self.werewolfTarget[ 1 ]) + ".")
                        if( message[len("eat "):] in ( self.werewolves ) ):
                            irclib.sendPrivateNotice( irclib.getUserList().findByName( self.werewolves[ 1 ] ), "You can't eat the other werewolf or yourself!" )
                        else:
                            irclib.sendPrivateNotice( source, "That's not a player!" )
                    else:
                        irclib.sendPrivateNotice( source, "Malformed request. Proper syntax is '/notice " + irclib.nickname + " eat <player name>" )
                    return True


    
    def initGame(self, irclib):
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
        self.gamePhase = "night"
        self.gameState = "playing"
        self.processNightPhase(irclib)

        

    def onChannelMessage(self, irclib, source, message):
        if( self.gameState == "playing" ):
            if( message == "players?" ):
                self.echoRemainingPlayers(irclib)

        if( self.gameState == "playing" and self.gamePhase == "day" ):
            if( message[:len("!lynch ")] == "!lynch " ):
                remainingPlayers = self.players + self.seer + self.werewolves
                self.lynchTarget[ source.getName() ] = message[len("!lynch "):]
                for i in self.lynchTarget:
                    if( self.lynchTarget.values().count( self.lynchTarget[ i ] ) > float( len( remainingPlayers ) ) / 2 ):
                        self.lynchTarget[ "final" ] = self.lynchTarget[ i ]
                        irclib.sendChannelMessage("You have decided to lynch " + self.lynchTarget[ "final" ] + "!")
                        if( self.lynchTarget[ "final" ] in self.players ):
                            self.players.remove( self.lynchTarget[ "final" ] )
                            irclib.sendChannelMessage("He or she was a villager. You paranoid gits!" )
                        elif( self.lynchTarget[ "final" ] in self.werewolves ):
                            self.werewolves.remove( self.lynchTarget[ "final"  ] )
                            irclib.sendChannelMessage("He or she was a werewolf. Good call!" )
                        elif( self.lynchTarget[ "final" ] in self.seer ):
                            self.seer.remove( self.lynchTarget[ "final" ] )
                            irclib.sendChannelMessage("That was the SEER! OMFG!")
                        if( didWerewolvesWin() ):
                            reportWerewolfWin( irclib )
                        elif( didPlayersWin() ):
                            reportPlayerWin( irclib )
                        else:
                            self.gamePhase = "night"
                            self.processNightPhase(irclib)
                        break
        
        if( self.gameState == "idle" ):
            if( message == "In Quas Corp Xen!" ):
                self.gameState = "adding"
                self.players.append( source.getName() )
                irclib.sendChannelMessage( "Beginning a game of werewolf. Type '!addme' to play, 'Por!' to begin the game." )

        
        
        if( self.gameState == "adding"):
            if( message == "!removeme" ):
                if( source.getName() in self.players):
                    self.players.remove( source.getName() )
                    irclib.sendChannelMessage("You've been removed, " + source.getName() + ".")
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
                    irclib.sendChannelMessage( "Adding you to the game, " + source.getName() + ".")
            if( message == "players?" ):
                irclib.sendChannelMessage( self.players )
            if( message == "Por!" ):
                if( len( self.players ) < 7 ):
                    irclib.sendChannelMessage("Fewer than the recommended amount of players. 'Ex!' to override." )
                else:
                    self.gameState = "playing"
                    self.initGame()
            if( message == "Ex!" ):
                if( len(self.players ) < 3 ):
                    irclib.sendChannelMessage("You can't even play a fake game with less than 3 players." )
                else:
                    self.gameState = "playing"
                    self.initGame(irclib)
                    irclib.sendPrivateMessage( irclib.getUserList().findByName( "Terralthra" ), "This is a test message. Werewolves: " + str( self.werewolves ) + ". Seer: " + str( self.seer ) )
        if( self.gameState != "idle" ):
            if( message == "An Quas Corp Xen!" ):
                irclib.sendChannelMessage("Game is over because it was manually aborted.")
                self.endGame()
