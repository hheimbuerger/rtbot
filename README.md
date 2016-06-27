RTBot
=====

## Personal note

This is a re-release of the original IRC bot "RTBot" that administered and entertained #rollingthunder on Quakenet for many years, roughly between 2005 and 2012.
The channel hosted members of the [Allegiance](http://www.freeallegiance.org/) squad Rolling Thunder and friends. Many features of the bot are heavily inspired by
Allegiance folklore and terminology and bot responses are often written in-universe, so they might appear nonsensical to outsiders. ('gu)

I'm releasing this on GitHub purely for nostalgic reasons. If you're looking for a working bot or a base framework for your next project, you're most likely in the wrong place.
There is a hot-(re)loading plugin system at the core that would make an interesting basis for an IRC bot, but who needs an IRC bot in this day and age... (Anyone interested in turning it into a Slack bot? :wink:)

That said, if you really want to run it, it should pretty much run out of the box. Just bootstrapping the AuthenticationPlugin database is a bit tricky (but most plugins work without that).

I highly enjoyed working on, with and alongside this bot immensely. And I'm incredibly thankful for everyone who contributed ideas, code or testing to this project.
Now, please consider it a historical artifact and don't judge anyone's skills (mine included) on this codebase. :blush:
Many years have passed since then and—as with any project ever—we would do it all [differently and better](http://www.joelonsoftware.com/articles/fog0000000069.html) today.
Nevertheless, no source code should ever be lost on an old drive, so I'm gonna release it anyway.

My personal thanks go to everyone who directly contributed code to this over the years, most of whom I had the pleasure of meeting in person at some point in my life:
badp, Bard, Ksero, Serpardum and Terralthra. And of course everyone in the channel who tested and suggested day in, day out.

-- Cort, June 17, 2016

## Usage

To run it, all you need it is Python 2.7.  
Run the `bot/BotManager.py` from its directory and by default it will appear as *RTBotTest* in `#RT.development` on Quakenet.  
You can configure those values in `bot/modules/config.py`.
