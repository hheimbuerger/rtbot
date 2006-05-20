import datetime, sys, traceback, threading, os
from config import Settings
import util
from xml.dom.minidom import getDOMImplementation
if(Settings.database_connection_string):
    from sqlobject import *

LOGLVL_DEBUG = 0
LOGLVL_INFO = 1
LOGLVL_LOG = 2
LOGLVL_NONE = 3



if(Settings.database_connection_string):
    class LoggedException(SQLObject):
        class sqlmeta:
            table = "exceptions"
        timestamp = DateTimeCol(default=datetime.datetime.utcnow)
        type = StringCol(length=255, varchar=True)
        message = StringCol(length=255, varchar=True)
        traceback = StringCol()
        handled_by = IntCol(default=None)
        handled_when = DateTimeCol(default=None)


class Logfile:
    
    def __init__(self, logfilelvl, debugfilelvl, stdoutlvl):
        self.fileLog = open(os.path.join("logs", "logfile.txt"), "a")
        self.fileError = open(os.path.join("logs", "debuglog.txt"), "a")
        self.logfilelvl = logfilelvl
        self.debugfilelvl = debugfilelvl
        self.stdoutlvl = stdoutlvl
        self.logLock = threading.RLock()
        self.exceptionCounter = 0

    @util.withMemberLock("logLock")
    def close(self):
        self.fileLog.close()
        self.fileError.close()
        
    def generateFilename(self):
        now = datetime.datetime.utcnow()
        self.exceptionCounter += 1
        return("exception_%.4i%.2i%.2i_%.2i%.2i%.2i_%.6i.xml" % (now.year, now.month, now.day, now.hour, now.minute, now.second, self.exceptionCounter))
    
    # Logs an exception. Must be called from an exception handler
    # message should be a string saying something about what the calling code does
    @util.withMemberLock("logLock")
    def addException(self, message, exception):
        # Change this to LOGLVL_NONE to receive exceptions in the console - nice for debugging
        loglevel = LOGLVL_DEBUG
        self.add(loglevel, "Encountered exception: " + exception.__str__())
        self.add(loglevel, "Programmer's message: " + message)
        (type, value, tb) = sys.exc_info()        #type="exceptions.ZeroDevisionError, value="integer division or modulo by zero", tb=<traceback object>
        formattedTraceback = traceback.format_exception(exception.__class__.__name__, exception, tb)
        self.add(loglevel, "".join(formattedTraceback).strip())
#        print "traceback:"
#        self.subprint(tb, 1)
        
        # Export the exception to /exceptions (in particular to be able to read it from the webapp)
        impl = getDOMImplementation()
        newdoc = impl.createDocument(None, "rtbot-exception", None)
        elemRtbotException = newdoc.documentElement
        attrType = newdoc.createAttribute("type")
        attrType.nodeValue = str(type)
        elemRtbotException.setAttributeNode(attrType)
        attrMessage = newdoc.createAttribute("message")
        attrMessage.nodeValue = str(value)
        elemRtbotException.setAttributeNode(attrMessage)
        elemTraceback = newdoc.createElement("traceback")
        textTraceback = newdoc.createTextNode("".join(formattedTraceback))
        elemTraceback.appendChild(textTraceback)
        elemRtbotException.appendChild(elemTraceback)
        file = open(os.path.join("exceptions", self.generateFilename()), "w")
        newdoc.writexml(file, indent="", addindent="  ", newl="\n")
        file.close()

        # Open database connection and post the exception
        if(Settings.database_connection_string):
            sqlhub.processConnection = connectionForURI(Settings.database_connection_string)
            #LoggedException._connection.debug = True
            exc = LoggedException(type=type, message=message, traceback=traceback)



    # Adds a message to the log. Message can be multiple lines, and is then split up
    @util.withMemberLock("logLock")
    def add(self, lvl, message):
        time = datetime.datetime.utcnow()
        formattedTime = time.strftime("%Y-%m-%d %H:%M:%S")
        for line in message.splitlines():
            formattedMessage = "[UTC: " + formattedTime + "] " + line
            if(lvl >= self.logfilelvl):
                self.fileLog.write(formattedMessage + "\n")
                self.fileLog.flush()
            if(lvl >= self.debugfilelvl):
                self.fileError.write(formattedMessage + "\n")
                self.fileError.flush()
            if(lvl >= self.stdoutlvl):
                print formattedMessage

log = Logfile(LOGLVL_LOG, LOGLVL_DEBUG, LOGLVL_NONE)
