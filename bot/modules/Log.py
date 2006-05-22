import datetime, sys, traceback, threading, os, logging, util
from lib.path import path
from config import Settings
from xml.dom.minidom import getDOMImplementation
if(Settings.database_connection_string):
    import sqlobject

"This file sets up the built-in python logging module"

rootlog = logging.getLogger('')

class XMLFormatter:
    "Handler for emitting exceptions to xml"
    def format(self, logrecord):
        # We only want exception records
        assert logrecord.exc_info
        exception = logrecord.exc_info[1]
        message = logrecord.msg % logrecord.args
        (type, exception, tb) = logrecord.exc_info
        formattedTraceback = traceback.format_exception(exception.__class__.__name__, exception, tb)
        
        impl = getDOMImplementation()
        newdoc = impl.createDocument(None, "rtbot-exception", None)
        elemRtbotException = newdoc.documentElement
        attrType = newdoc.createAttribute("type")
        attrType.nodeValue = str(type)
        elemRtbotException.setAttributeNode(attrType)
        attrMessage = newdoc.createAttribute("message")
        attrMessage.nodeValue = message
        elemRtbotException.setAttributeNode(attrMessage)
        elemTraceback = newdoc.createElement("traceback")
        textTraceback = newdoc.createTextNode("".join(formattedTraceback))
        elemTraceback.appendChild(textTraceback)
        elemRtbotException.appendChild(elemTraceback)
        
        return newdoc.toxml()

class ExceptionFilter:
    def filter(self, logrecord):
        if logrecord.exc_info:
            return True

class UniqueFileHandler(logging.Handler):
    "Emits each record to a unique file in specified directory"
    def __init__(self, basepath):
        logging.Handler.__init__(self)
        self.basepath = basepath
        self.recordCounter = 0
    def generateFilename(self):
        now = datetime.datetime.utcnow()
        self.recordCounter += 1
        return("exception_%.4i%.2i%.2i_%.2i%.2i%.2i_%.6i.xml" % (now.year, now.month, now.day, now.hour, now.minute, now.second, self.recordCounter))    
    def emit(self, record):
        stream = (self.basepath / self.generateFilename()).open("w")
        stream.write(self.format(record) + "\n")
        stream.close()

XMLEmitter = UniqueFileHandler(path("exceptions"))
XMLEmitter.setLevel(logging.ERROR)
XMLEmitter.addFilter(ExceptionFilter())
XMLEmitter.setFormatter(XMLFormatter())
rootlog.addHandler(XMLEmitter)

##          Handler that emits exceptions to a database

if(Settings.database_connection_string):
    class LoggedException(sqlobject.SQLObject):
        class sqlmeta:
            table = "exceptions"
        timestamp = sqlobject.DateTimeCol(default=datetime.datetime.utcnow)    # when did the exception get raised?
        exception_type = sqlobject.StringCol(length=255, varchar=True)         # what class is the exception of?
        meta_message = sqlobject.StringCol(length=255, varchar=True)           # what message did the bot code give?
        message = sqlobject.StringCol(length=255, varchar=True)                # what message did the runtime system give?
        traceback = sqlobject.StringCol()                                      # what's the stack trace? (multilined!)
        handled_by = sqlobject.IntCol(default=None)                            # who marked this exception as handled (not used by the bot)
        handled_when = sqlobject.DateTimeCol(default=None)                     # when was this exception marked as handled (not used by the bot)

    class DatabaseHandler(logging.Handler):
        def emit(self, logrecord):
            # We only want exception records
            assert logrecord.exc_info
            exception = logrecord.exc_info[1]
            message = logrecord.msg % logrecord.args
            (type, exception, tb) = logrecord.exc_info
            formattedTraceback = traceback.format_exception(exception.__class__.__name__, exception, tb)

            #LoggedException._connection.debug = True
            sqlobject.sqlhub.processConnection = sqlobject.connectionForURI(Settings.database_connection_string)
            exc = LoggedException(exception_type=str(exc_type), meta_message=message, message=str(exc_value), traceback=stringTraceback)
    
    DatabaseEmitter = DatabaseHandler()
    DatabaseEmitter.setLevel(logging.ERROR)
    DatabaseEmitter.addFilter(ExceptionFilter())
    rootlog.addHandler(DatabaseEmitter)

# Standard file logs
debuglog = logging.FileHandler(path("logs/debuglog.txt"))
debuglog.setLevel(logging.DEBUG)
debuglog.setFormatter(logging.Formatter("%(asctime)s %(message)s", "[UTC: %Y-%m-%d %H:%M:%S]"))
rootlog.addHandler(debuglog)

filelog = logging.FileHandler(path("logs/logfile.txt"))
filelog.setLevel(logging.INFO)
filelog.setFormatter(logging.Formatter("%(asctime)s %(message)s", "[UTC: %Y-%m-%d %H:%M:%S]"))
rootlog.addHandler(filelog)

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
console.setFormatter(logging.Formatter("%(asctime)s %(message)s", "[UTC: %Y-%m-%d %H:%M:%S]"))
# Uncomment this to receive verbose logging to console
#rootlog.addHandler(console)

rootlog.setLevel(logging.DEBUG)