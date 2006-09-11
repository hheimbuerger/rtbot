import random, logging

class InsultPlugin:
  insults = []
  
  def __init__(self, pluginInterface):
    self.pluginInterfaceReference = pluginInterface

    file = open("resources/insults.txt", "r")
    lines = file.readlines()
    file.close()
    for a in lines:
      self.insults.append(a.strip())

  def getVersionInformation(self):
    return("$Id$")

  def listAll(self):
    for insult in self.insults:
      print insult

  def getInsult(self, nick):
    selected_insult = self.insults[int(random.random() * len(self.insults))]
    return(nick + ", I have one thing to tell you: " + selected_insult)

  def insult(self, irclib, name):
    irclib.sendChannelMessage(self.getInsult(name))

  def onChannelMessage(self, irclib, sender, message):
    if((len(message.split()) >= 2) and (message.split()[0] == "insult")):
      name = message[7:]
      if(name.lower().find("bot") != -1):
          self.insult(irclib, sender.getCanonicalNick())
          sender.dataStore.setAttribute("isPunished", True)
      else:
          self.insult(irclib, name)



if __name__ == "__main__":
  insults = Insults()
  insults.listAll()
  print
  print insults.getInsult("Person A")
  print insults.getInsult("Person B")
  print insults.getInsult("Person C")
