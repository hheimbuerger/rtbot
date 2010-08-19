import string

class SpellCheckPlugin:

  closestword = ""
  lastld = 999
    
  def __init__(self):
    self.dictFile = "resources/dictionary.lst"

  def getVersionInformation(self):
    return("$Id$")
  
  def levenshtein_distance(self, first, second):
    """Find the Levenshtein distance between two strings."""
    if len(first) > len(second):
        first, second = second, first
    if len(second) == 0:
        return len(first)
    first_length = len(first) + 1
    second_length = len(second) + 1
    distance_matrix = [[0] * second_length for x in range(first_length)]
    for i in range(first_length):
       distance_matrix[i][0] = i
    for j in range(second_length):
       distance_matrix[0][j]=j
    for i in xrange(1, first_length):
        for j in range(1, second_length):
            deletion = distance_matrix[i-1][j] + 1
            insertion = distance_matrix[i][j-1] + 1
            substitution = distance_matrix[i-1][j-1]
            if first[i-1] != second[j-1]:
                substitution += 1
            distance_matrix[i][j] = min(insertion, deletion, substitution)
    return distance_matrix[first_length-1][second_length-1]
    
  def spellcheck(self, irclib, text):
    file = open(self.dictFile, "r")
    isWordFound = False
    input = string.lower(text)
    word = file.readline()
    while(word != ""):
      if(input == string.strip(word)):
        isWordFound = True
        break
      elif input[0] == word[0]:
#      else:
        ld = self.levenshtein_distance( input, word )
        if ( ld < self.lastld ):
          self.lastld = ld
          self.closestword = word
      word = file.readline()
    file.close()
    return(isWordFound)
   
  def onChannelMessage(self, irclib, source, msg):
      if((len(msg.split()) > 0) and (msg.split()[0] == "spellcheck")):
          if(len(msg.split()) >= 2):
              word = msg.split()[1]
              if(self.spellcheck(irclib, word)):
                  irclib.sendChannelMessage("Yes, '%s' is a word." % (word))
              else:
                  if ( self.lastld < 999 ):
                     irclib.sendChannelMessage("No, '%s' is not a word. Did you mean '%s'?" % (word, self.closestword))
                  else:
                     irclib.sendChannelMessage("No, '%s' is not a word." % (word))
 
              self.lastld = 999
              self.closestword = ""

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
