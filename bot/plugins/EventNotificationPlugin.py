import httplib
import xml.dom.minidom
import datetime
import re



class WrongCalendarDataVersionError(Exception):
    pass

class WrongDateFormatError(Exception):
    pass



class EventNotificationPlugin:
    updateTimeoutSeconds = 60*60
    dateExtractionRE = "(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d) 00:00:00"
    infotextUnfoldingRE = "(?P<hour>\d\d)(?P<minute>\d\d) UTC(: (?P<info>.*))?"
    reminderTimeoutSeconds = [12*60*60, 6*60*60, 3*60*60, 2*60*60, 1*60*60, 45*60, 30*60, 15*60, 10*60, 5*60, 3*60, 60, 0]    # has to be ordered from longest time-delta to shortest time-delta
    detectionThreshold = 15

    def __init__(self):
        #self.pluginInterface = pluginInterface
        self.calendarSource = {"host": "www.teamportal.net", "url": "/RollingThunder/XML/calendar.php"}
        self.expectedVersion = "1"
        self.eventList = []
        self.updateEventList()
        self.lastUpdate = datetime.datetime.now()

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

    def updateEventList(self):
        calendarItemList = []
        (status, document, location) = self.getPage(self.calendarSource["host"], self.calendarSource["url"])
        dom = xml.dom.minidom.parseString(document)
        calendar_item_list = dom.getElementsByTagName("calendar-item-list")[0]
        dataVersion = calendar_item_list.getAttribute("version")
        if(dataVersion != self.expectedVersion):
            raise WrongCalendarDataVersionError("Wrong data version: expected %s, got %s." % (self.expectedVersion, dataVersion))
        calendar_items = calendar_item_list.getElementsByTagName("calendar-item")
        self.eventList = []
        for item in calendar_items:
            # determine id and event caption
            id = item.getElementsByTagName("id")[0].firstChild.data
            calendarItem = {}
            calendarItem["id"] = id
            calendarItem["event"] = item.getElementsByTagName("event")[0].firstChild.data
            
            # determine date
            dateExtractionResult = re.compile(EventNotificationPlugin.dateExtractionRE).match(item.getElementsByTagName("date")[0].firstChild.data)
            if(not dateExtractionResult):
                raise WrongDateFormatError("The date format couldn't be parsed!: '%s'" % (infoText))

            # determine info text
            infoText = item.getElementsByTagName("info")[0].firstChild.data
            infoText = infoText.replace("\n\n", "\n")
            infoText = infoText.replace("\n", " ")
            infotextUnfoldingResult = re.compile(EventNotificationPlugin.infotextUnfoldingRE).match(infoText)
            if(infotextUnfoldingResult):
                calendarItem["datetime"] = datetime.datetime(year = int(dateExtractionResult.group('year')),
                                                             month = int(dateExtractionResult.group('month')),
                                                             day = int(dateExtractionResult.group('day')),
                                                             hour = int(infotextUnfoldingResult.group('hour')),
                                                             minute = int(infotextUnfoldingResult.group('minute')))
                if(infotextUnfoldingResult.group('info')):
                    calendarItem["info"] = infotextUnfoldingResult.group('info')
                else:
                    calendarItem["info"] = "[no additional info]"
            else:
                calendarItem["datetime"] = datetime.datetime(year = int(dateExtractionResult.group('year')),
                                                             month = int(dateExtractionResult.group('month')),
                                                             day = int(dateExtractionResult.group('day')))
                calendarItem["info"] = infoText
                
            self.eventList.append(calendarItem)

        # DEBUG: TEST-EVENT
#===============================================================================
#        testEvent1 = {}
#        testEvent1["event"] = "TestEvent1"
#        testEvent1["info"] = "Just for debugging purposes!"
#        testEvent1["datetime"] = datetime.datetime.utcnow() + datetime.timedelta(seconds = 12*60*60+15)
#        self.eventList.append(testEvent1)
#        testEvent2 = {}
#        testEvent2["event"] = "TestEvent2"
#        testEvent2["info"] = "Just for debugging purposes!"
#        testEvent2["datetime"] = datetime.datetime.utcnow() + datetime.timedelta(seconds = 75)
#        self.eventList.append(testEvent2)
#        testEvent3 = {}
#        testEvent3["event"] = "TestEvent3"
#        testEvent3["info"] = "Just for debugging purposes!"
#        testEvent3["datetime"] = datetime.datetime.utcnow() + datetime.timedelta(seconds = 40)
#        self.eventList.append(testEvent3)
#===============================================================================
        
        # determine upcoming notifications
        for event in self.eventList:
            event["notifications"] = []
            now = datetime.datetime.utcnow()
            for notificationTriggerDelta in EventNotificationPlugin.reminderTimeoutSeconds:
                delta = datetime.timedelta(seconds = notificationTriggerDelta)
                if(event["datetime"]-delta > now):
                    notification = {"datetime": event["datetime"]-delta,
                                    "text": self.secondsToString(notificationTriggerDelta)}
                    event["notifications"].append(notification)

        # sort the list by date
        self.eventList.sort(cmp = lambda x,y: cmp(x["datetime"], y["datetime"]))
            
    def secondsToString(self, seconds):
        values = {}
        values["weeks"] = seconds / (60*60*24*7)
        values["days"] = (seconds % (60*60*24*7)) / (60*60*24)
        values["hours"] = (seconds % (60*60*24)) / (60*60)
        values["minutes"] = (seconds % (60*60)) / (60)
        values["seconds"] = (seconds % (60))
        
        if(seconds == 0):
            return("now")
        else:
            stringElements = []
            for magnitude in ["weeks", "days", "hours", "minutes", "seconds"]:
                if(values[magnitude] > 1): stringElements.append("%i %s" % (values[magnitude], magnitude))
                elif(values[magnitude] == 1): stringElements.append("1 %s" % (magnitude[:-1]))
            return("in " + ", ".join(stringElements))

    def showNextEvent(self, irclib):
        if(len(self.eventList) > 0):
            now = datetime.datetime.utcnow()
            for event in self.eventList:
                if(event["datetime"] > now):
                    timeToEvent = event["datetime"]-now
                    deltaSeconds = timeToEvent.days * 60*60*24 + timeToEvent.seconds
                    irclib.sendChannelMessage("Next upcoming event: %s (%s) %s" % (event["event"], event["info"], self.secondsToString(deltaSeconds)))
                    return
        else:
            irclib.sendChannelMessage("No scheduled events.")

    def listAllEvents(self, irclib):
        if(len(self.eventList) > 0):
            irclib.sendChannelMessage("Known events:")
            for event in self.eventList:
                irclib.sendChannelMessage("%s UTC: %s (%s)" % (str(event["datetime"]), event["event"], event["info"]))
        else:
            irclib.sendChannelMessage("No scheduled events.")

    def listUpcomingEvents(self, irclib):
        if(len(self.eventList) > 0):
            irclib.sendChannelMessage("Upcoming events:")
            now = datetime.datetime.utcnow()
            for event in self.eventList:
                if(event["datetime"] > now):
                    timeToEvent = event["datetime"]-now
                    deltaSeconds = timeToEvent.days * 60*60*24 + timeToEvent.seconds
                    irclib.sendChannelMessage("%s: %s (%s)" % (self.secondsToString(deltaSeconds), event["event"], event["info"]))
        else:
            irclib.sendChannelMessage("No scheduled events.")

    def onTimer(self, irclib):
        # update if necessary
        deltatime = datetime.datetime.now() - self.lastUpdate
        if((deltatime.days != 0) or (deltatime.seconds > EventNotificationPlugin.updateTimeoutSeconds)):
            self.updateEventList()
            self.lastUpdate = datetime.datetime.now()

        # notify if necessary
        now = datetime.datetime.utcnow()
#        for event in self.eventList:
#            deltaToEvent = event["datetime"]-now
#            secondsToEvent = deltaToEvent.days * 60*60*24 + deltaToEvent.seconds
#            for notificationTrigger in EventNotificationPlugin.reminderTimeoutSeconds:
#                if((secondsToEvent <= notificationTrigger) and (secondsToEvent > notificationTrigger-EventNotificationPlugin.detectionThreshold)):
#                    irclib.sendChannelMessage("ATTENTION: %s (%s) %s!" % (event["event"], event["info"], self.secondsToString(notificationTrigger)))
#                    break
        for event in self.eventList:
            while(len(event["notifications"]) > 0):
                if(event["notifications"][0]["datetime"] < now):
                    irclib.sendChannelMessage("ATTENTION: %s (%s) %s!" % (event["event"], event["info"], event["notifications"][0]["text"]))
                    del(event["notifications"][0])
                else:
                    break
    
    def onChannelMessage(self, irclib, source, message):
#        if(message == "calendar /debug"):
#            try:
#                list = self.getCalendarItemList()
#                for item in list:
#                    irclib.sendChannelMessage("%s: %s (%s)" % (item["date"], item["event"], item["info"]))
#            except WrongCalendarDataVersionError, exc:
#                irclib.sendChannelMessage(exc.args[0])
        if(message == "event next"):
            self.showNextEvent(irclib)
        elif(message == "event list"):
            self.listAllEvents(irclib)
        elif(message == "event upcoming"):
            self.listUpcomingEvents(irclib)





if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
    
    a = CalendarWatchPlugin()
    a.onChannelMessage(FakeIrcLib(), "source", "calendar /debug")

