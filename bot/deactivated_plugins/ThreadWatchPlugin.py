import httplib
import re
#from modules import LogLib
import string
import htmllib
import formatter
import datetime
import StringIO
import poplib
import socket        #for socket.error




class AccessDeniedRestrictedForumError(Exception):
    pass
class AccessDeniedThreadDoesNotExistError(Exception):
    pass



class ThreadWatchPlugin:

    def __init__(self):
        # set member variables
        self.timeOfLastCheck = datetime.datetime.now()
        self.sourceHost = "www.freeallegiance.org"
#        self.sourceViewLastPostsUrl = "/modules.php?name=Forums&file=search&search_id=newposts"
        self.sourceMarkAsReadUrl    = "/modules.php?name=Forums&file=index&mark=forums"
#        self.sourceThreadAccessUrlTemplate = "/modules.php?name=Forums&file=viewtopic&t=%s"
        self.sourceCookie = "user=MzA0ODA6UlRCb3Q6MDE4MjE2ZmE5Nzc1MjU2ODk0MzY3NDRiMjAzNTBkZjU6MTA6OjA6MDowOjA6OjQwOTY%3D"
        self.linkTemplate = "http://www.freeallegiance.org/modules.php?name=Forums&file=viewtopic&p=%s#%s"
        self.checkInterval = 60       # in seconds, up to 3600*24
#        self.watchedThreads = {}
        self.watchThreadUrlTemplate = "/modules.php?name=Forums&file=viewtopic&t=%s&watch=topic"
        self.unwatchThreadUrlTemplate = "/modules.php?name=Forums&file=viewtopic&t=%s&unwatch=topic"
        self.popHost = "localhost"
        self.popUser = "rtbot%tufer.de"
        self.popPass = "tufer"
        self.markAllThreadsRead()



    def getVersionInformation(self):
        return("$Id: ThreadWatchPlugin.py 214 2006-03-26 21:03:03Z cortex $")



    def getPage(self, host, url, cookies):
        conn = httplib.HTTPConnection(host)
        #cookieString = ("%s=%s" % (
        myHeaders = {"Cookie": cookies}
        conn.request("GET", url, headers=myHeaders)
        r1 = conn.getresponse()
        #print r1.status, r1.reason, r1.getheader("Location")
        data = r1.read()
        conn.close()
        #LogLib.log.add(False, str((r1.status, data, r1.getheader("Location"))))
        return((r1.status, data, r1.getheader("Location")))



    def decodeHTMLCharacterEntities(self, code):
        #print code
        outputstring = StringIO.StringIO()
        w = formatter.DumbWriter(outputstring, maxcol = 9999999) # plain text
        f = formatter.AbstractFormatter(w)
        p = htmllib.HTMLParser(f)
        p.feed(code)
        p.close()
        #print outputstring.getvalue()
        return(outputstring.getvalue())



    def stripHTMLCode(self, code):
        result = code
        result = re.sub("<.*?>", "", result)
        #result = re.sub("&#34;", "\"", result)
        #result = re.sub("&#.*?;", "", result)
        return(self.decodeHTMLCharacterEntities(result).strip())



    def collapseIrrelevantWhitespaces(self, source):
        result = re.sub("\n", "", source)
        result = re.sub(">\s*?<", "><", result)
        return(result)



    def markAllThreadsRead(self):
        #pass
        (status2, dummy, location2) = self.getPage(self.sourceHost,
                                                self.sourceMarkAsReadUrl,
                                                self.sourceCookie)



    def getThreadTitle(self, threadID):
        (status, page, location) = self.getPage(self.sourceHost,
                                                self.sourceThreadAccessUrlTemplate % (threadID),
                                                self.sourceCookie)
        #file = open("test.txt", "w")
        #file.writelines(page)
        #file.close()
        if(re.compile("Sorry, but only <b>users granted special access</b> can read topics in this forum.", re.DOTALL).search(page)):
            raise AccessDeniedRestrictedForumError()
        if(re.compile("The topic or post you requested does not exist", re.DOTALL).search(page)):
            raise AccessDeniedThreadDoesNotExistError()
        RE = "<title>Freeallegiance :: View topic - (.*?)</title>"
        result = re.compile(RE, re.DOTALL).search(page)
        return(result.group(1))



    def parseUpdateEMails(self):
        RE = "Hello,(?P<author>.*?) has just replied to a thread you have subscribed to entitled - \"(?P<title>.*?)\" at Freeallegiance\..*?http://www.freeallegiance.org/modules.php\?name=Forums&file=viewtopic&p=(?P<postID>\d+?)#(?P<postID2>\d+).*?http://www.freeallegiance.org/modules.php\?name=Forums&file=viewtopic&t=(?P<threadID>\d+?)&unwatch=topic"

        result = []
        try:
            M = poplib.POP3(self.popHost)
        except socket.error:
            return([])
        M.user(self.popUser)
        M.pass_(self.popPass)
        list = M.list()
        messageList = list[1]
        for message in messageList:
            (ID, octets) = message.split()
            (response, text, octets) = M.retr(ID)
            #print str(text)
            #print
            #print
            concatinated_text = string.join(text, "")
            #print concatinated_text
            re_result = re.compile(RE).search(concatinated_text)
            if(re_result):
                match = {"author": re_result.group("author"),
                         "title": re_result.group("title"),
                         "postID":  re_result.group("postID"),
                         "postID2":  re_result.group("postID2"),
                         "threadID":  re_result.group("threadID")}
                #print match
                result.append(match)
            M.dele(ID)
        M.quit()
        return(result)



    def checkForChanges(self, irclib):
        emails = self.parseUpdateEMails()
        #irclib.sendPrivateMessage("Cort[]", str(emails))
        
        # if there is a change, mark all as read again
        if(emails):
            #irclib.sendPrivateMessage("Cort[]", "marking as read...")
            self.markAllThreadsRead()

        # notify
        for match in emails:
            #if(update["threadID"] in self.watchedThreads):
            link = self.linkTemplate % (match["postID"], match["postID"])
            irclib.sendChannelMessage("%s has posted in thread '%s', link: %s" % (match["author"], match["title"], link))



    def onTimer(self, irclib):
        if(self.timeOfLastCheck):
            deltatime = datetime.datetime.now() - self.timeOfLastCheck
            if((deltatime.days != 0) or (deltatime.seconds > self.checkInterval)):
                self.checkForChanges(irclib)
                self.timeOfLastCheck = datetime.datetime.now()



    def watchThread(self, threadID):
        (status, page, location) = self.getPage(self.sourceHost,
                                                self.watchThreadUrlTemplate % (threadID),
                                                self.sourceCookie)



    def unwatchThread(self, threadID):
        (status, page, location) = self.getPage(self.sourceHost,
                                                self.unwatchThreadUrlTemplate % (threadID),
                                                self.sourceCookie)



    def onChannelMessage(self, irclib, source, msg):
        if((len(msg.split()) >= 2) and (msg.split()[0] == "watchthread")):
            threadID = msg.split()[1]
            irclib.sendChannelMessage("Okay, I'll watch the thread!")
            self.watchThread(threadID)
        if((len(msg.split()) >= 2) and (msg.split()[0] == "unwatchthread")):
            threadID = msg.split()[1]
            irclib.sendChannelMessage("Okay, I'll stop watching the thread.")
            self.unwatchThread(threadID)
#        if((len(msg.split()) >= 1) and (msg.split()[0] == "listwatchedthreads")):
#            irclib.sendChannelMessage("Watched threads: %s" % (string.join(self.watchedThreads.values(), ", ")))



if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text

#    file = open("temp.html", "r")
#    page = string.join(file.readlines())
#    file.close()

    c = ThreadWatchPlugin()
#    c.parseUpdateEMails()

    #for hit in c.extractUpdates(page):
   #     print str(hit)
    
    c.onChannelMessage(FakeIrcLib(), "source", "watchthread 20281")
    c.onChannelMessage(FakeIrcLib(), "source", "watchthread 99999")
    c.onChannelMessage(FakeIrcLib(), "source", "watchthread 19999")
    c.checkForChanges(FakeIrcLib())
#    c.onChannelMessage(FakeIrcLib(), "source", "unwatchthread 19999")
#    c.onChannelMessage(FakeIrcLib(), "source", "unwatchthread 20281")
    #c.refreshTimezones()
    #print c.normaliseOffset("+3")
    #print c.normaliseOffset("-4:30")
    #print c.normaliseOffset("-13")

      #t.listAll()
#     print t.getTime("EDT")
#     print t.getTime("bERL")
#     print t.getTime("+5")
#     print t.getTime("aaaaa")
