import httplib
import re
#from modules import LogLib
import csv
import string
import formatter
import htmllib
import StringIO
import threading
import thread
import datetime
import logging





class ImdbNickLookupPlugin:

    def __init__(self):
        pass

    def onChannelMessage(self, irclib, source, msg):
        print msg.split()
        if len(msg.split()) >= 2 and msg.split()[0] == "imdbwatch":
            person = msg.split()[1]
            for (nick, user) in irclib.getUserList().items():
                if user.getCanonicalNick() == person:
                    if user.nick.find('|') != -1:
                        tag = user.nick.split('|')[1]
                        if re.match("tt\d{7}", tag):
                            irclib.sendChannelMessage("http://www.imdb.com/title/%s" % tag)
                            return
                    irclib.sendChannelMessage("That person doesn't seem to be watching anything.")
                    return
            irclib.sendChannelMessage("I can't see that person.")
            return



if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
