import httplib
import xml.dom.minidom
import datetime
import re
import socket



class WrongCalendarDataVersionError(Exception):
    pass

class WrongDateFormatError(Exception):
    pass



class EventNotificationPlugin:
    updateTimeoutSeconds = 60*60
    reminderTimeoutSeconds = [12*60*60, 6*60*60, 3*60*60, 2*60*60, 1*60*60, 45*60, 30*60, 15*60, 10*60, 5*60, 3*60, 60, 0]    # has to be ordered from longest time-delta to shortest time-delta
    detectionThreshold = 15
    datetimeFormat = "%d %b %Y %H:%M UTC"

    dateExtractionRE = "(?P<year>\d\d\d\d)-(?P<month>\d\d)-(?P<day>\d\d) 00:00:00"
    infotextUnfoldingRE = "(?P<hour>\d\d)(?P<minute>\d\d) UTC(: (?P<info>.*))?"
    eventThreadURLExtractionRE = "^(?P<prologue>.*?)\[url=(?P<url>.*?)\](?P<caption>.*?)\[\/url\](?P<epilogue>.*)$"
    topicEventSplitterL = "|-"
    topicEventSplitterR = "-|"
    channelTopicSplittingRE = "^(?P<prologue>.*?)" + re.escape(topicEventSplitterL) + "(?P<currentEvent>.*?)" + re.escape(topicEventSplitterR) + "(?P<epilogue>.*?)$"



    def __init__(self):
        #self.pluginInterface = pluginInterface
        self.calendarSource = {"host": "www.teamportal.net", "url": "/RollingThunder/XML/calendar.php"}
        self.expectedVersion = "1"
        self.eventList = []
        self.lastUpdate = None
        self.channelTopicUpdateScheduled = True



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



    def updateEventList(self, irclib):
        try:
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
                infoTextInputData = item.getElementsByTagName("info")[0].firstChild.data
                #infoText = infoTextInputData.replace("\n\n", "\n")
                #infoText = infoText.replace("\n", " ")
                infoTextLines = infoTextInputData.split("\n")
                if(len(infoTextLines) > 1):
                    infoText = infoTextLines[0] + " -- more information: http://www.teamportal.net/RollingThunder/modules.php?name=Forums&file=viewtopic&t=%s" % (id)
                elif(len(infoTextLines) == 1):
                    infoText = infoTextLines[0]
                else:
                    infoText = "[no information available]"

                linkExtractionResult = re.compile(EventNotificationPlugin.eventThreadURLExtractionRE, re.DOTALL).match(infoText)
                if(linkExtractionResult):
                    calendarItem["threadUrl"] = linkExtractionResult.group('url')
                    infoText = linkExtractionResult.group('prologue') + linkExtractionResult.group('caption') + linkExtractionResult.group('epilogue')
                
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
                        calendarItem["info"] = "no additional info"
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
            
            # trigger channel topic update
            self.channelTopicUpdateScheduled = True
        except socket.error, exc:
            irclib.sendChannelMessage("WARNING: EventNotificationPlugin couldn't retrieve events, presumably the website is down. Error message: '%s'" % (exc.args[1]))



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
            return("in " + ", ".join(stringElements[:2]))



    def getNextEvent(self):
        if(len(self.eventList) > 0):
            now = datetime.datetime.utcnow()
            for event in self.eventList:
                if(event["datetime"] > now):
                    return(event)
        else:
            return(None)



    def showEventLinks(self, irclib, event):
        irclib.sendChannelMessage("Event link to #%s: http://www.teamportal.net/RollingThunder/modules.php?name=Forums&file=viewtopic&t=%s" % (event["id"], event["id"]))
        if(event.has_key("threadUrl")):
            irclib.sendChannelMessage("Forum link to #%s: %s" % (event["id"], event["threadUrl"]))
        else:
            irclib.sendChannelMessage("No forum link available.")



    def showNextEvent(self, irclib):
        nextEvent = self.getNextEvent()
        if(nextEvent):
            now = datetime.datetime.utcnow()
            timeToEvent = nextEvent["datetime"]-now
            deltaSeconds = timeToEvent.days * 60*60*24 + timeToEvent.seconds
            irclib.sendChannelMessage("Next upcoming event: %s (%s) %s" % (nextEvent["event"], nextEvent["info"], self.secondsToString(deltaSeconds)))
            self.showEventLinks(irclib, nextEvent)
        else:
            irclib.sendChannelMessage("No scheduled events.")



    def listAllEvents(self, irclib):
        if(len(self.eventList) > 0):
            irclib.sendChannelMessage("Known events:")
            for event in self.eventList:
                irclib.sendChannelMessage("%s: %s (%s) [#%s]" % (event["datetime"].strftime(EventNotificationPlugin.datetimeFormat), event["event"], event["info"], event["id"]))
        else:
            irclib.sendChannelMessage("No scheduled events.")



    def listUpcomingEvents(self, irclib, numEvents = 0):
        if(len(self.eventList) > 0):
            irclib.sendChannelMessage("Upcoming events:")
            now = datetime.datetime.utcnow()
            for event in self.eventList:
                if(event["datetime"] > now):
                    timeToEvent = event["datetime"]-now
                    deltaSeconds = timeToEvent.days * 60*60*24 + timeToEvent.seconds
                    irclib.sendChannelMessage("%s: %s (%s) [#%s]" % (self.secondsToString(deltaSeconds), event["event"], event["info"], event["id"]))
                    if(numEvents == 1):
                        break
                    numEvents -= 1
        else:
            irclib.sendChannelMessage("No scheduled events.")



    def updateChannelTopicIfNecessary(self, irclib):
        # expand the current channel topic
        if(irclib.channelTopic):
            reResult = re.compile(EventNotificationPlugin.channelTopicSplittingRE).match(irclib.channelTopic)
            if(reResult):
                prologue = reResult.group("prologue")
                currentEvent = reResult.group("currentEvent")
                epilogue = reResult.group("epilogue")

                # generate the event text
                nextEvent = self.getNextEvent()
                if(nextEvent):
                    eventText = " Next event: %s on %s " % (nextEvent["event"], nextEvent["datetime"].strftime(EventNotificationPlugin.datetimeFormat))
                else:
                    eventText = " No scheduled event."
                
                # if the event text isn't already there, update the channel topic
                if(currentEvent != eventText):
                    newChannelTopic = "%s%s%s%s%s" % (prologue, EventNotificationPlugin.topicEventSplitterL, eventText, EventNotificationPlugin.topicEventSplitterR, epilogue)
                    irclib.setChannelTopic(newChannelTopic)

            # this has been handled now
            self.channelTopicUpdateScheduled = False                



    def onChannelTopicChange(self, irclib, source, newTopic):
        self.updateChannelTopicIfNecessary(irclib)



    def onTimer(self, irclib):
        # update if necessary
        if(self.lastUpdate):
            deltatime = datetime.datetime.now() - self.lastUpdate
        if((not self.lastUpdate) or (deltatime.days != 0) or (deltatime.seconds > EventNotificationPlugin.updateTimeoutSeconds)):
            self.updateEventList(irclib)
            self.lastUpdate = datetime.datetime.now()

        # notify if necessary
        now = datetime.datetime.utcnow()
        for event in self.eventList:
            while(len(event["notifications"]) > 0):
                if(event["notifications"][0]["datetime"] < now):
                    irclib.sendChannelMessage("ATTENTION: %s (%s) %s!" % (event["event"], event["info"], event["notifications"][0]["text"]))
                    del(event["notifications"][0])
                else:
                    break

            if(len(event["notifications"]) == 0):
                self.channelTopicUpdateScheduled = True
                
        if(self.channelTopicUpdateScheduled):
            self.updateChannelTopicIfNecessary(irclib)


    
    def onChannelMessage(self, irclib, source, message):
        if((len(message.split()) >= 2) and (message.split()[0:2] == ["event", "next"])):
            if(len(message.split()) >= 3):
                try:
                    self.listUpcomingEvents(irclib, int(message.split()[2]))
                except ValueError:
                    self.showNextEvent(irclib)
            else:
                self.showNextEvent(irclib)
        elif(message == "event list"):
            self.listAllEvents(irclib)
        elif(message == "event upcoming"):
            self.listUpcomingEvents(irclib)
        elif(message == "event trigger update"):
            irclib.sendChannelEmote("updates the event list...")
            self.updateEventList(irclib)
        elif((len(message.split()) >= 3) and (message.split()[0:2] == ["event", "links"])):
            eventId = message.split()[2]
            for event in self.eventList:
                if(event["id"] == eventId):
                    self.showEventLinks(irclib, event)
                    break





if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
    
    a = CalendarWatchPlugin()
    a.onChannelMessage(FakeIrcLib(), "source", "calendar /debug")

