# MTA Wiki Bot
This is an IRC bot that will parse the Multi Theft Auto wiki (http://wiki.multitheftauto.com) for a function or event parameters.

Usage is simple.  Either in the designated channel, or in private message, use the following command:

    !wiki <functionName>
Or:

    !wiki <eventName>

It gracefully handles Deprecated features, and will print all Syntax Variants and related Handler functions.  It also performs some basic syntax highlighting.  The HTML parsing is fairly robust and could be repurposed for use in Text Editor API generation tools.

![Wikibot output example](http://i.imgur.com/veNfUiH.png)

# Installation
You need some Python packages before this will work.  

    pip install beautifulsoup4
    pip install irc

# Running
Once you've installed the dependencies, running is easy.  You can modify the following lines to specify the connection details.

    channel = "#mta.scripting"
    nick = "wikibot"
    server = "irc.gtanet.com"
    port = 6667
    nspass = nspass

The `nspass` refers to the NickServ password.  By default, this is read from a password.txt file.  Once everything is configured, simply run the bot:

    python wikibot.py