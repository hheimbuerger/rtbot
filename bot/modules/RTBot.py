#! /usr/bin/env python
import sys, re, random, time, threading, string
import util, logging


class RTBot:
    pluginTimerTimeout = 10.0

    def __init__(self, library, channelname, pluginInterface):
        self.irclib = library
        logging.debug("Initialized")
        self.channelname = channelname
        self.pluginInterface = pluginInterface
        self.genericPluginTimerLock = threading.RLock()
        self.storedPluginErrors = []
        self.storedRemovedPluginsDuringLoad = []

    @util.withMemberLock("genericPluginTimerLock")
    def dispose(self):
        self.genericPluginTimer.cancel()
        pass
    
    # If we can't lock, then we're shutting down - do nothing
    @util.withMemberLock("genericPluginTimerLock", False)
    def genericPluginTimerEvent(self):
        self.pluginInterface.fireEvent("onTimer", self.irclib)
        self.startOrRestartTimer()
        
    def startOrRestartTimer(self):
        self.genericPluginTimer = threading.Timer(self.pluginTimerTimeout, self.genericPluginTimerEvent)
        self.genericPluginTimer.start()

#    def prepareRefresh(self):
#        self.irclib.sendEmote("sees a tac scout boosting by... and another one! Weird, it looked just the same...")

    #---------------------------------------------------------------------------------
    #                      EVENTS FROM PLUGIN INTERFACE
    #---------------------------------------------------------------------------------

    def informPluginChanges(self, loadedPluginsList, reloadedPluginsList, removedPluginsList, notLoadedDueToMissingDependenciesPluginsList):
        if(self.irclib.channel != None):
            if(len(loadedPluginsList) > 0):
                self.irclib.sendChannelMessage("Plugins loaded: " + string.join(loadedPluginsList, ", "))
            if(len(reloadedPluginsList) > 0):
                self.irclib.sendChannelMessage("Plugins updated: " + string.join(reloadedPluginsList, ", "))
            if(len(removedPluginsList) > 0):
                self.irclib.sendChannelMessage("Plugins removed: " + string.join(removedPluginsList, ", "))
            if(len(notLoadedDueToMissingDependenciesPluginsList) > 0):
                self.irclib.sendChannelMessage("Plugin files that could not be loaded due to missing dependencies: " + string.join(notLoadedDueToMissingDependenciesPluginsList, ", "))

    def informErrorRemovedPlugin(self, plugin):
        if(self.irclib.channel == None):
            self.storedPluginErrors.append(plugin)
        else:
            self.irclib.sendChannelMessage("Plugin caused an error and has been removed: " + plugin)

    def informRemovedPluginDuringLoad(self, pluginfile):
        if(self.irclib.channel == None):
            self.storedRemovedPluginsDuringLoad.append(pluginfile)
        else:
            self.irclib.sendChannelMessage("Plugin file caused an error during load, loading aborted: " + pluginfile)

    #---------------------------------------------------------------------------------
    #                            EVENTS FROM IRCLIB
    #---------------------------------------------------------------------------------
    
    def onConnected(self):
        logging.debug("connected")
        self.irclib.sendPrivateMessage("Q@CServe.quakenet.org", "AUTH RTBot2 9wPfgFiH")
        self.irclib.joinChannel(self.channelname)

    def onJoinedChannel(self):
        # give your welcome message
        self.irclib.sendChannelMessage("Hello, I'm your friendly RT-bot!")
        
        # report plugin problems
        if(len(self.storedPluginErrors) > 0):
            self.irclib.sendChannelMessage("The following plugins have caused an error while connecting and have been removed: " + string.join(self.storedPluginErrors, ", "))
            self.storedPluginErrors = []
        if(len(self.storedRemovedPluginsDuringLoad) > 0):
            self.irclib.sendChannelMessage("The following plugin files have caused an error during load while connecting and have been removed: " + string.join(self.storedRemovedPluginsDuringLoad, ", "))
            self.storedRemovedPluginsDuringLoad = []
            
        # start timer
        self.startOrRestartTimer()

    def onLeave(self, source, channel, reason):
        logging.info("* " + source + " left channel " + channel + " (reason: " + reason + ")")
        self.pluginInterface.fireEvent("onLeave", self.irclib, source)

    def onQuit(self, source, reason):
        logging.info("* Person left IRC: " + source + " (reason: " + reason + ")")
        self.pluginInterface.fireEvent("onQuit", self.irclib, source, reason)

    def onKick(self, source, target, reason, channel):
        logging.info("* %s was kicked by %s for %s" % (target, source, reason))
        self.pluginInterface.fireEvent("onKick", self.irclib, source, target, reason)

    def onChannelMode(self, source, flags, channel):
        logging.info("* Channel mode changed: %s-->%s: %s" % (source, channel, flags))
        self.pluginInterface.fireEvent("onChannelMode", self.irclib, source, flags)

    def onUserMode(self, source, targets, flags, channel):
        logging.info("* Mode changed: " + source + "-->" + str(targets) + "(" + channel + "): " + flags)
        self.pluginInterface.fireEvent("onUserMode", self.irclib, source, targets, flags)

    # somebody else joins
    def onJoin(self, source, channel):
        logging.info("* Person joined: " + source)
        self.pluginInterface.fireEvent("onJoin", self.irclib, source)

    def onKeyboardInterrupt(self):
        self.irclib.sendChannelEmote("has been sent away from the computer by the server admin -- grrr!")
        self.irclib.quit("'yr")

    def onChangeNick(self, source, target):
        logging.info("* Nick changed: " + source + "-->" + target)
        self.pluginInterface.fireEvent("onChangeNick", self.irclib, source, target)
#        self.deliverMessages(target)

    def onNotice(self, source, message):
        logging.info("incoming NOTICE: " + message)
        self.pluginInterface.fireEvent("onNotice", self.irclib, source, message)

    def onChannelMessage(self, source, message, channel):
        # ============= DEBUG ===============
        if(message == "list"):
            list = []
            for (name, data) in self.irclib.getUserList().userList.items():
                list.append((name, data.mode, data.id))
            self.irclib.sendChannelMessage(list)
            return
        logging.info(source + "-->#: " + message)
        self.pluginInterface.fireEvent("onChannelMessage", self.irclib, source, message)
        # ============= DEBUG ===============

    def onChannelEmote(self, source, emote):
        logging.info(source + "-->#: * " + emote)
        self.pluginInterface.fireEvent("onChannelEmote", self.irclib, source, emote)

    def onPrivateMessage(self, source, message):
        logging.info(source + "-->RTBot: " + message)
        self.pluginInterface.fireEvent("onPrivateMessage", self.irclib, source, message)
        if(message == "quit"):
            logging.debug("received 'quit'")
            self.irclib.sendChannelMessage("'go")
            self.irclib.sendChannelMessage("Ok guys, gotta go. See ya!")
            self.irclib.quit("'yr")

    def onPrivateEmote(self, source, emote):
        logging.info(source + "-->RTBot: * " + emote)
        self.pluginInterface.fireEvent("onPrivateEmote", self.irclib, source, emote)

    def onWhoResult(self, nick, user):
        logging.info("WHO %s: USERNAME=%s, HOST=%s, USERINFO=%s" % (nick, user.username, user.host, user.userinfo))
        self.pluginInterface.fireEvent("onWhoResult", self.irclib, nick, user)
        