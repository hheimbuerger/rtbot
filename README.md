RTBot
=====

This is a re-release of the original IRC bot "RTBot" that administered and entertained #rollingthunder on Quakenet for many years, roughly between 2005 and 2012. The channel hosted members of the [Allegiance](http://www.freeallegiance.org/) squad Rolling Thunder and many friends. Most features of the bot are heavily inspired by Allegiance folklore and terminology and many bot responses are written in-universe, so they might appear nonsensical to outsiders.

I'm releasing this on GitHub purely for nostalgic reasons. If you're looking for a working bot or a base framework for your next project, you're most likely in the wrong place.
There is a hot-(re)loading plugin system at the core that would make an interesting basis for an IRC bot, but who needs an IRC bot in this day and age.

That said, it should run out of the box by setting up some basics (e.g. server, channel and bot name) in `bot/modules/config.py` and then running `bot/BotManager.py` from the bot directory. There should be no external dependencies but Python 2.7.

While I enjoyed working on, with and alongside this bot immensely, and I'm incredibly thankful for everyone who contributed ideas, code or testing to this project, please consider it now a historical artifact and don't judge anyone's skills (mine included) on this codebase. :) Many years have passed since then and—as with any project ever—we would do it all [differently and better](http://www.joelonsoftware.com/articles/fog0000000069.html) today. Nevertheless, no source code should ever be lost on an old drive, so I'm gonna release it anyway.

-- Henrik "Cort" Heimbuerger, June 17, 2016
