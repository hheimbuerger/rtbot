import random, logging

class WerewolfModeratorPlugin:

    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface

    def getVersionInformation(self):
        return("$Id: WerewolfModeratorPlugin.py 315 2007-06-05 15:24:26Z terralthra $")

    players = []
    gameState = "idle"

    def endGame(self, reason):
        self.gameState = "idle"
        players = []
        self.onChannelMessage("Game aborted.")
            
    
    def initGame(self):
        #add all players
        #randomly  pick 2 werewolves and seer
        #inform werewolves of each other's identity
        #explain rule macro
        #return

    def onChannelMessage(self, irclib, source, message):
        #if self.gameState = "playing"
            #if night phase
            #while werewolf1.target != werewolf2.target
                #message werewolves and await target
                #pass target back to other werewolf
                #if they agree, kill target
            #ask seer for divination target, respond
            #check for win by werewolves, set phase to day

            #if phase = day

            #inform village who is dead
            #while lynch votes not in consensus
                #accept votes for lynching in channel
            #kill lynching target
            #check for win by werewolves, win by villagers, set phase to night

        #if gameState = "idle"
            #check for someone starting a game, set gamestate to adding, add them to player list
        if( self.gameState = "idle" ):
            if( message == "In Quas Corp Xen!" ):
                self.gameState = "adding"
                self.players.append( source.getName() )
                irclib.sendChannelMessage( "Beginning a game of werewolf. Type !addme to play." )
        
        
        if( self.gameState == "adding"):
            if( message = "!addme" ):
                dontAddMe = False
                for i in self.players:
                    if (source == i):
                        irclib.sendChannelMessage( "You are already playing," + source )
                        dontAddMe = True
                if( source.isAuthed() == False ):
                    irclib.sendChannelMessage( "You must be authed to play," + source )
                    dontAddMe = True
                if( dontAddMe == False ):
                    self.players.append( source.getName() )
            #if a player says start the game
                #check for >= 7 players
                #if yes
                    #start the game
                #if no
                    #report fewer than 7, allow override to start game anyway
        if( self.gameState != "idle" ):
            if( message = "An Quas Corp Xen!" ):
                self.endGame()
                
        
