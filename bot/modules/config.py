"""Configuration file

This file handles the basic (and only) configuration file
for RTBot. Edit this file to change:
	* the IRC server to connect to
	* the IRC server port
	* the channel to join (with an optional password)
	* the bot's nick, username, realname
	* the optional database connection for exception handling
	* the optional webservice host and port.

All the rest is conveniently hardcoded into RTBot's code,
including:

	In BotManager.py:
	* the plugin hot-updater refresh interval (startModificationsTimer)

	In IrcLib.py:
	* the timeout between messages (global)
	* trusted channels (sendChannelMessage)
	* RTBot's colour code 10 (sendChannelMessage)

"""

class Settings:
    """Settings storage
    
    This class handles the basic (and only) configuration file
    for RTBot.
    
    See documentation of config.py for detailed information.
    """
    # The IRC server to connect to.
    server = "de.quakenet.org"

    # The port used by the IRC server. (The default port is 6667, but some server hosts block this port.)
    port = 6668

    # The channel to connect to. It SHOULD be possible to join passworded rooms like this: channel = "#channel password"
    channel = "#RollingThunder.development"

    # The nickname, username and realname to use (for WHOIS).
    nickname = "RTBotTest"
    username = "rtbottest"
    realname = "RTBotTest"

    # The database connection (currently used to log exceptions for the webapp)
    database_connection_string = None    #"mysql://root@localhost/rtbotadmin"

    # The host and port of the webservice or "None" to deactivate the webservice.
    webservice_host = None      #"tufer.de"
    webservice_port = None      #8000
