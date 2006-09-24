import re, logging, math
from modules import PluginInterface

class HighLowSolverPlugin:
    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface

    def getVersionInformation(self):
	return("$Id: HighLowSolverPlugin.py 1 2006-09-23 15:24:26Z Terralthra $")

    @PluginInterface.Priorities.prioritized(PluginInterface.Priorities.PRIORITY_LOW)

    int ceiling = 1
    int floor = 1
    int guess = 1
    bool isPlaying = False

    def computeGuess(self, ceiling, floor)
        return( ((ceiling - floor)/2) + floor)
    

    def onChannelMessage(self, irclib, source, msg):
        reResult = re.compile("hl\son\s(\d+)").search(msg.lower())
	if(reResult):
            isPlaying = True
            irclib.sendChannelMessage("I've got this one.")
            ceiling = reResult.groups()[0]
            guess = self.ComputeGuess(ceiling, floor)
            irclib.sendChannelMessage("num %s", guess)
        if(isPlaying):
            if(msg.lower()[:len(5)] == irclib.nickname + "> "):
                reResult2 = re.compile("([^>]+)\> (HIGHER)|(LOWER)").search(msg.lower())
                if(reResult2.groups()[1]):
                    floor = guess
                elif(reResult2.groups()[2]:
                     ceiling = guess
                guess = self.computeGuess(ceiling, floor)
                irclib.sendChannelMessage("num %s", guess)
            if(msg.lower() == irclib.nickname + "just won the Higher/Lower game! The Higher/Lower game has just been auto-disabled."):
                irclib.sendChannelMessage("pwnt.")
                isPlaying = false
                int ceiling, floor, guess = 1


    
            

