from modules import LogLib
import random

class AllegTacToePlugin:

    def getVersionInformation(self):
        return("$Id$")

    def __init__(self):
        self.games = {}

    def onChannelMessage(self, irclib, source, msg):
      if((msg == "play") or (msg == "play novice")):
          LogLib.log.add(False, "play")
          if((len(msg.split()) >= 2) and (msg.split()[1] == "novice")):
            irclib.sendChannelMessage("Okay, here we go (easy mode):")
            self.games[source] = AllegTacToeGame(False)
          else:
            irclib.sendChannelMessage("Okay, here we go (expert mode):")
            self.games[source] = AllegTacToeGame(True)
          #LogLib.log.add(False, "board:" + string.join(self.games[source].showBoard(), "\n"))
          for line in self.games[source].showBoard():
              irclib.sendChannelMessage(line)
      elif(source in self.games):
          LogLib.log.add(False, "move")
          (isValid, error) = self.games[source].isValidMove(msg)
          if(isValid):
              LogLib.log.add(False, "valid move")
              res = self.games[source].nextTurn(int(msg))
              LogLib.log.add(False, "next board")
              for line in self.games[source].showBoard():
                  irclib.sendChannelMessage(line)
              if(res != ""):
                  irclib.sendChannelMessage(res)
                  del self.games[source]
          else:
              if(error != ""):
                irclib.sendChannelMessage(error)


class AllegTacToeGame:
      E = "O"
      R = "R"
      T = "T"
      winConfigurations = [ #outer border
                            (0,1,7), (1,7,12), (7,12,11), (12,11,5), (11,5,0), (5,0,1),
                            #mid-high
                            (5,2,3), (2,3,4), (3,4,7),
                            #mid-low
                            (5,8,9), (8,9,10), (9,10,7),
                            #middle
                            (3,6,9) ]
      bitchingPhrases = ["You are so going to lose!",
                         "You suck so bad it takes the joy out of winning!",
                         "My momma could beat you and she's written in basic!"]
      finalWinConfig = None
      currentMessage = None
    
      def __init__(self, isExpertMode = False):
        self.board = [self.E, self.E, self.E, self.E, self.E, self.E, self.E, self.E, self.E, self.E, self.E, self.E, self.E]
        self.isExpertMode = isExpertMode
        if(self.isExpertMode):
          self.board[5 + 2*int(random.random() * 2)] = self.T
        else:
          self.doComputerTurn()
    
      def showSector(self, field):
        if(self.finalWinConfig == None):
          return(self.board[field])
        else:
          if(field in self.finalWinConfig):
            return("\x0304" + self.board[field] + "\x0310")
          else:
            return(self.board[field])
    
      def showBoard(self):
        output = []
        if(self.currentMessage != None):
          output.append(self.currentMessage)
        output.append("   -" + self.showSector(0) + "-------" + self.showSector(1) + "-   ")
        output.append("  / |       | \  ")
        output.append(" /  " + self.showSector(2) + "---" + self.showSector(3) + "---" + self.showSector(4) + "  \ ")
        output.append("| /     |     \ |")
        output.append(self.showSector(5) + "       " + self.showSector(6) + "       " + self.showSector(7))
        output.append("| \     |     / |")
        output.append(" \  " + self.showSector(8) + "---" + self.showSector(9) + "---" + self.showSector(10) + "  / ")
        output.append("  \ |       | /  ")
        output.append("   -" + self.showSector(11) + "-------" + self.showSector(12) + "-   ")
        return(output)
    
      def isDraw(self):
        numStones = 0
        for field in range(0, 13):
          if(self.board[field] != self.E):
            numStones += 1
        return(numStones == 13)
    
      def isPossibleDraw(self):
        lastEmptyField = -1
        numStones = 0
        for field in range(0, 13):
          if(self.board[field] == self.E):
            lastEmptyField = field
          else:
            numStones += 1
        if(numStones == 12):
          self.board[lastEmptyField] = self.R
          return(True)
        else:
          return(False)
    
      def nextTurn(self, nr):
        self.currentMessage = None
        self.board[nr] = self.R
        if(self.checkIfWon()):
            return("gg. 'ym, you won!")
        self.doComputerTurn()
        if(self.checkIfWon()):
            return("gg. '4, I won this round!")
        if(self.isDraw()):
            return("gg. This is a draw!")
        return("")
    
      def isValidMove(self, move):
        try:
          m = int(move)
          if((m <= 12) and (m >= 0)):
            if(self.board[m] == self.E):
              return((True, ""))
            else:
              return((False, "That field is not empty!"))
          else:
            return((False, ""))
        except:
          return((False, ""))
    
      def fieldIsEmpty(self, field):
        return(self.board[field] == self.E)
    
      def findWinMoves(self, goodMoves):
        lastEmptyField = 0
        for winConfig in self.winConfigurations:
          emptyCount = 0
          computerCount = 0
          for field in winConfig:
            if(self.board[field] == self.E):
              emptyCount += 1
              lastEmptyField = field
            if(self.board[field] == self.T):
              computerCount += 1
          if((computerCount == 2) and (emptyCount == 1)):
            goodMoves.append(lastEmptyField)
    
      def findBlockingMoves(self, goodMoves):
        lastEmptyField = 0
        for winConfig in self.winConfigurations:
          emptyCount = 0
          playerCount = 0
          for field in winConfig:
            if(self.board[field] == self.E):
              emptyCount += 1
              lastEmptyField = field
            if(self.board[field] == self.R):
              playerCount += 1
          if((playerCount == 2) and (emptyCount == 1)):
            goodMoves.append(lastEmptyField)
    
      def getNumberOfPossibleWinConfigs(self, possibleNextMove):
        num = 0
        for winConfig in self.winConfigurations:
          isNextMoveIn = False
          isOneFieldAlreadyTaken = False
          isOneFieldStillFree = False
          for currentField in winConfig:
            if(currentField == possibleNextMove):
              isNextMoveIn = True
            elif(self.board[currentField] == self.T):
              if(isOneFieldAlreadyTaken):
                continue
              isOneFieldAlreadyTaken = True
            elif(self.board[currentField] == self.E):
              if(isOneFieldStillFree):
                continue
              isOneFieldStillFree = True
          if(isNextMoveIn and isOneFieldAlreadyTaken and isOneFieldStillFree):
            num += 1
        return(num)
    #        if((currentField == possibleNextMove) or ):
    #          numPossiblyOwnedFields += 1
    #        else:
    #          lastField = currentField
    #      if(numPossiblyOwnedFields == 2):
    #        if(self.board[lastField] == self.E):
    #          num += 1
    #        if((field1 in winConfig) and (field2 in winConfig)):
    #          for testfield in winConfig:
    #            if((testfield != field1) and (testfield != field2)):
    #              field3 = testfield
    #          if(self.board[field3] == self.E):
    #            num += 1
    
      def findCreateDoubleWindmillMoves(self, goodMoves):
        for possibleNextMove in range(0, 13):
          if(self.board[possibleNextMove] == self.E):
            if(self.getNumberOfPossibleWinConfigs(possibleNextMove) >= 2):
              goodMoves.append(possibleNextMove)
    
      def findRandomMove(self, goodMoves):
        pos = 0
        for i in range(0, int(random.random() * 13)):
          pos += 1
          if(pos > 12): pos = 0
          while(not self.fieldIsEmpty(pos)):
            pos = pos + 1
            if(pos > 12): pos = 0
        goodMoves.append(pos)
    
      def doComputerTurn(self):
        goodMoves = []
        self.findWinMoves(goodMoves)
        if(len(goodMoves) == 0):
          self.findBlockingMoves(goodMoves)
          if(len(goodMoves) != 0):
            self.currentMessage = "STACK!"
        if(self.isExpertMode):
          if(len(goodMoves) == 0):
            self.findCreateDoubleWindmillMoves(goodMoves)
            if(len(goodMoves) != 0):
              self.currentMessage = self.bitchingPhrases[int(random.random() * len(self.bitchingPhrases))]
        if(len(goodMoves) == 0):
          self.findRandomMove(goodMoves)
        self.board[goodMoves[int(random.random() * len(goodMoves))]] = self.T
    
      def checkIfWon(self):
        for winConfig in self.winConfigurations:
          if(self.board[winConfig[0]] == self.board[winConfig[1]] == self.board[winConfig[2]]):
            if(self.board[winConfig[0]] != self.E):
              self.finalWinConfig = winConfig
              return(True)
        return(False)







if __name__ == "__main__":
    b = AllegTacToe()
    for line in b.showBoard():
      print line
    while(True):
      s = ""
      while(not b.isValidMove(s)[0]):
        s = raw_input("Your move?: ")
      res = b.nextTurn(int(s))
      if(res != ""):
        for line in b.showBoard():
          print line
        print res
        for line in b.showBoard():
          print line
        break
      for line in b.showBoard():
        print line

