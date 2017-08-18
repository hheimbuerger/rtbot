import re


class HumanBehaviorPlugin:
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
    async def on_message(self, channel, user, message):
        if channel.is_private:
            if message == "help":
                # TODO: this URL no longer exists. However, Discord doesn't have IRC's strict rate limits, so we can just print out lots of help right here, e.g. in a single big code block
                for line in HumanBehaviorPlugin.helpMessage:
                    await channel.reply(line)
                return True
    
            if user.is_admin():   # TODO: these are supposed to make the bot act *in the text channel* when instructed in PM. This is broken right now.
                if (len(message.split()) > 0) and (message.split()[0] == "say"):
                    await channel.reply(message[4:])
                    return True
                elif (len(message.split()) > 0) and (message.split()[0] == "me"):
                    await channel.reply('_'+message[3:]+'_')
                    return True

        if message.lower() == "'yt" or message.lower() == "`yt":
            await channel.reply("'rt")
        elif message.lower() == "'yb" or message.lower() == "`yb":
            await channel.reply("'yb")
        elif message.lower() == "'yr" or message.lower() == "`yr":
            await channel.reply("See ya, " + user.name + "!")
        elif message.lower() == "'ym" or message.lower() == "`ym":
            await channel.reply("'yt")
        elif message.lower() == "'gl" or message.lower() == "`gl":
            await channel.reply("'gc")
        elif message.lower() == "'go" or message.lower() == "`go":
            await channel.reply("Sleep well, " + user.name + "!")
        elif message.lower() == "'ac" or message.lower() == "`ac":
            await channel.reply("Ram it! Ram it! RAM IT!!!")
        elif message.lower() == "'gn" or message.lower() == "`gn":
            await channel.reply("Read the Academy, you n00b!")
        elif 'lich' in message.lower():
            await channel.reply("A lich? TURN UNDEAD!")
        elif 'ghost' in message.lower():
            await channel.reply("A ghost? TURN UNDEAD!")
        elif 'ghast' in message.lower():
            await channel.reply("A ghast? TURN UNDEAD!")
        elif 'zombie' in message.lower():
            await channel.reply("A zombie? TURN UNDEAD!")
        elif 'ghoul' in message.lower():
            await channel.reply("A ghoul? TURN UNDEAD!")
        elif 'skeleton' in message.lower():
            await channel.reply("A skeleton? TURN UNDEAD!")
        elif 'slut' in message.lower():
            await channel.reply("A slut? TURN UNWED!")
        elif 'rtbot' in self.removeURLs(message).lower():
            if "'yh" in message.lower() or 'sup' in message.lower():
                await channel.reply("'yh! I'm fine. How about you?")
            else:
                await channel.reply("Hey " + user.name + ", did you just say my name?")
                self.saidMyNameLastMessage[user] = True
