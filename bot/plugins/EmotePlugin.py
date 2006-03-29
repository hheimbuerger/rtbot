import re

class EmotePlugin:
  
  def __init__(self):
    self.emoticons = []
    file = open("resources/emoticons.csv", "r")
    lines = file.readlines()
    file.close()
    for a in lines:
      emotedef = a.strip().split("\",\"")
      self.emoticons.append(((emotedef[0])[1:], (emotedef[1])[:-1]))

  def getVersionInformation(self):
    return("$Id$")

  def listAll(self):
    for emote, desc in self.emoticons:
      print emote + " = " + desc

#  def getText(self, keyseq):
#    if(len(keyseq) < 2 or len(keyseq) > 3):
#      return("Invalid syntax! Try 'XX. (For example, 'gu or '1)")
#    try:
#      return("'" + keyseq[1:3].lower() + " = " + self.VCs[keyseq[1:3].lower()])
#    except KeyError:
#      return("unknown VC!")

#  def stripFromSpec(self, a):
#    result = ""
#    for letter in a.lower():
#      print letter
#      if(letter >= 'a' and letter <= 'z'):
#        result += letter

  def getEmote(self, text):
    theRE = ""
    for a in text.split():
      theRE += ".*?" + re.escape(a)
    #print theRE
    for emote, desc in self.emoticons:
      try:
        if(re.match(theRE, emote)):
          return(emote + " = " + desc)
      except:
        pass
    return("not found")

  def onPrivateMessage(self, irclib, source, msg):
      if((len(msg.split()) > 0) and (msg.split()[0] == "emote")):
          if(len(msg.split()) >= 2):
              irclib.sendPrivateMessage(source, self.getEmote(msg[6:]))

  def onChannelMessage(self, irclib, source, msg):
      if((len(msg.split()) > 0) and (msg.split()[0] == "emote")):
          if(len(msg.split()) >= 2):
              irclib.sendChannelMessage(self.getEmote(msg[6:]))



##def main():
##if(1 == 1):
#b = Emoticons()
#b.listAll()
#print "'GT = " + b.getText("'GT")
#print "'3 = " + b.getText("'3")
#print "' = " + b.getText("'")
#print "fdjsklf = " + b.getText("fdjsklf")
#print " = " + b.getText("")
##print b.stripFromSpec("Hey. what, do you?")
#vc = "'" + b.getVC("need more help")
#print vc + " = " + b.getText(vc)
#print
#print b.getEmote("@_@")
#print
#print b.getEmote("(@_@)")
#print
#print b.getEmote("O_o")
#print
#print b.getEmote("o_O")
#print
#print b.getEmote("o O")
#print
#print b.getEmote("@ @")
