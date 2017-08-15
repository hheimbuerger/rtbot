import random

class WarWisdomPlugin:
  wisdoms = []

  def __init__(self):
    file = open("resources/warwisdom.txt", "r")
    lines = file.readlines()
    file.close()
    for a in lines:
      self.wisdoms.append(a.strip())

  def getVersionInformation(self):
    return("$Id$")

  def giveWisdom(self, irclib):
    selected_wisdom = self.wisdoms[int(random.random() * len(self.wisdoms))]
    irclib.sendChannelMessage(selected_wisdom)

  def onChannelMessage(self, irclib, sender, message):
    if(message == "wisdom"):
      self.giveWisdom(irclib)




if __name__ == "__main__":
  pass