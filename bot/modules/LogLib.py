import datetime, sys, traceback, threading, os
import util
LOGLVL_DEBUG = 0
LOGLVL_INFO = 1
LOGLVL_LOG = 2
LOGLVL_NONE = 3

class Logfile:
    def __init__(self, logfilelvl, debugfilelvl, stdoutlvl):
        self.fileLog = open(os.path.join("logs", "logfile.txt"), "a")
        self.fileError = open(os.path.join("logs", "debuglog.txt"), "a")
        self.logfilelvl = logfilelvl
        self.debugfilelvl = debugfilelvl
        self.stdoutlvl = stdoutlvl
        self.logLock = threading.RLock()

    @util.withMemberLock("logLock")
    def close(self):
        self.fileLog.close()
        self.fileError.close()
    
    # Logs an exception. Must be called from an exception handler
    # message should be a string saying something about what the calling code does
    @util.withMemberLock("logLock")
    def addException(self, message, exception):
        # Change this to LOGLVL_NONE to receive exceptions in the console - nice for debugging
        loglevel = LOGLVL_DEBUG
        self.add(loglevel, "Encountered exception: " + exception.__str__())
        self.add(loglevel, "Programmer's message: " + message)
        (type, value, tb) = sys.exc_info()
        result = traceback.format_exception(exception.__class__.__name__, exception, tb)
        self.add(loglevel, "".join(result).strip())        
    
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
