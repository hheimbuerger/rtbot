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





class AliasLookupTooDeepError(Exception):
    def __init__(self, alias):
        self.aliases = [alias]

class SubAliasNotFoundError(Exception):
    def __init__(self, alias):
        self.aliases = alias



class ClockPlugin:

    def __init__(self):
        # set member variables
        self.timezoneFilename = "resources/timezones.csv"
        self.aliasFilename = "resources/timezone_aliases.csv"
        self.citiesSource = {"host": "www.timeanddate.com", "path": "/worldclock/", "file": "full.html"}
        self.zonesSource = {"host": "www.timeanddate.com", "url": "/library/abbreviations/timezones/"}
        self.isRefreshRunning = False
        self.hasRefreshFailed = False

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
        lastUrlParsed = "[init]"
    
        try:
            # find cities
            (status, page, location) = self.getPage(self.citiesSource["host"], self.citiesSource["path"]+self.citiesSource['file'])
            numCities = 0
            for (url, city) in re.compile("<a href=\"(city.html\?n=.*?)\">(.*?)</a>").findall(page):
              numCities += 1
              #if(numCities == 21):
              #  break
              
              lastUrlParsed = url
              #print "Parsing %s..." % (url)
              
              # terminate if asked for
              if(not self.isRefreshRunning):
                  return
    
              # get the city's page and extract its timezone information
              (city_status, city_page, city_location) = self.getPage(self.citiesSource["host"], self.citiesSource["path"]+url)
              fullname = self.decodeHTMLCharacterEntities(re.compile("<span class=\"biggest\">(.*?)</span>", re.DOTALL).search(city_page).group(1))
              timezone_string = re.compile("<tr class=\"d2\"><th>UTC/GMT Offset</th><td id=\"tz1\"><table border=\"0\" cellpadding=\"2\" cellspacing=\"0\">(.*?)</table>", re.DOTALL).search(city_page).group(1)
        
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
              
              #print "New timezone: %s, %s (%s)" % (fullname, normalisedOffset, decodedTimezone)
    
            # find timezones
            numZones = 0
            (status, page, location) = self.getPage(self.zonesSource["host"], self.zonesSource["url"])
            lastUrlParsed = self.zonesSource["host"]+self.zonesSource["url"]
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
        except Exception, e:
            logging.debug("Exception!: %s" % (str(e)))
            logging.debug("Last URL parsed: %s" % (lastUrlParsed))
            self.refreshFailed = True

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
            if(self.hasRefreshFailed):
                irclib.sendChannelMessage("Refreshing the timezones has failed. The problem has been logged.")
                self.isRefreshRunning = False
                self.hasRefreshFailed = False
            else:
                self.loadTimezones()
                irclib.sendChannelMessage("Phew! That was some hard work, but I updated the timezones! '4")
                self.isRefreshRunning = False



    def doTimezoneRefresh(self):
        self.refreshFinishedEvent = threading.Event()
        self.isRefreshRunning = True
        thread.start_new_thread(self.refreshTimezones, ())
        #self.refreshTimezones()



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



    def findZone(self, nameparts, findOnlyAliases=False, currentLookupDepth=0):
        # ASSERT: nameparts is a list
        if(type(nameparts) != list):
            raise TypeError("ERROR: Parameter 'nameparts' has to be a list!")

        currentBestZone = ""

        # construct RE
        RE = string.lower(string.join(map(re.escape, nameparts), ".*?"))
        #print RE

        # first, try to find an exact match
        if(not findOnlyAliases):
            for zone in self.timezones.keys():
                if(string.lower(zone) == string.lower(string.join(nameparts))):
                    currentBestZone = zone
                    modifier = self.timezones[currentBestZone][0]
                    zonename = self.timezones[currentBestZone][1]

        # then try to find a matching alias
        if(currentBestZone == ""):
            for zone in self.aliases.keys():
                if(re.search(RE, string.lower(zone))):
                    currentBestZone = zone
                    if(currentLookupDepth >= 3):
                        raise AliasLookupTooDeepError(zone)
                    else:
                        try:
                            lookupresult = self.findZone([self.aliases[zone]], currentLookupDepth=currentLookupDepth+1)
                        except AliasLookupTooDeepError, exc:
                            exc.aliases.append(zone)
                            raise exc
                        except SubAliasNotFoundError, exc:
                            exc.aliases.append(zone)
                            raise exc
                        if(not lookupresult):
                            raise SubAliasNotFoundError([self.aliases[zone], zone]) 
                        (dummy, modifier, zonename) = lookupresult
                        break

        # if that didn't give a result, search through the rest of the list
        if(not findOnlyAliases):
            if(currentBestZone == ""):
                for zone in self.timezones.keys():
                    if(string.lower(zone) == string.join(nameparts)):
                        currentBestZone = zone
                        modifier = self.timezones[currentBestZone][0]
                        zonename = self.timezones[currentBestZone][1]
                    elif(re.search(RE, string.lower(zone))):
                        if(len(zone) == len(string.join(nameparts))):
                            currentBestZone = zone
                            modifier = self.timezones[currentBestZone][0]
                            zonename = self.timezones[currentBestZone][1]
                            break
                        elif(len(zone) > len(currentBestZone)):
                            currentBestZone = zone
                            modifier = self.timezones[currentBestZone][0]
                            zonename = self.timezones[currentBestZone][1]
    
            if(re.match("^[+-]\d\d\d\d$", string.join(nameparts))):
                return(string.join(nameparts), string.join(nameparts), "[manually specified zone]")
        
        if(currentBestZone == ""):
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
            if(time[2] != ":"):
                raise ValueError()
            nowtime = datetime.datetime.utcnow()
            basetime = datetime.datetime(nowtime.year, nowtime.month, nowtime.day, hours, minutes)
        except ValueError:
            irclib.sendChannelMessage("That is not a valid time (format: HH:MM)!")
            return

        # detect sourceZone and targetZone
        inIndex = arguments.index("in")
        sourceZone = arguments[1:inIndex]
        targetZone = arguments[inIndex+1:]
        #print "|%s|%s|" % (str(sourceZone), str(targetZone))
        
        # find the zones
        if(sourceZone == []):
            source = self.findZone(["UTC"])
        else:
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



    def saveAliasDatabase(self):
        # write the CSV
        file = open(self.aliasFilename, "wb")
        writer = csv.writer(file)
        for alias in self.aliases.keys():
          writer.writerow((alias, self.aliases[alias]))
        file.close()



    def defineAlias(self, irclib, arguments):
        # detect alias and location
        asIndex = arguments.index("as")
        alias = arguments[:asIndex]
        location = arguments[asIndex+1:]
        #print "|%s|%s|" % (str(alias), str(location))

        aliasresult = self.findZone(alias)
        lookupresult = self.findZone(location)
        #if(aliasresult and lookupresult and (aliasresult == lookupresult)):
        #    irclib.sendChannelMessage("You can't create an alias to itself.")
        if(aliasresult):
            irclib.sendChannelMessage("You can't create the alias '%s', it already resolves to '%s'." % (string.join(alias), aliasresult[0]))
        elif(lookupresult):
            (target, modifier, zonename) = lookupresult
            #print string.join(alias)
            self.aliases[string.join(alias)] = target
            irclib.sendChannelMessage("Okay, I defined '%s' as an alias of '%s'." % (string.join(alias), target))
            self.saveAliasDatabase()
        else:
            irclib.sendChannelMessage("I don't know a timezone that matches '%s'." % (string.join(location)))



    def deleteAlias(self, irclib, alias):
        aliasString = string.join(alias)
        if(aliasString in self.aliases.keys()):
            irclib.sendChannelMessage("The alias '%s'->'%s' has been deleted." % (aliasString, self.aliases[aliasString]))
            del self.aliases[aliasString]
            self.saveAliasDatabase()
        else:
            irclib.sendChannelMessage("There is no alias '%s'." % (aliasString))



    def displayAlias(self, irclib, alias):
        aliasString = string.join(alias)
        if(aliasString in self.aliases.keys()):
            irclib.sendChannelMessage("The alias '%s' is defined as '%s'." % (aliasString, self.aliases[aliasString]))
        else:
            aliasresult = self.findZone(alias, findOnlyAliases=True)
            if(aliasresult):
                irclib.sendChannelMessage("There is no alias '%s', but '%s' is resolved to '%s'." % (aliasString, aliasString, aliasresult[0]))
            else:
                irclib.sendChannelMessage("There is no alias '%s'." % (aliasString))



    def onChannelMessage(self, irclib, source, msg):
        try:
            if((len(msg.split()) > 0) and (msg.split()[0] == "clock")):
                if(self.isRefreshRunning):
                    irclib.sendChannelMessage("I'm busy updating the tables, don't bother me!")
                elif(len(msg.split()) > 1):
                    commandArguments = msg.split()[1:]
                    trailing = msg.split(None, 1)[1]
                    if(commandArguments[0] == "update"):
                        irclib.sendChannelMessage("Do I really have to? Oh well, this will take a while...")
                        self.doTimezoneRefresh()
                    elif(commandArguments[0] == "define"):
                        if((len(commandArguments) >= 4) and ("as" in commandArguments[2:])):
                            self.defineAlias(irclib, commandArguments[1:])
                        else:
                            irclib.sendChannelMessage("If you were trying to define a new alias, you forgot to tell me 'as' what to define it.")
                    elif((len(commandArguments) >= 3) and ("in" in commandArguments[1:])):
                        self.showTranslation(irclib, commandArguments[0:])
                    elif((len(commandArguments) >= 3) and (commandArguments[0] == "delete") and (commandArguments[1] == "alias")):
                        self.deleteAlias(irclib, commandArguments[2:])
                    elif((len(commandArguments) >= 3) and (commandArguments[0] == "display") and (commandArguments[1] == "alias")):
                        self.displayAlias(irclib, commandArguments[2:])
                    else:
                        self.showResult(irclib, commandArguments)
                else:
                    self.showResult(irclib, ["UTC"])
        except AliasLookupTooDeepError, exc:
            exc.aliases.reverse()
            irclib.sendChannelMessage("You're using too many aliases, that's confusing! (%s)" % ("->".join(exc.aliases)))
        except SubAliasNotFoundError, exc:
            exc.aliases.reverse()
            irclib.sendChannelMessage("An alias referenced a timezone that doesn't exist! (%s)" % ("->".join(exc.aliases)))



if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text

    c = ClockPlugin()
#    c.onChannelMessage(FakeIrcLib(), "source", "clock berl")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock delhi")
    c.onChannelMessage(FakeIrcLib(), "source", "clock t1")
    c.onChannelMessage(FakeIrcLib(), "source", "clock 10:00 New York in England")
    c.onChannelMessage(FakeIrcLib(), "source", "clock 25:00 in New York")
    c.onChannelMessage(FakeIrcLib(), "source", "clock Jerusalem")
    c.onChannelMessage(FakeIrcLib(), "source", "clock define Terralthra as San Francisco")
    c.onChannelMessage(FakeIrcLib(), "source", "clock define")
    c.onChannelMessage(FakeIrcLib(), "source", "clock Wurf")
    c.onChannelMessage(FakeIrcLib(), "source", "clock display alias terr")
    c.onChannelMessage(FakeIrcLib(), "source", "clock define terr as UTC")
    c.onChannelMessage(FakeIrcLib(), "source", "clock define abc as UTC")
    c.onChannelMessage(FakeIrcLib(), "source", "clock define def as abc")
    c.onChannelMessage(FakeIrcLib(), "source", "clock delete alias Cortex")
    c.onChannelMessage(FakeIrcLib(), "source", "clock display alias abc")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock define test1 as UTC")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock define test2 as test1")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock define test3 as test2")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock define test4 as test3")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock define UTC as UTC")
    c.onChannelMessage(FakeIrcLib(), "source", "clock test4")
    c.onChannelMessage(FakeIrcLib(), "source", "clock test3")
    c.onChannelMessage(FakeIrcLib(), "source", "clock test2")
    c.onChannelMessage(FakeIrcLib(), "source", "clock test1")
    c.onChannelMessage(FakeIrcLib(), "source", "clock display alias Z")
    c.onChannelMessage(FakeIrcLib(), "source", "clock Z")
    
#    c.onChannelMessage(FakeIrcLib(), "source", "clock Wurf")
    #print "findZone: |%s|" % (c.findZone("clock Abidjan, Cote d'Ivoire (Ivory Coast)"))
    #c.onChannelMessage(FakeIrcLib(), "source", "clock Abi")
    #c.onChannelMessage(FakeIrcLib(), "source", "clock +0300")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock define Tuebingen, Baden-Wuerttemberg, Germany as Berlin")
#    c.onChannelMessage(FakeIrcLib(), "source", "clock Tuebingen")
    #c.isRefreshRunning = True
    #c.refreshTimezones()
    #print c.normaliseOffset("+3")
    #print c.normaliseOffset("-4:30")
    #print c.normaliseOffset("-13")
    #c.onChannelMessage(FakeIrcLib(), "source", "clock update")
    

      #t.listAll()
#     print t.getTime("EDT")
#     print t.getTime("bERL")
#     print t.getTime("+5")
#     print t.getTime("aaaaa")
