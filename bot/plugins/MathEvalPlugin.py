import math

class MathEvalPlugin:

    def getVersionInformation(self):
        return("$Id$")

    def onPrivateMessage(self, irclib, source, msg):
        if((len(msg.split()) > 1) and (msg.split()[0] == "eval")):
            try:
                exp = msg.split(None, 1)[1]
                if(exp == "42"):
                    irclib.sendPrivateMessage(source, "No need to think about that. It's The Answer to Life, the Universe, and Everything, of course!")
                else:
                    result = eval(exp)
                    str_result = str(result)
                    irclib.sendPrivateEmote("thinks...")
                    if(len(str_result) > 100):
                        irclib.sendPrivateMessage(source, "That's too long, I won't write all that down...")
                    else:
                        irclib.sendPrivateMessage(source, "I think '" + exp + "' evaluates to '" + str_result + "', but I'm not all knowing. ;)")
            except:
                irclib.sendPrivateMessage(source, "Too complex to do with mental arithmetics. Am I a computer or what!?")

    def onChannelMessage(self, irclib, source, msg):
        if((len(msg.split()) > 1) and ((msg.split()[0] == "eval") or (msg.split()[0] == "evalstatement"))):
            try:
                exp = msg.split(None, 1)[1]
                if(exp == "42"):
                    irclib.sendChannelMessage("No need to think about that. It's The Answer to Life, the Universe, and Everything, of course!")
                elif(msg.split()[0] == "evalstatement"):
                    result = eval(exp)
                    str_result = str(result)
                    irclib.sendChannelEmote("thinks...")
                    if(len(str_result) > 100):
                        irclib.sendChannelMessage("That's too long, I won't write all that down...")
                    else:
                        irclib.sendChannelMessage(str_result)
                else:
                    result = eval(exp)
                    str_result = str(result)
                    irclib.sendChannelEmote("thinks...")
                    if(len(str_result) > 100):
                        irclib.sendChannelMessage("That's too long, I won't write all that down...")
                    else:
                        irclib.sendChannelMessage("I think '" + exp + "' evaluates to '" + str_result + "', but I'm not all knowing. ;)")
            except:
                irclib.sendChannelMessage("Too complex to do with mental arithmetics. Am I a computer or what!?")
