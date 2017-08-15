import asyncio


class DemoPlugin:

    async def onMessage(self, ctx, source, message):

        if message == "!countdown":
            for i in range(5, 0, -1):
                await ctx.reply(i)
                await asyncio.sleep(1)
            await ctx.reply('Take off!')

        elif message == '!test':
            await ctx.reply('I can do two things at once!')
