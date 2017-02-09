# MTA Wiki Bot Discord
This is an Discord bot that will parse the Multi Theft Auto wiki (http://wiki.multitheftauto.com) for a function or event parameters.  It is a port of the original IRC bot.

Usage is simple.  Either in the designated channel, or in private message, use the following command:

    !wiki <functionName>
Or:

    !wiki <eventName>

It gracefully handles Deprecated features, and will print all Syntax Variants and related Handler functions.  It also performs some basic syntax highlighting.  The HTML parsing is fairly robust and could be repurposed for use in Text Editor API generation tools.

![Wikibot output example](http://i.imgur.com/HyHjXxc.png)

# Getting the bot on your server

The bot is available to be added to other Discord servers upon request.  Just contact me and I can setup the bot on your server so you don't have to host it yourself.


# Installation
These instructions are if you want to run the bot yourself.  You'll need a [Discord token](https://github.com/reactiflux/discord-irc/wiki/Creating-a-discord-bot-&-getting-a-token) for this to work.

You need some Python packages before this will work - beautifulsoup4, requests, and discord.  You can use pip, or a Conda environment definition has been provided:

1. Install [Anaconda Python](https://www.continuum.io/downloads) or [miniconda Python](http://conda.pydata.org/miniconda.html)  (Version 3.6 reccomended, though either will work)
2. Create a conda Environment using the `environment.yml`.  This will automatically download all required dependencies:
	-  `conda env create -f environment.yml`

# Running
Once you've installed the dependencies, running is easy. 

1. Edit password.txt with your Discord bot token
2. Activate the environment:
	- **Linux, OS X:** `source activate wikibot`
	- **Windows:** `activate wikibot`
3. `python wikibot.py`

