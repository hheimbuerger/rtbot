import re, random

class DieRollingPlugin:

    def getVersionInformation(self):
        return("$Id$")

    def rollDie(self, irclib, dieDesc):
        die = Die(dieDesc)
        if(die.isValid()):
	  if(die.num_surfaces == 1):
		irclib.sendChannelEmote("rolls " + dieDesc + "...")
		irclib.sendChannelMessage("It rolls... and rolls... aww, I can't find it anymore. Damn marbles.")
	  else:
		irclib.sendChannelEmote("rolls " + dieDesc + "...")
		irclib.sendChannelMessage("It rolls... and rolls... now it stopped -- it comes up \x0304" + str(die.roll()) + "\x0310!")
        else:
          irclib.sendChannelMessage("Sorry, I don't know that die...")

    def rollFromList(self, irclib, listString):
        alternatives = listString.split(", ")
        irclib.sendChannelEmote("rolls a d%i..." % (len(alternatives)))
        resultId = int(random.random()*len(alternatives))
        resultText = alternatives[resultId]
        irclib.sendChannelMessage("It rolls... and rolls... now it stopped -- it comes up \x0304%s\x0310! %s is the one!" % (resultId+1, resultText))

    def flipCoin(self, irclib):
        irclib.sendChannelEmote("flips a coin...")
        if(int(random.random() * 2) == 0):
          irclib.sendChannelMessage("It flies... and flies... got it! -- \x0304heads\x0310!")
        else:
          irclib.sendChannelMessage("It flies... and flies... got it! -- \x0304tails\x0310!")

    def onChannelMessage(self, irclib, source, msg):
        if((len(msg.split()) > 0) and (msg.split()[0] == "roll")):
            if(len(msg.split()) >= 2):
                self.rollDie(irclib, msg.split()[1])
        if((len(msg.split()) >= 2) and (msg.split()[0] == "rollfrom")):            
            self.rollFromList(irclib, msg.split(" ", 1)[1])
        if(msg == "flip"):
            self.flipCoin(irclib)
            

class Die:
      valid = False
      num_dice = 0
      num_surfaces = 0
      num_rolls = 0
      isOpenEnded = False
    
      def __init__(self, input):
        try:
          result_re = re.match("^((\d{1,2})([xo]))?(\d{1,4})?d(\d{1,4})(oe)?$", input)
    #      if(len(result_re.group(1)) > 4):
    #        raise Exception()
    #      if(len(result_re.group(2)) > 4):
    #        raise Exception()
    #      print result_re.group(1)
          if(result_re.group(1) == None):
            self.num_rolls = 1
          else:
    #        print result_re.group(2)
            self.num_rolls = int(result_re.group(2))
            if(result_re.group(3) == "o"):
              self.isOpenEnded = True
          if(self.num_rolls > 15):
            raise Exception()
          if(result_re.group(4) == None):
            self.num_dice = 1
          else:
            self.num_dice = int(result_re.group(4))
          self.num_surfaces = int(result_re.group(5))
          #print "rolls: " + str(self.num_rolls)
          #print "dice: " + str(self.num_dice)
          #print "surfaces: " + str(self.num_surfaces)
          if(not (self.num_rolls > 0)):
            raise Exception()
          if(not (self.num_dice > 0)):
            raise Exception()
          if(not (self.num_surfaces > 0)):
            raise Exception()
          self.valid = True
          #print "valid die"
        except:
          self.valid = False
          #print "invalid die"
    
      def isValid(self):
        return(self.valid)
    
      def rollOneRound(self):
        sum = 0
        for i in range(0, self.num_dice):
          sum += int(random.random() * self.num_surfaces) + 1
        return(sum)
    
      def rollOneRoundWithOpenEndedPossibility(self):
        temp = ""
        value = self.rollOneRound()
        temp += str(value)
        if(self.isOpenEnded):
          count_rerolls = 0
          while((value == self.num_dice * self.num_surfaces) and (count_rerolls<20)):
            temp += "+"
            value = self.rollOneRound()
            temp += str(value)
            count_rerolls += 1
          if(count_rerolls >= 20):
            temp += "+..."
        return(temp)
    
      def roll(self):
        if(not self.isValid()):
          return(-1)
        if(self.num_rolls == 1):
          return(self.rollOneRoundWithOpenEndedPossibility())
        else:
          result = []
          for i in range(0, self.num_rolls):
            temp = self.rollOneRoundWithOpenEndedPossibility()
            result.append(temp)
          return(", ".join(result))



if __name__ == "__main__":
    class IrcLibMock:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def sendChannelEmote(self, text):
            print "* %s" % (text)

#    print Die("1d1").roll()
#    print Die("2d6").roll()
#    print Die("d6").roll()
#    print Die("20xd6").roll()
#    print Die("20od6").roll()
    for i in range(0,20):
      print Die("1od6").roll()
    DieRollingPlugin().onChannelMessage(IrcLibMock(), "source", "rollfrom DN, EoR, PC2, GoD2, A+, Star Wars")