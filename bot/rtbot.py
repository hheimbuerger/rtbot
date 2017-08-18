#!/usr/bin/python

"""RTBot

RTBot is a IRC^h^h^hDiscord bot unlike many others. It has been originally
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

import logging

from core import settings
from core.client import RTBotClient
from core.plugin_interface import PluginInterface


# initialize logging
logging.basicConfig(level=logging.INFO)

# initialize plugin interface
plugin_interface = PluginInterface('plugins/')

# create Discord client
client = RTBotClient(plugin_interface=plugin_interface)

# initialize plugins
plugin_interface.registerInformTarget(client)
plugin_interface.updatePlugins(False)

# run the event loop until (external) termination
client.obey_humans_forever()   # blocking call, will never return
