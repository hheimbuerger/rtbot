import datetime
import re
import itertools



class Poll:
    def __init__(self, question, listOfAnswers, timeout):
        self.question = question
        self.answers = listOfAnswers
        self.votes = {}
        self.timeout = timeout
        self.startTime = datetime.datetime.now()

    def getRemainingSeconds(self):
        deltatime = datetime.datetime.now() - self.startTime
        return(self.timeout - deltatime.seconds)
    
    def isTimeout(self):
        return(self.getRemainingSeconds() <= 0)
    
    def hasVoted(self, name):
        return(name in self.votes.keys())
    
    def vote(self, name, id):
        self.votes[name] = id
    
    def stripQuotes(self, source):
        if((source[0]=="'") and (source[-1]=="'")):
            return(source[1:-1])
        else:
            raise Exception("no quote!")

    def close(self, irclib):
        irclib.sendChannelMessage("The poll '%s' has finished. Results:" % (self.question))
        for answerID in range(1, len(self.answers)+1):
            # how many votes have the value 'i'?
            numVotes = sum(itertools.imap(lambda x: x==answerID, self.votes.values()))
            # send the channel message
            irclib.sendChannelMessage("%s, %i votes." % (self.answers[answerID-1], numVotes))

    def show(self, irclib):
        irclib.sendChannelMessage("Poll: %s" % (self.question))
        for answerID in range(1, len(self.answers)+1):
            irclib.sendChannelMessage("#%i: %s" % (answerID, self.answers[answerID-1]))
        irclib.sendChannelMessage("Vote with '!vote <answer-id/>'.")



class PollPlugin:
    
    def __init__(self):
        #self.pluginInterfaceReference = pluginInterface
        self.currentPoll = None

    def getVersionInformation(self):
        return("$Id: PollPlugin.py 202 2006-03-25 23:14:16Z cortex $")

    def onTimer(self, irclib):
        if(self.currentPoll and self.currentPoll.isTimeout()):
           self.currentPoll.close(irclib)
           self.currentPoll = None

    def onChannelMessage(self, irclib, source, message):
        if((len(message.split()) >= 1) and (message.split()[0] == "!poll")):
            if(self.currentPoll):
                irclib.sendChannelMessage("Sorry, there is already a poll running (%i seconds left)." % (self.currentPoll.getRemainingSeconds()))
                self.currentPoll.show(irclib)
            else:
                result = re.compile("!poll \"(.*?)\" ((\".*?\"\s){2,5})(\d{1,3})").match(message)      #
                if(result):
                    #print str(result)
                    question = result.group(1)
                    rawAnswers = result.group(2)
                    timeout = int(result.group(4))
                    #answers = map(self.stripQuotes, re.findall("'.*?'", rawAnswers))
                    answers = re.findall("\".*?\"", rawAnswers)
                    #print "Question: %s" % (question)
                    #print "raw answers: %s" % (str(rawAnswers))
                    #print "Answers: %s" % (str(answers))
                    #print "Timeout: %i" % (timeout)
                    self.currentPoll = Poll(question, answers, timeout)
                    self.currentPoll.show(irclib)
                else:
                    irclib.sendChannelMessage("Syntax: !poll \"<question/>\" [\"<answer/>\"] <timeout in seconds/>")
        elif((len(message.split()) >= 2) and (message.split()[0] == "!vote")):
            if(self.currentPoll):
                try:
                    voteID = int(message.split()[1])
                    if(source.isAuthed()):
                        if(voteID >= 1 and voteID <= len(self.currentPoll.answers)):
                            name = source.dataStore.getAttribute("authedAs")
                            if(self.currentPoll.hasVoted(name)):
                                irclib.sendChannelMessage("Your vote has been changed, %s." % (name))
                            else:
                                irclib.sendChannelMessage("Your vote has been counted, %s." % (name))
                            self.currentPoll.vote(name, voteID)
                        else:
                            irclib.sendChannelMessage("That vote-id is invalid, %s." % (source.nick))
                    else:
                        irclib.sendChannelMessage("Only authenticated users are allowed to vote, %s." % (source.nick))
                except ValueError:
                    irclib.sendChannelMessage("That vote-id is invalid, %s." % (source.nick))





#Unit-test
if __name__ == "__main__":
    class DataStoreMock:
        def getAttribute(self, attribute):
            if(attribute == "authedAs"):
                return("test1")
            else:
                raise Exception("asked for wrong attribute")
    
    class IrcUserMock:
        def __init__(self):
            self.dataStore = DataStoreMock()
        def isAuthed(self):
            return(True)
    
    class IrcLibMock:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def sendChannelEmote(self, text):
            print "* %s" % (text)

    a = PollPlugin()
    a.onChannelMessage(IrcLibMock(), IrcUserMock(), '!poll "Are you?" "Yes" "No" "Dunno" 3')
    a.onChannelMessage(IrcLibMock(), IrcUserMock(), '!poll "Are you?" "Yes" "No" "Dunno" 3')
    a.onChannelMessage(IrcLibMock(), IrcUserMock(), "!vote 1")
    a.onChannelMessage(IrcLibMock(), IrcUserMock(), "!vote 2")
    a.onChannelMessage(IrcLibMock(), IrcUserMock(), "!vote 3")
    import time
    time.sleep(3)
    a.onTimer(IrcLibMock())
