import asyncio

from plugin_base import BasePlugin


class DemoPlugin(BasePlugin):

    async def on_message(self, channel, user, message):
        if message == "!countdown":
            for i in range(5, 0, -1):
                await self.send_message(channel, i)   # one way to respond on the same channel
                await asyncio.sleep(1)
            await channel.reply('Take off!')   # another way

        elif message == '!test':
            await self.send_message(channel, 'I can do two things at once!')
