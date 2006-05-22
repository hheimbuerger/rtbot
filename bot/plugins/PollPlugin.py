import datetime
import re

class PollPlugin:
    
    def __init__(self):
        #self.pluginInterfaceReference = pluginInterface
        self.currentPoll = None
        self.currentVotes = [0, 0, 0, 0, 0, 0]

    def getVersionInformation(self):
        return("$Id: PollPlugin.py 202 2006-03-25 23:14:16Z cortex $")
    
    def stripQuotes(self, source):
        if((source[0]=="'") and (source[-1]=="'")):
            return(source[1:-1])
        else:
            raise Exception("no quote!")
        
    def getRemainingSeconds(self):
        deltatime = datetime.datetime.now() - self.startTime
        return(self.currentPoll[2] - deltatime.seconds)

    def finishPoll(self, irclib):
        irclib.sendChannelMessage("The poll '%s' has finished. Results:" % (self.currentPoll[0]))
        i = 1
        for answer in self.currentPoll[1]:
            irclib.sendChannelMessage("%s, %i votes." % (answer, self.currentVotes[i]))
            i += 1
        self.currentPoll = None
        self.currentVotes = [0, 0, 0, 0, 0, 0]

    def printCurrentVote(self, irclib):
        if(self.currentPoll):
            (question, answers, timeout) = self.currentPoll
            irclib.sendChannelMessage("Poll: %s" % (question))
            for answerID in range(0, len(answers)):
                irclib.sendChannelMessage("#%i: %s" % (answerID+1, answers[answerID]))
            irclib.sendChannelMessage("Vote with '!vote <answer-id/>'")

    def onTimer(self, irclib):
        if(self.currentPoll):
            if(self.getRemainingSeconds() < 0):
                self.finishPoll(irclib)

    def onChannelMessage(self, irclib, source, message):
        if((len(message.split()) >= 1) and (message.split()[0] == "!poll")):
            if(self.currentPoll):
                irclib.sendChannelMessage("Sorry, there is already a poll running (%i seconds left)." % (self.getRemainingSeconds()))
                self.printCurrentVote(irclib)
            else:
                result = re.compile("!poll '(.*?)' (('.*?'\s){2,5})(\d{1,3})").match(message)      #
                if(result):
                    #print str(result)
                    question = result.group(1)
                    rawAnswers = result.group(2)
                    timeout = int(result.group(4))
                    #answers = map(self.stripQuotes, re.findall("'.*?'", rawAnswers))
                    answers = re.findall("'.*?'", rawAnswers)
                    #print "Question: %s" % (question)
                    #print "raw answers: %s" % (str(rawAnswers))
                    #print "Answers: %s" % (str(answers))
                    #print "Timeout: %i" % (timeout)
                    self.currentPoll = (question, answers, timeout)
                    self.printCurrentVote(irclib)
                    self.startTime = datetime.datetime.now()
                else:
                    irclib.sendChannelMessage("Syntax: !poll '<question/>' ['<answer/>'] <timeout in seconds/>")
        elif((len(message.split()) >= 2) and (message.split()[0] == "!vote")):
            try:
                voteID = int(message.split()[1])
                if(voteID >= 1 and voteID <= len(self.currentPoll[1])):
                    self.currentVotes[voteID] += 1
                    irclib.sendChannelMessage("Your vote has been counted, %s." % (source))
            except ValueError:
                pass





#Unit-test
if __name__ == "__main__":
    class IrcLibMock:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def sendChannelEmote(self, text):
            print "* %s" % (text)

    a = PollPlugin()
    a.onChannelMessage(IrcLibMock(), "me", "!poll 'Are you?' 'Yes' 'No' 'Dunno' 23")
    a.onChannelMessage(IrcLibMock(), "me", "!vote 1")
    a.onChannelMessage(IrcLibMock(), "me", "!vote 2")
    a.onChannelMessage(IrcLibMock(), "me", "!vote 3")
    a.onChannelMessage(IrcLibMock(), "me", "!vote 2")
    a.onChannelMessage(IrcLibMock(), "me", "!vote 2")
    a.onChannelMessage(IrcLibMock(), "me", "!vote 3")
    a.finishPoll(IrcLibMock())
    