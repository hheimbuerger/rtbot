class EchoPlugin:

    async def onChannelMessage(self, ctx, source, message):
        await ctx.reply("You said: %s" % message)

    def onPrivateMessage(self, irclib, source, message):
        irclib.sendPrivateMessage(source, "You privately said: %s" % message)
