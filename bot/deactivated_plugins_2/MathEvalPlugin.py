from __future__ import division
from math import *
import re, itertools

class MathEvalPlugin:

    latestResult = None

    def getVersionInformation(self):
        return("$Id$")

    def handleMessage(self, msg, _, replyMessage, replyEmote):
        # _ is the latest result eval returned. Returns "None"
        if((len(msg.split()) > 1) and ((msg.split()[0] == "eval") or (msg.split()[0] == "evalstatement"))):
            try:
                exp = msg.split(None, 1)[1]
                if(len(re.findall("\*\*", exp)) + len(re.findall("pow", exp)) > 1):
                    replyMessage("Sorry, excessive use of power is not allowed.")
                elif(exp == "42"):
                    replyMessage("No need to think about that. It's The Answer to Life, the Universe, and Everything, of course!")
                elif(msg.split()[0] == "evalstatement"):
                    replyEmote("thinks...")
                    result = eval(exp)
                    str_result = str(result)
                    if(len(str_result) > 100):
                        replyMessage("That's too long, I won't write all that down...")
                    else:
                        replyMessage(str_result)
                        return result
                else:
                    replyEmote("thinks...")
                    result = eval(exp)
                    str_result = str(result)
                    if(len(str_result) > 100):
                        replyMessage("That's too long, I won't write all that down...")
                    else:
                        replyMessage("I think '" + exp + "' evaluates to '" + str_result + "', but I'm not all knowing. ;)")
                        return result
            except:
                replyMessage("Too complex to do with mental arithmetics. Am I a computer or what!?")

    def onPrivateMessage(self, irclib, source, msg):
        self.handleMessage( msg, "Sorry, _ is not available for private queries yet.",
                           (lambda reply: irclib.sendPrivateMessage(source, reply)),
                           (lambda reply: irclib.sendPrivateEmote(source, reply))
                          )


    def onChannelMessage(self, irclib, source, msg):
        thisResult = self.handleMessage( msg, MathEvalPlugin.latestResult,
                                        (lambda reply: irclib.sendChannelMessage(reply)),
                                        (lambda reply: irclib.sendChannelEmote(reply))
                                       )
        if thisResult:
            MathEvalPlugin.latestResult = thisResult

if __name__ == "__main__":
    class IrcLibMock:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
        def sendPrivateEmote(self, target, text):
            print "* " + text
        def sendChannelEmote(self, text):
            print "* " + text
    a = MathEvalPlugin()
    a.onChannelMessage(IrcLibMock(), "source", "eval 1+2")
    a.onChannelMessage(IrcLibMock(), "source", "eval 1+_")
    a.onChannelMessage(IrcLibMock(), "source", "irclib.sendChannelMessage('test')")
