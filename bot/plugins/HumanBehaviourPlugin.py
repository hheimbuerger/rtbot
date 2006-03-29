import re
from modules import LogLib
from modules import PluginInterface

class HumanBehaviourPlugin:

  def __init__(self, pluginInterface):
	self.saidMyNameLastMessage = {}
	self.pluginInterfaceReference = pluginInterface

  def getVersionInformation(self):
	return("$Id$")
    
  @classmethod
  def getDependencies(self):
      return(["AuthenticationPlugin", "InsultPlugin"])

  def getCanonicalName(self, rawName):
	# retrieve AuthenticationPlugin
	authenticationPlugin = self.pluginInterfaceReference.getPluginByClassname("AuthenticationPlugin")
	if(authenticationPlugin == None):
	  LogLib.log.add(LogLib.LOGLVL_INFO, "ERROR: HumanBehaviourPlugin didn't succeed at lookup of AuthenticationPlugin during execution of getCanonicalName()")
	  return(rawName)
	else:
	  return(authenticationPlugin.getCanonicalName(rawName))

  def insult(self, irclib, name):
	# retrieve InsultPlugin
	insultPlugin = self.pluginInterfaceReference.getPluginByClassname("InsultPlugin")
	if(insultPlugin == None):
	  LogLib.log.add(LogLib.LOGLVL_INFO, "ERROR: HumanBehaviourPlugin didn't succeed at lookup of InsultPlugin during execution of insult()")
	  pass
	else:
	  insultPlugin.insult(irclib, name)

  def removeURLs(self, text):
	reResult = re.compile("(.*?)http://(\\S*)(.*)").match(text)
	if(reResult):
	  return(self.removeURLs(reResult.groups()[0] + reResult.groups()[2]))
	else:
	  return(text)

  def onPrivateMessage(self, irclib, source, msg):
	if((len(msg.split()) > 0) and (msg.split()[0] == "say")):
		irclib.sendChannelMessage(msg[4:])
	elif((len(msg.split()) > 0) and (msg.split()[0] == "me")):
		irclib.sendChannelEmote(msg[3:])

  @PluginInterface.Priorities.prioritized(PluginInterface.Priorities.PRIORITY_LOW)
  def onChannelMessage(self, irclib, source, msg):
	#print self.saidMyNameLastMessage
	if(source in self.saidMyNameLastMessage):
	  temp = True
	  del self.saidMyNameLastMessage[source]
	else:
	  temp = False
	if((temp == True) and (msg == "'2" or msg == "`2" or msg.lower().find("i didn't")!=-1)):
		self.insult(irclib, self.getCanonicalName(source))
	elif((temp == True) and (msg == "'1" or msg == "`1" or msg.lower().find("yes")!=-1 or msg.lower().find("ya")!=-1 or msg.lower().find("yup")!=-1 or msg.lower().find("yep")!=-1 or msg.lower().find("yeah")!=-1 or msg.lower().find("i did")!=-1)):
		irclib.sendChannelMessage(":)")
	elif((temp == True) and (msg.lower().find("no")!=-1 or msg.lower().find("nah")!=-1)):
		self.insult(irclib, self.getCanonicalName(source))
	elif((temp == True) and (msg.lower().find("naturally")!=-1 or msg.lower().find("of course")!=-1)):
		irclib.sendChannelMessage(":)")
	elif(msg.lower() == "'yt" or msg.lower() == "`yt"):
		irclib.sendChannelMessage("'rt")
	elif(msg.lower() == "'yb" or msg.lower() == "`yb"):
		irclib.sendChannelMessage("'yb")
	elif(msg.lower() == "'yr" or msg.lower() == "`yr"):
		irclib.sendChannelMessage("See ya, " + self.getCanonicalName(source) + "!")
	elif(msg.lower() == "'ym" or msg.lower() == "`ym"):
		irclib.sendChannelMessage("'yt")
	elif(msg.lower() == "'gl" or msg.lower() == "`gl"):
		irclib.sendChannelMessage("'gc")
	elif(msg.lower() == "'go" or msg.lower() == "`go"):
		irclib.sendChannelMessage("Sleep well, " + source + "!")
	elif(msg.lower() == "'ac" or msg.lower() == "`ac"):
		irclib.sendChannelMessage("Ram it! Ram it! RAM IT!!!")
	elif(msg.lower() == "'gn" or msg.lower() == "`gn"):
		irclib.sendChannelMessage("Read the Academy, you n00b!")
	elif(self.removeURLs(msg).lower().find("rtbot") != -1):
		if((msg.lower().find("'yh") != -1) or (msg.lower().find("sup") != -1)):
			irclib.sendChannelMessage("'yh! I'm fine. How about you?")
		else:
			irclib.sendChannelMessage("Hey " + self.getCanonicalName(source) + ", did you just say my name?")
			self.saidMyNameLastMessage[source] = True
#		elif(self.getCanonicalName(source).lower().find("denga") != -1):
#			irclib.sendChannelEmote("closes his eyes and sings: bla bla bla, bla blaaaaa")




if __name__ == "__main__":
  pass