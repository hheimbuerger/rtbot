"""Configuration file

This file handles the basic (and only) configuration file
for RTBot. Edit this file to change:
    * the Discord token
"""

import os

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    raise RuntimeError('Configuration error: DISCORD_TOKEN envvar must be set to bot token')

MAIN_CHANNEL_NAME = os.environ.get('MAIN_CHANNEL_NAME', '#rtbot-development')
if not MAIN_CHANNEL_NAME.startswith('#'):
    raise RuntimeError('Configuration error: MAIN_CHANNEL_NAME must be a full channel name starting with a # sign')
