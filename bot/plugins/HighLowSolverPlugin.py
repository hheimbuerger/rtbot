import re, logging, math
from modules import PluginInterface

class HighLowSolverPlugin:
    def __init__(self, pluginInterface):
        self.pluginInterfaceReference = pluginInterface

    def getVersionInformation(self):
	return("$Id: HighLowSolverPlugin.py 1 2006-09-23 15:24:26Z Terralthra $")

    self.ceiling = 1
    self.floor = 1
    self.guess = 1
    self.isPlaying = False

    def computeGuess(self):
	self.guess = (((self.ceiling - self.floor)/2) + self.floor)
	

    def onChannelMessage(self, irclib, source, msg):
        reResult = re.compile("hl\son\s(\d+)").search(msg.lower())
        if(reResult):
            isPlaying = True
            irclib.sendChannelMessage("I've got this one.")
            self.ceiling = reResult.groups()[0]
            self.computeGuess()
	    irclib.sendChannelMessage("num %s", guess)
	if(isPlaying):
	    if(msg.lower()[:len(5)] == irclib.nickname + "> "):
		reResult2 = re.compile("([^>]+)\> (HIGHER)|(LOWER)").search(msg.lower())
		if(reResult2.groups()[1]):
		    self.floor = self.guess
		elif(reResult2.groups()[2]):
		    self.ceiling = self.guess
		    self.computeGuess()
		    irclib.sendChannelMessage("num %s", guess)
		elif(msg.lower() == irclib.nickname + "just won the Higher/Lower game! The Higher/Lower game has just been auto-disabled."):
		    irclib.sendChannelMessage("pwnt.")
		    self.isPlaying = false
		    self.ceiling = self.floor = self.guess = 1


	
			

