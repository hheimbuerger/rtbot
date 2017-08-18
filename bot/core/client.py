import collections

import discord
import asyncio

from core import settings
from core.decorators import deprecated


user_data_store = collections.defaultdict(dict)


class User:   # TODO: this should be extracted into a separate module
    def __init__(self, client, raw_message):
        self.client = client
        self.raw_user = raw_message.author

    @property
    def id(self):
        return self.raw_user.id

    @property
    def name(self):
        return self.raw_user.name

    @property
    def is_admin(self):
        return True

    @property
    def data_store(self):
        return user_data_store[self.raw_user.id]

    def __str__(self):
        return 'User {name}#{id}'.format(id=self.id, name=self.name)


class Channel:   # TODO: this should be extracted into a separate module
    def __init__(self, client, raw_message):
        self.client = client
        self.raw_channel = raw_message.channel

    @property
    def name(self):
        return self.raw_channel.name

    @property
    def is_private(self):
        return self.raw_channel.is_private

    async def reply(self, message):
        await self.client.dispatch_message(self, message)

    async def get_channel_users(self):
        raise NotImplementedError('does anyone need this?')

    def __str__(self):
        return 'Channel #{name}'.format(name=self.name)


class PluginContext:
    def __init__(self, client):
        self.client = client

    async def dispatch_message(self, target, content):
        await self.client.dispatch_message(target, content)


class RTBotClient(discord.Client):

    def __init__(self, plugin_interface):
        super(RTBotClient, self).__init__()
        self.plugin_interface = plugin_interface
        self.plugin_context = PluginContext(self)

        # FIXME: not the right way to inject a dependency
        self.plugin_interface.pluginContext = self.plugin_context

    def _determine_main_channel(self):
        for channel in self.get_all_channels():
            print(channel.name)
            if channel.name == settings.MAIN_CHANNEL_NAME[1:]:
                self.main_channel = channel

    async def dispatch_message(self, target, content):
        if target is None:
            destination = self.main_channel
        elif isinstance(target, User):
            destination = target.raw_user
        elif isinstance(target, Channel):
            destination = target.raw_channel
        else:
            raise Exception('Invalid message destination: %s', target)

        await self.send_message(destination, content)

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
            await self.plugin_interface.fireEvent("on_message", Channel(self, message), User(self, message), message.content)

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
        self.run(settings.DISCORD_TOKEN)
