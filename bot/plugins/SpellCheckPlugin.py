import string

class SpellCheckPlugin:
  
  def __init__(self):
    self.dictFile = "resources/dictionary.lst"

  def getVersionInformation(self):
    return("$Id$")

  def spellcheck(self, text):
    file = open(self.dictFile, "r")
    isWordFound = False
    input = string.lower(text)
    word = file.readline()
    while(word != ""):
      if(input == string.strip(word)):
        isWordFound = True
        break
      word = file.readline()
    file.close()
    return(isWordFound)

  def onChannelMessage(self, irclib, source, msg):
      if((len(msg.split()) > 0) and (msg.split()[0] == "spellcheck")):
          if(len(msg.split()) >= 2):
              word = msg.split()[1]
              if(self.spellcheck(word)):
                  irclib.sendChannelMessage("Yes, '%s' is a word." % (word))
              else:
                  irclib.sendChannelMessage("No, '%s' is not a word." % (word))


#Unit-test
if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text

    a = SpellCheckPlugin()
    a.onChannelMessage(FakeIrcLib(), "source", "spellcheck manoeuvrer")
    print "==============="
    a.onChannelMessage(FakeIrcLib(), "source", "spellcheck manoeuver")
