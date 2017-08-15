import collections

import discord
import asyncio

from core.decorators import deprecated


user_data_store = collections.defaultdict(dict)


class User:   # TODO: this should be extracted into a separate module
    def __init__(self, author):
        self.author = author

    #@deprecated
    def getCanonicalNick(self):
        return self.author

    @property
    def dataStore(self):
        return user_data_store[self.author]


class MessageContext:   # TODO: this should be extracted into a separate module
    def __init__(self, client, message):
        self.client = client
        self.channel = message.channel
        self.author = message.author
        self.content = message.content

    async def reply(self, content):
        await self.client.send_message(self.channel, content)

    async def emote(self, content):
        await self.client.send_message('_{}_'.format(content))

    async def get_channel_users(self):
        raise NotImplementedError('does anyone need this?')


class RTBotClient(discord.Client):

    MAIN_CHANNEL_NAME = '#rtbot-development'

    def __init__(self, plugin_interface, discord_token):
        super(RTBotClient, self).__init__()
        self.plugin_interface = plugin_interface
        self.discord_token = discord_token

    def _determine_main_channel(self):
        for channel in self.get_all_channels():
            print(channel.name)
            if channel.name == self.MAIN_CHANNEL_NAME[1:]:
                self.main_channel = channel

    async def on_timer(self):
        await self.wait_until_ready()
        counter = 0
        #channel = discord.Object(id='channel_id_here')
        while not self.is_closed:
            counter += 1
            #await self.send_message(channel, counter)
            #print('beep')
            await asyncio.sleep(10) # task runs every 60 seconds

    async def on_message(self, message):
        #print('Servers: ' + str(list(self.servers)))
        print('Channels: ' + str(list(self.private_channels)))
        print('MSG: ', message.id, message.server, message.channel, message.author, message.timestamp, message.content)
        #print('---')
        if message.author != self.user:
            await self.plugin_interface.fireEvent("on_message", MessageContext(self, message), User(message.author), message.content)

    async def on_ready(self):
        self._determine_main_channel()

        await self.send_message(self.main_channel, 'I\'m ready! (Is this my new home?)')

        print('Logged in as: ' + self.user.name)
        print('ID: ' + self.user.id)
        print('User: ' + str(self.user))
        print('Servers: ' + str(list(self.servers)))
        print('Channels: ' + str(list(self.private_channels)))
        print('Email: ' + str(self.email))
        print('------')

    def informPluginChanges(self, loadedPluginsList, reloadedPluginsList, removedPluginsList, notLoadedDueToMissingDependenciesPluginsList):   # TODO: temporary hack
        if len(loadedPluginsList) > 0:
            print("Plugins loaded: " + str.join(loadedPluginsList, ", "))
        if len(reloadedPluginsList) > 0:
            print("Plugins updated: " + str.join(reloadedPluginsList, ", "))
        if len(removedPluginsList) > 0:
            print("Plugins removed: " + str.join(removedPluginsList, ", "))
        if len(notLoadedDueToMissingDependenciesPluginsList) > 0:
            print("Plugin files that could not be loaded due to missing dependencies: " + str.join(notLoadedDueToMissingDependenciesPluginsList, ", "))

    def informErrorRemovedPlugin(self, plugin):   # TODO: temporary hack
        print("Plugin caused an error and has been removed: " + plugin)

    def informRemovedPluginDuringLoad(self, pluginfile):   # TODO: temporary hack
        print("Plugin file caused an error during load, loading aborted: " + pluginfile)

    def obey_humans_forever(self):
        self.loop.create_task(self.on_timer())
        self.run(self.discord_token)
