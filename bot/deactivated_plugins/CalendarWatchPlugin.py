import re
import string
import httplib
import xml.dom.minidom



class WrongCalendarDataVersionError(Exception):
    pass



class CalendarWatchPlugin:

    def __init__(self):
        #self.pluginInterface = pluginInterface
        self.calendarSource = {"host": "www.teamportal.net", "url": "/RollingThunder/XML/calendar.php"}
        self.expectedVersion = "1"
        self.currentEventList = []
   
    def getVersionInformation(self):
        return("$Id: CalendarWatchPlugin.py 199 2006-03-25 23:10:53Z cortex $")
  
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
        for item in calendar_items:
            calendarItem = {}
            calendarItem["id"] = item.getElementsByTagName("id")[0].firstChild.data
            calendarItem["event"] = item.getElementsByTagName("event")[0].firstChild.data
            calendarItem["date"] = item.getElementsByTagName("date")[0].firstChild.data
            calendarItem["info"] = item.getElementsByTagName("info")[0].firstChild.data
            calendarItem["info"] = calendarItem["info"].replace("\n\n", "\n")
            calendarItem["info"] = calendarItem["info"].replace("\n", " ")
            calendarItemList.append(calendarItem)
        return(calendarItemList)

    def onChannelMessage(self, irclib, source, message):
        if(message == "calendar /debug"):
            try:
                list = self.getCalendarItemList()
                for item in list:
                    irclib.sendChannelMessage("%s %s: %s" % (item["date"], item["info"], item["event"]))
            except WrongCalendarDataVersionError, exc:
                irclib.sendChannelMessage(exc.args[0])





if __name__ == "__main__":
    class FakeIrcLib:
        def sendPrivateMessage(self, target, text):
            print text
        def sendChannelMessage(self, text):
            print text
    
    a = CalendarWatchPlugin()
    a.onChannelMessage(FakeIrcLib(), "source", "calendar /debug")

