import re


class HumanBehaviourPlugin:
    helpMessage = ["You can read up on my commands on this page: http://wiki.edge-of-reality.de/bin/view/Main/RTBotCommands"]

    def __init__(self):
        self.saidMyNameLastMessage = {}

    def removeURLs(self, text):
        reResult = re.compile("(.*?)http://(\\S*)(.*)").match(text)
        if reResult:
            return(self.removeURLs(reResult.groups()[0] + reResult.groups()[2]))
        else:
            return(text)

    # @PluginInterface.Priorities.prioritized(PluginInterface.Priorities.PRIORITY_LOW)
    async def on_message(self, ctx, source, message):
        if ctx.is_private:
            if message == "help":
                # TODO: this URL no longer exists. However, Discord doesn't have IRC's strict rate limits, so we can just print out lots of help right here, e.g. in a single big code block
                for line in HumanBehaviourPlugin.helpMessage:
                    await ctx.reply(line)
                return True
    
            if source.isAdmin():   # TODO: these are supposed to make the bot act *in the text channel* when instructed in PM. This is broken right now.
                if (len(message.split()) > 0) and (message.split()[0] == "say"):
                    await ctx.reply(message[4:])
                    return True
                elif (len(message.split()) > 0) and (message.split()[0] == "me"):
                    await ctx.emote(message[3:])
                    return True

        if message.lower() == "'yt" or message.lower() == "`yt":
            await ctx.reply("'rt")
        elif message.lower() == "'yb" or message.lower() == "`yb":
            await ctx.reply("'yb")
        elif message.lower() == "'yr" or message.lower() == "`yr":
            await ctx.reply("See ya, " + source.getCanonicalNick() + "!")
        elif message.lower() == "'ym" or message.lower() == "`ym":
            await ctx.reply("'yt")
        elif message.lower() == "'gl" or message.lower() == "`gl":
            await ctx.reply("'gc")
        elif message.lower() == "'go" or message.lower() == "`go":
            await ctx.reply("Sleep well, " + source.getCanonicalNick() + "!")
        elif message.lower() == "'ac" or message.lower() == "`ac":
            await ctx.reply("Ram it! Ram it! RAM IT!!!")
        elif message.lower() == "'gn" or message.lower() == "`gn":
            await ctx.reply("Read the Academy, you n00b!")
        elif 'lich' in message.lower():
            await ctx.reply("A lich? TURN UNDEAD!")
        elif 'ghost' in message.lower():
            await ctx.reply("A ghost? TURN UNDEAD!")
        elif 'ghast' in message.lower():
            await ctx.reply("A ghast? TURN UNDEAD!")
        elif 'zombie' in message.lower():
            await ctx.reply("A zombie? TURN UNDEAD!")
        elif 'ghoul' in message.lower():
            await ctx.reply("A ghoul? TURN UNDEAD!")
        elif 'skeleton' in message.lower():
            await ctx.reply("A skeleton? TURN UNDEAD!")
        elif 'slut' in message.lower():
            await ctx.reply("A slut? TURN UNWED!")
        elif 'rtbot' in self.removeURLs(message).lower():
            if "'yh" in message.lower() or 'sup' in message.lower():
                await ctx.reply("'yh! I'm fine. How about you?")
            else:
                await ctx.reply("Hey " + source.getCanonicalNick() + ", did you just say my name?")
                self.saidMyNameLastMessage[source] = True
