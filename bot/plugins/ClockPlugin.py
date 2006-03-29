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



class ClockPlugin:

    def __init__(self):
        # set member variables
        self.timezoneFilename = "resources/timezones.csv"
        self.aliasFilename = "resources/timezone_aliases.csv"
        self.citiesSource = {"host": "www.timeanddate.com", "path": "/worldclock/", "file": "full.html"}
        self.zonesSource = {"host": "www.timeanddate.com", "url": "/library/abbreviations/timezones/"}
        self.isRefreshRunning = False

        # initialise
        self.loadTimezones()
        

    
    def dispose(self):
        if(self.isRefreshRunning):
            self.isRefreshRunning = False



    def getVersionInformation(self):
        return("$Id$")



    def getPage(self, host, url):
        conn = httplib.HTTPConnection(host)
        conn.request("GET", url)
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



    def normaliseOffset(self, offset):
        (direction, delta_hours, dummy, delta_minutes) = re.compile("([+-])(\d\d?)(:(\d\d))?").match(offset).groups()
        if(delta_minutes == None):
            delta_minutes = "00"
        normalised = "%s%.2i%.2i" % (direction, int(delta_hours), int(delta_minutes))
        return(normalised)
        



    def refreshTimezones(self):
        # runs in a new thread but can be terminated by setting isRefreshRunning to False
        newTimezones = {}
    
        # find cities
        (status, page, location) = self.getPage(self.citiesSource["host"], self.citiesSource["path"]+self.citiesSource["file"])
        numCities = 0
        for (url, city) in re.compile("<a href=\"(city.html\?n=.*?)\">(.*?)</a>").findall(page):
          numCities += 1
          #if(numCities == 21):
          #  break
          
          # terminate if asked for
          if(not self.isRefreshRunning):
              return

          # get the city's page and extract it's timezone information
          (city_status, city_page, city_location) = self.getPage(self.citiesSource["host"], self.citiesSource["path"]+url)
          fullname = self.decodeHTMLCharacterEntities(re.compile("<span class=\"biggest\">(.*?)</span>", re.DOTALL).search(city_page).group(1))
          timezone_string = re.compile("<tr class=\"d1\"><th>UTC/GMT Offset</th><td><table border=\"0\" cellpadding=\"2\" cellspacing=\"0\">(.*?)</table>.</td></tr>", re.DOTALL).search(city_page).group(1)
    
          # terminate if asked for
          if(not self.isRefreshRunning):
              return

          # try to find a "Current time zone offset" text (i.e. town in summertime)
          result1 = re.compile("Current time zone offset:.*?UTC/GMT ([-+]\d\d?) hour", re.DOTALL).search(timezone_string)
          if(result1):
              offset = result1.group(1)
    
          # try to find a "Standard time zone" text (i.e. town in summertime)
          else:
              result2 = re.compile("Standard time zone:.*?UTC/GMT ([-+]\d\d?(:\d\d)?) hour", re.DOTALL).search(timezone_string)
              if(result2):
                  offset = result2.group(1)

          # try to find a "Standard time zone: No UTC/GMT offset" text (i.e. town in summertime)
              else:
                  result3 = re.compile("Standard time zone:.*?No UTC/GMT offset", re.DOTALL).search(timezone_string)
                  if(result3):
                      offset = "+0"
                  else:
                      print "Error: $$$%s$$$" % (timezone_string)
    
          # try to find a "Time zone abbreviation"
          result4 = re.compile("Time zone abbreviation:</td><td>(.*?)</td>", re.DOTALL).search(timezone_string)
          if(result4):
              timezone = string.strip(re.compile("<.*?>").sub("", result4.group(1)))
          elif(offset == "+0"):
              timezone = "UTC - Coordinated Universal Time"
          else:
              timezone = "no timezone abbreviation"
    
          #print "|%s|%s|%s|" % (fullname, offset, timezone_abbrev)
          decodedTimezone = self.decodeHTMLCharacterEntities(timezone)
          normalisedOffset = self.normaliseOffset(offset)
          newTimezones[fullname] = (normalisedOffset, decodedTimezone)

        # find timezones
        numZones = 0
        (status, page, location) = self.getPage(self.zonesSource["host"], self.zonesSource["url"])
        for (fullname, timezone, dummy1, offset, dummy3) in re.compile("<td><a href=\".*?\">(.*?)</a></td><td>(.*?)</td><td>.*?</td><td>UTC(\s([+-]\s\d\d?(:\d\d)?) hours?)?</td>").findall(page):
          numZones += 1
          
          # terminate if asked for
          if(not self.isRefreshRunning):
              return

          decodedTimezone = self.decodeHTMLCharacterEntities(timezone)
          #print "|%s|%s|%s|" % (fullname, decodedTimezone, offset)
          if(offset == ""):
            newTimezones[fullname] = ("+0000", "%s - %s" % (fullname, decodedTimezone))
          else:
            normalisedOffset = self.normaliseOffset(offset[0] + offset[2:])
            newTimezones[fullname] = (normalisedOffset, "%s - %s" % (fullname, decodedTimezone))

    #    for zone in self.timezones.keys():
    #      print "|%s|%s|%s|" % (zone, self.timezones[zone][0], self.timezones[zone][1])
        # write the CSV
        file = open(self.timezoneFilename, "wb")
        writer = csv.writer(file)
        for zone in newTimezones.keys():
          writer.writerow((zone, newTimezones[zone][0], newTimezones[zone][1]))
        file.close()

        self.refreshFinishedEvent.set()



    def loadTimezones(self):
        # read timezones
        self.timezones = {}
        file = open(self.timezoneFilename, "rb")
        reader = csv.reader(file)
        for row in reader:
            self.timezones[row[0]] = (row[1], row[2])
        file.close()

        # read aliases
        self.aliases = {}
        file = open(self.aliasFilename, "rb")
        reader = csv.reader(file)
        for row in reader:
            self.aliases[row[0]] = row[1]
        file.close()



    def onTimer(self, irclib):
        if(self.isRefreshRunning and self.refreshFinishedEvent.isSet()):
            self.loadTimezones()
            irclib.sendChannelMessage("Phew! That was some hard work, but I updated the timezones! '4")
            self.isRefreshRunning = False
            return



    def doTimezoneRefresh(self):
        self.refreshFinishedEvent = threading.Event()
        self.isRefreshRunning = True
        thread.start_new_thread(self.refreshTimezones, ())
        


    def getTime(self, modifier, basetime = False):        # basetime==False-->current time, otherwise basetime has to be a datetime.datetime
        if(not basetime):
            basetime = datetime.datetime.utcnow()
        direction = modifier[0]
        delta_hours = modifier[1:3]
        delta_minutes = modifier[3:5]
        delta = datetime.timedelta(hours=int(delta_hours), minutes=int(delta_minutes))
        if(direction == "+"):
            adjustedTime = basetime + delta
        else:
            adjustedTime = basetime - delta
        return(adjustedTime)



    def getTimeString(self, time):
        return(time.strftime("%A, %d %b %Y %H:%M:%S"))



    def findZone(self, nameparts, checkForAliases=True):
        currentBestZone = ""

        # construct RE
        RE = string.lower(string.join(map(re.escape, nameparts), ".*?"))
        #print RE

        for zone in self.timezones.keys():
            if(re.search(RE, string.lower(zone))):
                if(len(zone) == len(string.join(nameparts))):
                    currentBestZone = zone
                    modifier = self.timezones[currentBestZone][0]
                    zonename = self.timezones[currentBestZone][1]
                    break
                elif(len(zone) > len(currentBestZone)):
                    currentBestZone = zone
                    modifier = self.timezones[currentBestZone][0]
                    zonename = self.timezones[currentBestZone][1]
        if(len(currentBestZone) == 0):
            for zone in self.aliases.keys():
                if(re.search(RE, string.lower(zone))):
                    currentBestZone = zone
                    lookupresult = self.findZone([self.aliases[zone]], False)
                    if(lookupresult):
                        (dummy, modifier, zonename) = lookupresult
                        break

        if(re.match("^[+-]\d\d\d\d$", string.join(nameparts))):
            return(string.join(nameparts), string.join(nameparts), "[manually specified zone]")
        elif(len(currentBestZone) == 0):
            return(None)
        else:
            return(currentBestZone, modifier, zonename)



    def showResult(self, irclib, namepart):
        #print namepart
        result = self.findZone(namepart)

        if(result):
            (name, modifier, zonename) = result
            adjustedTime = self.getTimeString(self.getTime(modifier))
            message = "%s: %s %s (%s)" % (name, adjustedTime, modifier, zonename)
            irclib.sendChannelMessage(message)
        else:
            irclib.sendChannelMessage("Sorry, I couldn't find this timezone or city. :(")



    def showTranslation(self, irclib, arguments):
        # extract specified time
        try:
            time = arguments[0]
            hours = int(time[0:2])
            minutes = int(time[3:5])
        except:
            irclib.sendChannelMessage("That is not a valid time: HH:MM")
            return

        # detect sourceZone and targetZone
        inIndex = arguments.index("in")
        sourceZone = arguments[1:inIndex]
        targetZone = arguments[inIndex+1:]
        #print "|%s|%s|" % (str(sourceZone), str(targetZone))
        
        # find the zones
        source = self.findZone(sourceZone)
        if(not source):
            irclib.sendChannelMessage("That is not a valid source timezone!")
            return
        (source_zone, source_modifier, source_zonename) = source
        target = self.findZone(targetZone)
        if(not target):
            irclib.sendChannelMessage("That is not a valid target timezone!")
            return
        (target_zone, target_modifier, target_zonename) = target
        
        # calculate times
        nowtime = datetime.datetime.utcnow()
        basetime = datetime.datetime(nowtime.year, nowtime.month, nowtime.day, hours, minutes)
        source_direction = source_modifier[0]
        source_hours = source_modifier[1:3]
        source_minutes = source_modifier[3:5]
        delta = datetime.timedelta(hours=int(source_hours), minutes=int(source_minutes))
        if(source_direction == "+"):
            adjustedTime = basetime - delta
        else:
            adjustedTime = basetime + delta

        # give output
        #irclib.sendChannelMessage("%s %s is %s %s" % (self.getTimeString(self.getTime(source_modifier, adjustedTime)), source_zonename, self.getTimeString(self.getTime(target_modifier, adjustedTime)), target_zonename))
        sourceTimeString = "%s in %s (%s)" % (self.getTime(source_modifier, adjustedTime).strftime("%H:%M:%S"), source_zone, source_zonename)
        targetTimeString = "%s in %s (%s)" % (self.getTime(target_modifier, adjustedTime).strftime("%H:%M:%S"), target_zone, target_zonename)
        irclib.sendChannelMessage("%s is %s" % (sourceTimeString, targetTimeString))



    def defineAlias(self, irclib, arguments):
        # detect alias and location
        asIndex = arguments.index("as")
        alias = arguments[:asIndex]
        location = arguments[asIndex+1:]
        #print "|%s|%s|" % (str(alias), str(location))

        lookupresult = self.findZone(location)
        if(lookupresult):
            (target, modifier, zonename) = lookupresult
            #print string.join(alias)
            self.aliases[string.join(alias)] = target
            irclib.sendChannelMessage("Okay, I defined '%s' as an alias of '%s'." % (string.join(alias), target))
            # write the CSV
            file = open(self.aliasFilename, "wb")
            writer = csv.writer(file)
            for alias in self.aliases.keys():
              writer.writerow((alias, self.aliases[alias]))
            file.close()
        else:
            irclib.sendChannelMessage("I don't know a timezone that matches '%s'." % (location))



    def onChannelMessage(self, irclib, source, msg):
        if((len(msg.split()) > 0) and (msg.split()[0] == "clock")):
            if(self.isRefreshRunning):
                irclib.sendChannelMessage("I'm busy updating the tables, don't bother me!")
            elif(len(msg.split()) > 1):
                commandArguments = msg.split()[1:]
                trailing = msg.split(None, 1)[1]
                if(commandArguments[0] == "update"):
                    irclib.sendChannelMessage("Do I really have to? Oh well, this will take a while...")
                    self.doTimezoneRefresh()
                elif((len(commandArguments) >= 4) and (commandArguments[0] == "define") and ("as" in commandArguments[2:])):
                    self.defineAlias(irclib, commandArguments[1:])
                elif((len(commandArguments) >= 4) and ("in" in commandArguments[1:])):
                    self.showTranslation(irclib, commandArguments[0:])
                else:
                    self.showResult(irclib, commandArguments)
            else:
                self.showResult(irclib, ["UTC"])



if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text

    c = ClockPlugin()
#    c.onChannelMessage(FakeIrcLib(), "source", "clock berl")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock delhi")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock 10:00 New York in England")
    #print "findZone: |%s|" % (c.findZone("clock Abidjan, Cote d'Ivoire (Ivory Coast)"))
    #c.onChannelMessage(FakeIrcLib(), "source", "clock Abi")
    #c.onChannelMessage(FakeIrcLib(), "source", "clock +0300")
    c.onChannelMessage(FakeIrcLib(), "source", "clock define Tuebingen, Baden-Wuerttemberg, Germany as Berlin")
    c.onChannelMessage(FakeIrcLib(), "source", "clock Tuebingen")
    #c.refreshTimezones()
    #print c.normaliseOffset("+3")
    #print c.normaliseOffset("-4:30")
    #print c.normaliseOffset("-13")

      #t.listAll()
#     print t.getTime("EDT")
#     print t.getTime("bERL")
#     print t.getTime("+5")
#     print t.getTime("aaaaa")
