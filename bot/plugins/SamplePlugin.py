class SamplePlugin:

    async def onChannelMessage(self, ctx, source, message):
        if(message == "!sample"):
            await ctx.emote("emotes")
            await ctx.reply("Hello, brave new world!")
