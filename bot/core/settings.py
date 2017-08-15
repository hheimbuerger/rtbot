"""Configuration file

This file handles the basic (and only) configuration file
for RTBot. Edit this file to change:
	* the Discord token
"""

import os

discord_token = os.environ.get('DISCORD_TOKEN')
if not discord_token:
    raise RuntimeError('Configuration problem: DISCORD_TOKEN envvar must be set to bot token')
