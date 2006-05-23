import os, threading, time, logging
from modules import IrcLib, RTBot, Log, config, PluginInterface, util, WebService
from lib import daemonize

class BotManager:
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
            raise Exception("Unsupported action sent to controller_IRCLibrary: %s" % action)

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
            raise Exception("Unsupported action sent to controller_PluginInterface: %s" % action)

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
            raise Exception("Unsupported action sent to controller_BotCore: %s" % action)

    def controller_Plugins(self, action):
        if(action == "start"):
            logging.info("Loading plugins...")
            self.pluginInterface.updatePlugins(False)
        elif(action == "stop"):
            pass
        else:
            raise Exception("Unsupported action sent to controller_Plugins: %s" % action)

    def controller_ModificationsTimer(self, action):
        if(action == "start"):
            logging.info("Starting to check for changed plugins every X seconds...")
            self.modificationsTimerLock = threading.RLock()
            self.startModificationsTimer()
        elif(action == "stop"):
            logging.info("Stopping checking for changed plugins...")
            self.modificationsTimer.cancel()
            self.modificationsTimer = None
        else:
            raise Exception("Unsupported action sent to controller_ModificationsTimer: %s" % action)

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

    @util.withMemberLock("modificationsTimerLock", False) # If we can't lock, then we're shutting down - do nothing
    def checkForModifications(self):
        self.pluginInterface.updatePlugins()
        
        # Restart the timer
        self.startModificationsTimer()





if __name__ == "__main__":
    if(os.name == 'posix'):
        daemonize.startstop(stdout='/tmp/rtbot.log',
                            stderr='/tmp/rtbot_err.log',
                            pidfile='/tmp/rtbot.pid')
    botManager = BotManager()
    botManager.run()
