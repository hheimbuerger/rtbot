'''
    This module is used to fork the current process into a daemon.
    Almost none of this is necessary (or advisable) if your daemon 
    is being started by inetd. In that case, stdin, stdout and stderr are 
    all set up for you to refer to the network connection, and the fork()s 
    and session manipulation should not be done (to avoid confusing inetd). 
    Only the chdir() and umask() steps remain as useful.
    References:
        UNIX Programming FAQ
            1.7 How do I get my program to act like a daemon?
                http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        Advanced Programming in the Unix Environment
            W. Richard Stevens, 1992, Addison-Wesley, ISBN 0-201-56317-7.

    History:
      2001/07/10 by Juergen Hermann
      2002/08/28 by Noah Spurrier
      2003/02/24 by Clark Evans
      
      http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
'''

import sys, os, threading, traceback, time, logging
from modules import IrcLib, RTBot, Log, config, PluginInterface, util, WebService
from signal import SIGTERM

def deamonize(stdout='/dev/null', stderr=None, stdin='/dev/null',
              pidfile=None, startmsg = 'started with pid %s' ):
    '''
        This forks the current process into a daemon.
        The stdin, stdout, and stderr arguments are file names that
        will be opened and be used to replace the standard file descriptors
        in sys.stdin, sys.stdout, and sys.stderr.
        These arguments are optional and default to /dev/null.
        Note that stderr is opened unbuffered, so
        if it shares a file with stdout then interleaved output
        may not appear in the order that you expect.
    '''
    # Do first fork.
    try: 
        pid = os.fork() 
        if pid > 0: sys.exit(0) # Exit first parent.
    except OSError, e: 
        sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)

    # Decouple from parent environment.
    #os.chdir("/") 
    os.umask(0) 
    os.setsid() 
    
    # Do second fork.
    try: 
        pid = os.fork() 
        if pid > 0: sys.exit(0) # Exit second parent.
    except OSError, e: 
        sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
        sys.exit(1)
    
    # Open file descriptors and print start message
    if not stderr: stderr = stdout
    si = file(stdin, 'r')
    so = file(stdout, 'a+')
    se = file(stderr, 'a+', 0)
    pid = str(os.getpid())
    sys.stderr.write("\n%s\n" % startmsg % pid)
    sys.stderr.flush()
    if pidfile: file(pidfile,'w+').write("%s\n" % pid)
    
    # Redirect standard file descriptors.
    os.dup2(si.fileno(), sys.stdin.fileno())
    #os.dup2(so.fileno(), sys.stdout.fileno())
    #os.dup2(se.fileno(), sys.stderr.fileno())

def startstop(stdout='/dev/null', stderr=None, stdin='/dev/null',
              pidfile='pid.txt', startmsg = 'started with pid %s' ):
    if len(sys.argv) > 1:
        action = sys.argv[1]
        try:
            pf  = file(pidfile,'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        if 'stop' == action or 'restart' == action:
            if not pid:
                mess = "Could not stop, pid file '%s' missing.\n"
                sys.stderr.write(mess % pidfile)
                sys.exit(1)
            try:
               while 1:
                   os.kill(pid,SIGTERM)
                   time.sleep(1)
            except OSError, err:
               err = str(err)
               if err.find("No such process") > 0:
                   os.remove(pidfile)
                   if 'stop' == action:
                       sys.exit(0)
                   action = 'start'
                   pid = None
               else:
                   print str(err)
                   sys.exit(1)
        if 'start' == action:
            if pid:
                mess = "Start aborded since pid file '%s' exists.\n"
                sys.stderr.write(mess % pidfile)
                sys.exit(1)
            deamonize(stdout,stderr,stdin,pidfile,startmsg)
            return
    print "usage: %s start|stop|restart" % sys.argv[0]
    sys.exit(2)





class BotManager:
    lastModificationTime = {}
    pluginsDirectory = "plugins"
    timeoutBeforeReconnecting = 60
    
    def __init__(self):
        logging.info("----------------------------------------------------------------------")
        logging.info("Starting up RTBot...")

        self.settings = config.Settings()

    def controller_IRCLibrary(self, action):
        if(action == "start"):
            logging.info("Loading IRC library...")
            self.irclib = IrcLib.LowlevelIrcLib()
            self.irclib.connect(self.settings.server, self.settings.port, self.settings.nickname, self.settings.username, self.settings.realname)
        elif(action == "stop"):
            logging.info("Disconnecting from IRC...")
            try:
                self.irclib.disconnect()
            except Exception, exc:
                logging.exception("Exception during irclib.disconnect()")
            self.irclib = None
        else:
            raise("NO ACTION SPECIFIED")

    def controller_PluginInterface(self, action):
        if(action == "start"):
            logging.info("Loading PluginInterface...")
            self.pluginInterface = PluginInterface.PluginInterface(self.pluginsDirectory)
        elif(action == "stop"):
            logging.info("Unloading PluginInterface...")
            try:
                self.pluginInterface.dispose()
            except Exception, exc:
                logging.exception("Exception during pluginInterface.dispose()")
            self.pluginInterface = None
        else:
            raise("NO ACTION SPECIFIED")

    def controller_BotCore(self, action):
        if(action == "start"):
            logging.info("Loading core bot code...")
            self.rtbot = RTBot.RTBot(self.irclib, self.settings.channel, self.pluginInterface)
            self.irclib.registerEventTarget(self.rtbot)
            self.pluginInterface.registerInformTarget(self.rtbot)
        elif(action == "stop"):
            logging.info("Unloading core bot code...")
            try:
                self.rtbot.dispose()
            except Exception, exc:
                logging.exception("Exception during rtbot.dispose()")
            self.rtbot = None
        else:
            raise("NO ACTION SPECIFIED")

    def controller_Plugins(self, action):
        if(action == "start"):
            logging.info("Loading plugins...")
            self.pluginInterface.updatePlugins(False)
        elif(action == "stop"):
            pass
        else:
            raise("NO ACTION SPECIFIED")

    def controller_ModificationsTimer(self, action):
        if(action == "start"):
            logging.info("Starting to check for changed plugins every X seconds...")
            self.modificationsTimerLock = threading.RLock()
            self.startModificationsTimer()
        elif(action == "stop"):
            logging.info("Stopping changed plugin check...")
            self.modificationsTimer.cancel()
            self.modificationsTimer = None
        else:
            raise("NO ACTION SPECIFIED")

    def controller_WebService(self, action):
        if(action == "start"):
            if(self.settings.webservice_host and self.settings.webservice_port):
                logging.info("Starting WebService...")
                self.webservice = WebService.WebService(self, self.settings.webservice_host, self.settings.webservice_port)
                self.webservice.start()
            else:
                logging.info("WebService deactivated...")
        elif(action == "stop"):
            logging.info("STOPPING WEBSERVICE NOT YET IMPLEMENTED!")
            self.webservice = None
        else:
            raise("NO ACTION SPECIFIED")

    def startup(self):
        self.controller_IRCLibrary("start")
        self.controller_PluginInterface("start")
        self.controller_BotCore("start")
        self.controller_Plugins("start")
        self.controller_ModificationsTimer("start")

    @util.withMemberLock("modificationsTimerLock")
    def shutdown(self):
        self.controller_ModificationsTimer("stop")
        self.controller_PluginInterface("stop")
        self.controller_BotCore("stop")
        self.controller_IRCLibrary("stop")

    def run(self):
        self.controller_WebService("start")
        
        logging.debug( "Entering main BotManager loop...")        

        while(True):
            logging.info("Trying to initialise bot...")
            try:
                self.startup()
            except IrcLib.ServerConnectionError, x:
                logging.exception("Exception: ServerConnectionError during connect!")
            else:
                try:
                    self.irclib.receiveDataLooped()        # receiveDataLooped() won't return unless the user requested a quit
                    break
                except IrcLib.ServerConnectionError, x:
                    logging.exception("Exception: ServerConnectionError in BotManager.run()")
                    # will try to reconnect
                except IrcLib.IrcError, x:
                    logging.exception("Exception: IrcError in BotManager.run()")
                    # will try to reconnect
                except Exception, x:
                    logging.exception("Exception: ")
                    self.irclib.sendChannelEmote("is confused and runs away panicking")
                    # will not try to reconnect
                    break

            # wait x seconds before reconnecting
            self.shutdown()
            time.sleep(self.timeoutBeforeReconnecting)

        logging.info("BotManager.run(): Destructing BotManager...")
        self.shutdown()
        logging.info("Thank you for using RTBot! 'yb")

        self.controller_WebService("stop")

    def startModificationsTimer(self):
        self.modificationsTimer = threading.Timer(10.0, self.checkForModifications)
        self.modificationsTimer.start()

    # If we can't lock, then we're shutting down - do nothing
    @util.withMemberLock("modificationsTimerLock", False)
    def checkForModifications(self):
        self.pluginInterface.updatePlugins()
        
        # Restart the timer
        self.startModificationsTimer()





if __name__ == "__main__":
    if(os.name == 'posix'):
        startstop(stdout='/tmp/rtbot.log',
                  stderr='/tmp/rtbot_err.log',
                  pidfile='/tmp/rtbot.pid')
    botManager = BotManager()
    botManager.run()
