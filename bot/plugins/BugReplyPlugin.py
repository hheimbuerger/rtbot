import random, logging

class BugReplyPlugin:
  replies = []
  
  def __init__(self, pluginInterface):
    self.pluginInterfaceReference = pluginInterface

    file = open("resources/bug_replies.txt", "r")
    lines = file.readlines()
    file.close()
    for a in lines:
      self.replies.append(a.strip())

  def getCanonicalName(self, rawName):
    # retrieve AuthenticationPlugin
    authenticationPlugin = self.pluginInterfaceReference.getPlugin("AuthenticationPlugin")
    if(authenticationPlugin == None):
      logging.info("ERROR: HumanBehaviourPlugin didn't succeed at lookup of AuthenticationPlugin during execution of getCanonicalName()")
      return(rawName)
    else:
      return(authenticationPlugin.getCanonicalName(rawName))

  def getVersionInformation(self):
    return("$Id$")

  def listAll(self):
    for reply in self.replies:
      print reply

  def reply(self, irclib, name):
    irclib.sendChannelMessage(self.getReply(name))

  def onChannelMessage(self, irclib, sender, message):
    if((message == "!bug") or ((len(message.split()) >= 2) and (message.split()[0] == "!bug"))):
      self.reply(irclib, sender)

  def getReply(self, name):
    selected_reply = self.replies[int(random.random() * len(self.replies))]
    return(self.getCanonicalName(name) + ", " + selected_reply)

if __name__ == "__main__":
  replies = BugReplyPlugin()
  replies.listAll()
  print
  print replies.getReply("Person A")
  print replies.getReply("Person B")
  print replies.getReply("Person C")
