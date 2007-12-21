"""RTBot

RTBot is a IRC bot unlike many others. It has been originally
developed with three objectives in mind:

        1. Learn Python
        2. Make an amusing bot with an unique "personality"
        3. Attract loads of people to #RollingThunder at quakenet.org
        4. Conquer the world.

What started as a probably ugly hack developed into a less ugly hack
with lots of hardcoded special cases and magic expression on the one
side, and a polished and useful plugin system that allows to load,
unload and update plugins on the go.

RTBot makes heavy usage of dark art, a.k.a. regular expressions.
Some regual expression may not be suitable for the view of the
underage and the unwary -- nasty stuff! :-}

"""

import os, threading, time, logging
from modules import IrcLib, RTBot, Log, config, PluginInterface, util, WebService
from lib import daemonize

class BotManager:
        """BotManager

        BotManager is the main module that starts, restarts and updates
        RTBot.



        Starting and Stopping RTBot

        On Windows, starting the bot is achieved by simply running the script;
        a window will appear with debug information and closing it will close
        RTBot.

        On Linux, BotManager.py accepts one argument that ideally lets the
        bot behave like a daemon:

                BotManager.py <action>

                where:

                action  One of "start", "stop" or "restart".

        In practice, the Windows approach works just as well. With Bash, you
        can press Ctrl-Z and then type the "bg" command to have the bot run
        in the background of a text terminal; using "fg" from the same terminal
        will bring the bot's debug output back to the console, and from there
        one can terminate the bot with Ctrl-C. Sending the TERM signal is
        equally valid.

        There are more ways to stop the bot: some involve the web-application,
        some involve being logged in under the right "magic" username. Each
        method will resume in a different quit behaviour by the bot -- treat
        him good and it'll play it fine. :)

        How to treat him good is yet unexplained.
        """

        pluginsDirectory = "plugins"
        timeoutBeforeReconnecting = 60

        # -----------------------
        # PRIVATE
        # -----------------------
        
        def __init__(self):
                """Load RTBot

                Begins loading RTBot. Mostly a wrapper call.
                """
                self.status = "Loaded."
                logging.info("----------------------------------------------------------------------")
                logging.info("Starting up RTBot...")
                self.settings = config.Settings()

        def controller_IRCLibrary(self, action):
                """Start/Stop IRC connection.

                "start"s and "stop"s IrcLib's connection to the IRC network.
                Raises an exception if the action is not "start" or "stop".

                Internal use.
                """
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
                """Start/Stop Plugin System

                "start"s and "stop"s the plugin system.
                Raises an exception if the action is not "start" or "stop".

                Internal use.
                """
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
                """Initialise/Deinitialise RTBot's core code.

                "start"s and "stop"s RTBot's core code (?)
                Raises an exception if the action is not "start" or "stop".

                Internal use.
                """
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
                """Start/Stop RTBot's Plugins

                "start"s and "stop"s the individual plugins. Mostly a wrapper.
                Raises an exception if the action is not "start" or "stop".

                Internal use.
                """
                if(action == "start"):
                        logging.info("Loading plugins...")
                        self.pluginInterface.updatePlugins(False)
                elif(action == "stop"):
                        pass
                else:
                        raise Exception("Unsupported action sent to controller_Plugins: %s" % action)

        def controller_ModificationsTimer(self, action):
                """Start/Stop Plugin Hot-updating System

                "start"s and "stop"s the hot-updating system.
                Raises an exception if the action is not "start" or "stop".

                Internal use.
                """
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
                """Start/Stop WebService
                
                "start"s and "stop"s the web-application
                Raises an exception if the action is not "start" or "stop".
                
                Internal use.
                """

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
                        raise Exception("Unsupported action sent to controller_ModificationsTimer: %s" % action)

        def startup(self):
                """Start main RTBot modules.

                Starts all the main components of RTBot. In order:

                        1. the IRC library (handles the connection to the servers)
                        2. the plugin loading/unloading system
                        3. RTBot's core code
                        4. the plugins
                        5. the plugin hot-update system.

                Internal use.
                """
                self.controller_IRCLibrary("start")
                self.controller_PluginInterface("start")
                self.controller_BotCore("start")
                self.controller_Plugins("start")
                self.controller_ModificationsTimer("start")

        @util.withMemberLock("modificationsTimerLock")
        def shutdown(self):
                """Stop main RTBot modules.  

                Stops all the main components of RTBot.

                Internal use.
                """
                self.controller_ModificationsTimer("stop")
                self.controller_PluginInterface("stop")
                self.controller_BotCore("stop")
                self.controller_IRCLibrary("stop")

        def startModificationsTimer(self):
                """Create the timer for the hot-update system

                Starts the timer for the hot-update system.
                RTBot will check plugins every 10 seconds (hardcoded value).

                Internal use.
                """
                self.modificationsTimer = threading.Timer(10.0, self.checkForModifications)
                self.modificationsTimer.start()

        @util.withMemberLock("modificationsTimerLock", False) # If we can't lock, then we're shutting down - do nothing
        def checkForModifications(self):
                """Force an update of the plugin list.

                Starts the timer for the hot-update system.
                RTBot will check plugins every 10 seconds (hardcoded value).
                Decorated (requires a lock (?)).

                Internal use.
                """
                self.pluginInterface.updatePlugins()
                
                # Restart the timer
                self.startModificationsTimer()


                
        # -----------------------
        # PUBLIC
        # -----------------------

        def getState(self):
                """Returns RTBot's Status

                It can be one of the following:

                        1. "Launched." (Loading the web-applet. Connecting to IRC.)
                        2. "Connected." (Connected to IRC. Working.)

                        3. "Disconnected." (Preparing to unload the code.)
                        4. "Shutting down." (Unloading the modules.)
                        5. "Shut down." (Closing the web-applet.)

                Of course, each status is an hardcoded string.

                See also: run(self)
                """
                return(self.status)

        def run(self):
                """Main RTBot control

                Initialises the bot, starts the main loop, deinitialises the bot.
                """
                self.status = "Launched."
                self.controller_WebService("start")
                
                logging.debug( "Entering main BotManager loop...")              

                while(True):
                        logging.info("Trying to initialise bot...")
                        try:
                                self.startup()
                        except IrcLib.ServerConnectionError, x:
                                logging.exception("Exception: ServerConnectionError during connect!")
                        else:
                                self.status = "Connected."
                                try:
                                        self.irclib.receiveDataLooped()         # receiveDataLooped() won't return unless the user requested a quit
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
                        self.status = "Disconnected."
                        self.shutdown()
                        time.sleep(self.timeoutBeforeReconnecting)

                self.status = "Shutting down."
                logging.info("BotManager.run(): Destructing BotManager...")
                self.shutdown()
                logging.info("Thank you for using RTBot! 'yb")

                self.controller_WebService("stop")
                self.status = "Shut down."




if __name__ == "__main__":
        if(os.name == 'posix'):
                daemonize.startstop(stdout='logs/rtbot.log',
                        stderr='logs/rtbot_err.log',
                        pidfile='rtbot.pid')
        botManager = BotManager()
        botManager.run()
