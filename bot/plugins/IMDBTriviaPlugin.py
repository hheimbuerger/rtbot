import random, re, logging, httplib, urllib, htmllib, formatter, StringIO

class IMDBTriviaPlugin:
    def __init__(self):
        pass

    def getVersionInformation(self):
        return("$Id$")

    def getPage(self, host, url):
        conn = httplib.HTTPConnection(host)
        conn.request("GET", url)
        r1 = conn.getresponse()
        #print r1.status, r1.reason, r1.getheader("Location")
        data = r1.read()
        conn.close()
        #logging.debug(str((r1.status, data, r1.getheader("Location"))))
        return((r1.status, data, r1.getheader("Location")))

    def extractAllPopularFilmSearchResults(self, page):
        result = []

        #a = open("temp.txt", "w")
        #a.write(page)
        #a.close()

#        reobj = re.compile("<ol>(.*?)</ol>", re.DOTALL).search(page)
        reobj = re.compile("<table>(.*?)</table>", re.DOTALL).search(page)
        if(not reobj):
            logging.debug("IMDBTriviaLib: couldn't find the film list")
            return(result)
        filmList = reobj.group(1)
        #print filmList
        #print

#        reobj = re.compile("<li>(.*?)</li>(.*)", re.DOTALL).search(filmList)
        reobj = re.compile("<tr>(.*?)</tr>(.*)", re.DOTALL).search(filmList)
        while(reobj):
            #print reobj.group(1)
            #print
            thisFilm = reobj.group(1)
            filmList = reobj.group(2)

            reobj = re.search("href=\"(/title/.*?)(\?)?\"", thisFilm)
            
            #sometimes, a weird GET argument is attached, like /title/tt0088763/?fr=c2l0ZT1kZnx0dD0xfGZiPXV8cG49MHxrdz0xfHE9RnV0dXJ8ZnQ9MXxteD0yMHxsbT01MDB8Y289MXxodG1sPTF8bm09MQ__;fc=1;ft=23;fm=1
            #removing this here
            if(reobj.group(1).find("?") == -1):
                result.append(reobj.group(1))
            else:
                cleansedURL = reobj.group(1)[:reobj.group(1).find("?")]
                logging.debug("IMDBTriviaLib: removing URL artifact from (%s), result (%s)" % (reobj.group(1), cleansedURL))
                result.append(cleansedURL)
            
            reobj = re.search("<li>(.*?)</li>(.*)", filmList)
        
#        a = open("temp.txt", "w")
#        a.write(data1)
#        a.close()

        return(result)

    def extractAllTrivia(self, page):
        result = []

#        a = open("temp.txt", "w")
#        a.write(page)
#        a.close()

        reobj = re.compile("<ul class=\"trivia\">(.*?)</ul>(.*)", re.DOTALL).search(page)
        while(reobj):
            triviaList = reobj.group(1)
            page = reobj.group(2)
            
            reobj2 = re.compile("<li>(.*?)</li>(.*)", re.DOTALL).search(triviaList)
            while(reobj2):
                #print reobj.group(1)
                #print
                thisTrivia = reobj2.group(1)
                triviaList = reobj2.group(2)
    
                result.append(thisTrivia)
                #reobj = re.search("href=\"(.*?)\"", thisFilm)
                #result.append(reobj.group(1))
                
                reobj2 = re.compile("<li>(.*?)</li>(.*)", re.DOTALL).search(triviaList)

            reobj = re.compile("<ul class=\"trivia\">(.*?)</ul>(.*)", re.DOTALL).search(page)

        return(result)

    def getTitle(self, page):
#        reobj = re.compile("<title>Trivia for (.*?)</title>", re.DOTALL).search(page)
        reobj = re.compile("<title>(.*?) - Trivia</title>", re.DOTALL).search(page)
        if(reobj):
            return(reobj.group(1))
        else:
            return("[error reading title]")

    def getType(self, title):
        if(title[0] == "\""):
            return("series")
        elif(title[-4:] == "(VG)"):
            return("video game")
        else:
            return("film")

    def cleanseTitle(self, title):
        if((title[0] == "\"") and (title[-8] == "\"")):
            return(title[1:-8] + title[-7:])
        elif(title[-5:] == " (VG)"):
            return(title[:-5])
        else:
            return(title)

    def stripHTMLCode(self, code):
        result = code
        result = re.sub("<.*?>", "", result)
        #result = re.sub("&#34;", "\"", result)
        #result = re.sub("&#.*?;", "", result)
        return(self.decodeHTMLCharacterEntities(result).strip())

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

    def findFilmAndExtractTrivia(self, query):
        (status, page, url) = self.getPage("www.imdb.com", "/find?tt=on;q=" + urllib.quote(query))
        if(status == 200):        #"ok"
            logging.debug("IMDBTriviaLib: got search result page, selecting first of the popular results")
            films = self.extractAllPopularFilmSearchResults(page)
            if(not films):
                logging.debug("IMDBTriviaLib: no popular films found on (%s)" % ("/find?q=" + urllib.quote(query)))
                return
            chosenFilm = films[0]
            #print "URL = " + chosenFilm + "trivia"
            (status, page, url) = self.getPage("www.imdb.com", chosenFilm+"trivia")
            logging.debug("IMDBTriviaLib: selected (%s), extracting trivia now" % (chosenFilm+"trivia"))

            #a = open("temp.txt", "w")
            #a.write(page)
            #a.close()

            title = self.getTitle(page)
            trivia = self.extractAllTrivia(page)
            return((title, trivia))
        elif(status == 302):        #"forward"
            reobj = re.match("http://www\.imdb\.com(.*)", url)
            chosenFilm = reobj.group(1)
            (status, page, url) = self.getPage("www.imdb.com", chosenFilm+"trivia")
            logging.debug("IMDBTriviaLib: direct film hit (%s), extracting trivia now" % (chosenFilm+"trivia"))
            title = self.getTitle(page)
            trivia = self.extractAllTrivia(page)
            return((title, trivia))
        else:
            #print "IMDBTriviaLib: incorrect status code: " + status + " (query: " + query + ")"
            logging.debug("IMDBTriviaLib: incorrect status code: " + status + " (query: " + query + ")")

    def getStrippedRandomTrivia(self, query):
#        try:
            result = self.findFilmAndExtractTrivia(query)
            if(result):
                (title, trivia) = result
                if(len(trivia) > 0):
                    rand = int(random.random() * len(trivia))-1
                    #print rand
                    return((self.stripHTMLCode(title), self.stripHTMLCode(trivia[rand])))
                else:
                    return((self.stripHTMLCode(title), "Sorry, he doesn't know any trivia for that film."))
            else:
                return(None)
#        except:
#            return("unknown", "Sorry, I had problems while trying to find trivia for that film.")

    def showTrivia(self, irclib, query):
#          self.irclib.sendChannelMessage("Sorry, I lost the phone number of my friend, the IMDBBot. :(")
        result = self.getStrippedRandomTrivia(query)
        if(not result):
            irclib.sendChannelEmote("asks his friend, the IMDBBot, about that film, but he doesn't know it.")
        else:
            (title, trivia) = result
            irclib.sendChannelEmote("asks his friend, the IMDBBot, about that " + self.getType(title) + " " + self.cleanseTitle(title) + "...")
            irclib.sendChannelMessage(trivia)

    def onChannelMessage(self, irclib, source, msg):
        if((len(msg.split()) >= 2) and (msg.split()[0] == "trivia")):
            self.showTrivia(irclib, msg[7:])
 





if __name__ == "__main__":
    searchterm = "vampire"     #"sedim na konari a je mi dobre"       #
    a = IMDBTriviaPlugin()
    #print a.cleanseTitle("\"Futurama\" (1999)")
    result = a.getStrippedRandomTrivia(searchterm)
    print result[0] + " = \"" + result[1] + "\""
    
#    films = a.getAllPopularFilmResults("www.imdb.com", "/find?q=" + urllib.quote("crossing jordan"))
#    list = a.getAllTrivia("www.imdb.com", films[0]+"trivia")
#    print a.stripHTMLCode("abc<de>fgh")
#    b = open("temp.txt", "w")
#    for c in list:
#        b.write(a.stripHTMLCode(c) + "\n")
#    b.close()
    #a.getAllTrivia()
    #print string.join(a.getAllTrivia(), "\n")








#        params = urllib.urlencode({'spam': 1, 'eggs': 2, 'bacon': 0})
#        headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
#        conn = self.httplib.HTTPConnection("musi-cal.mojam.com:80")
#        conn.request("POST", "/cgi-bin/query", params, headers)
#        response = conn.getresponse()
#        print response.status, response.reason
#        data = response.read()
#        conn.close()
