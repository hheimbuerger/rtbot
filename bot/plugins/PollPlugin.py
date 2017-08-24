import datetime
import re

from plugin_base import BasePlugin


class Poll:
    def __init__(self, channel, question, listOfAnswers, timeout):
        self.channel = channel
        self.question = question
        self.answers = listOfAnswers
        self.votes = {}
        self.timeout = timeout
        self.startTime = datetime.datetime.now()

    def getRemainingSeconds(self):
        deltatime = datetime.datetime.now() - self.startTime
        return self.timeout - deltatime.seconds

    def isTimeout(self):
        return self.getRemainingSeconds() <= 0

    def hasVoted(self, user):
        return user in self.votes

    def vote(self, user, id):
        self.votes[user] = id

    async def close(self):
        await self.channel.reply("The poll '%s' has finished. Results:" % (self.question))
        for answerID in range(1, len(self.answers)+1):
            # how many votes have the value 'i'?
            numVotes = sum(map(lambda x: x == answerID, self.votes.values()))
            # send the self.channel message
            await self.channel.reply("%s, %i votes." % (self.answers[answerID-1], numVotes))

    async def show(self):
        await self.channel.reply("Poll: %s" % (self.question))
        for answerID in range(1, len(self.answers)+1):
            await self.channel.reply("#%i: %s" % (answerID, self.answers[answerID-1]))
        await self.channel.reply("Vote with '!vote <answer-id/>'.")


class PollPlugin(BasePlugin):

    def __init__(self):
        self.currentPoll = None

    async def on_timer(self):
        if self.currentPoll and self.currentPoll.isTimeout():
            await self.currentPoll.close()
            self.currentPoll = None

    async def on_message(self, channel, user, message):
        if len(message.split()) >= 1 and message.split()[0] == "!poll":
            if self.currentPoll:
                await channel.reply("Sorry, there is already a poll running (%i seconds left)." % (self.currentPoll.getRemainingSeconds()))
                await self.currentPoll.show()
            else:
                result = re.compile("!poll \"(.*?)\" ((\".*?\"\s){2,5})(\d{1,3})").match(message)      #
                if result:
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
                    self.currentPoll = Poll(channel, question, answers, timeout)
                    await self.currentPoll.show()
                else:
                    await channel.reply("Syntax: !poll \"<question/>\" [\"<answer/>\"] <timeout in seconds/>")

        elif message.startswith('!vote') and len(message.split()) >= 2:
            if self.currentPoll:
                try:
                    voteID = int(message.split()[1])
                    if 1 <= voteID <= len(self.currentPoll.answers):
                        if self.currentPoll.hasVoted(user):
                            await channel.reply("Your vote has been changed, %s." % user)
                        else:
                            await channel.reply("Your vote has been counted, %s." % user)
                        self.currentPoll.vote(user, voteID)
                    else:
                        await channel.reply("That vote-id is invalid, %s." % user)
                except ValueError:
                    await channel.reply("That vote-id is invalid, %s." % user)
