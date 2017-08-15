import random, logging

class RandomGamePlugin:
	factions = ['IC', 'BIOS', 'Belts', 'Rix', 'Giga', 'TF', 'GT', 'Dreg']
	gameSettings = {'Starting': ['Low / 0.75', 'Med / 1', 'high 1.25', 'V High 1.5'],
					'total': ['Low - 0.75', 'Med Low - 0.85', 'Med - 1.0', 'Med High - 1.15', 'High 1.25', 'higher 1.35'],
					'Resources': ['Very Scarce', 'Scarce', 'Scarce +', 'Normal', 'N:NoHomeS', 'Equal', 'Plentiful', 'P:NoHomeS']
				   }

	def __init__(self, pluginInterface):
		self.pluginInterfaceReference = pluginInterface

	def getVersionInformation(self):
		return("$Id: RandomGamePlugin.py 0 2009-08-06 15:24:26Z cortex $")

	def onChannelMessage(self, irclib, sender, message):
		messageParts = message.split()
		if((len(messageParts) == 4) and (messageParts[0] == "RandomAlleg") and (messageParts[2] == "vs.")):
			comm1 = messageParts[1]
			comm2 = messageParts[3]

			settings = []
			for (settingName, settingOptions) in RandomGamePlugin.gameSettings.items():
				settings.append('%s = %s' % (settingName, random.choice(settingOptions)))
			
			irclib.sendChannelMessage('%s playing %s' % (comm1, random.choice(RandomGamePlugin.factions)))
			irclib.sendChannelMessage('%s playing %s' % (comm2, random.choice(RandomGamePlugin.factions)))
			irclib.sendChannelMessage('Settings: %s' % (', '.join(settings)))
	  


class IrcLibMock:
	def sendChannelMessage(self, text):
		print text
if __name__ == "__main__":
	rgp = RandomGamePlugin(None)
	rgp.onChannelMessage(IrcLibMock(), 'sender', 'RandomAlleg Rav vs. Spidey')
	rgp.onChannelMessage(IrcLibMock(), 'sender', 'RandomAlleg Rav vs. Spidey')
	rgp.onChannelMessage(IrcLibMock(), 'sender', 'RandomAlleg Rav vs. Spidey')
