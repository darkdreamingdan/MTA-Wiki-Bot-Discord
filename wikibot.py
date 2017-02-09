import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import re
import requests
import logging

"""
LOGGING
"""
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

"""
CONFIG
"""
description = '''MTA wiki bot to grab function syntaxes from the wiki.'''
bot = commands.Bot(command_prefix=['!', '.'], description=description)

f = open("password.txt", "r")
token = f.readline().rstrip()
f.close()


def clean_string(msg):
    """Clean a message string to get rid of tabs and spaces 
    Args:
        msg (str): The original chat message 
    Returns:
        str: Cleaned message
    """
    return " ".join(msg.replace("\t", ' ').replace("\n", '').replace("\r", '').split())


def make_output(queue, name):
    """Make an output a parameter list
    Args:
        queue (list): List of code parameters
        name (str): The name of the type of function
    Returns:
        str: A compiled Discord markdown string of the syntaxes
    """
    msg = ""
    if len(queue) != 0:
        msg = "**"+name+":**\n```lua\n"
        msg += "\n".join(queue)
        msg += "```"

    return msg


def get_wiki_syntax(fn_name):
    """Produce a Discord markdown string from a particular function name by looking up the wiki    
    Args:
        fn_name (str): The function name to lookup 
    Returns:
        str: The Discord message containing the wiki syntaxes
        embed: A discord embed object containing a link to the Wiki for the function
    """
    url = 'http://wiki.multitheftauto.com/wiki/'+fn_name
    page = requests.get(url).text

    # Let's strip out examples onwards if we've found them
    example_start = page.find('<span class="mw-headline" id="Example')
    if example_start != -1:
        page = page[:example_start]

    soup = BeautifulSoup(page, 'html.parser')
    # Scan for deprecated functions
    deprecated = 'This function is deprecated. This means that its use is discouraged and that it might not exist in ' \
                 'future versions.'
    deprecated = soup.find(text=re.compile(deprecated))
    if deprecated:
        a = deprecated.parent.parent.parent.find("a")
        if a:
            new_name = a.get('href').replace('/wiki/', '')
            return get_wiki_syntax(new_name)

    for meta in soup.find_all('meta'):
        if meta.get('name') == 'headingclass':
            msg_queue = {
                "Server-only function": [],
                "Serverside event": [],
                "Client-only function": [],
                "Clientside event": [],
                "Shared function": [],
            }

            fn_name = soup.select("h1")[0].string
            fn_name = fn_name[0].lower() + fn_name[1:]
            fn_type = meta.get('data-subcaption')

            if msg_queue.get(fn_type) is None:
                continue

            code_list = soup.select("pre.lang-lua")
            if code_list and code_list[0]:
                # Try and find a server syntax
                server_code_list = soup.select("div.serverContent pre.lang-lua")
                for code in server_code_list:
                    fn_type_now = "Server-only function" if fn_type.find("function") != -1 else "Serverside event"
                    msg_queue[fn_type_now].append(clean_string(code.string))

                # Then a client syntax
                client_code_list = soup.select("div.clientContent pre.lang-lua")
                for code in client_code_list:
                    fn_type_now = "Client-only function" if fn_type.find("function") != -1 else "Clientside event"
                    msg_queue[fn_type_now].append(clean_string(code.string))

                # Fall back to content without a <section/> tag
                if len(server_code_list) == 0 and len(client_code_list) == 0:
                    for code in code_list:
                        msg_queue[fn_type].append(clean_string(code.string))

            msg = ""
            msg += make_output(msg_queue["Server-only function"], "Server")
            msg += make_output(msg_queue["Client-only function"], "Client")
            msg += make_output(msg_queue["Serverside event"], "Server event")
            msg += make_output(msg_queue["Clientside event"], "Client event")
            msg += make_output(msg_queue["Shared function"], "Both")

            embed_title = "No Parameters Found.  View on Wiki" if msg == "" else "View on Wiki"
            embed = discord.Embed(title=embed_title, url=url)

            return msg, embed


"""
COMMAND LOGIC
"""


@bot.group(pass_context=True)
async def wiki(ctx, fn_name):
    msg, embed = get_wiki_syntax(fn_name)
    if ctx.prefix == "!":
        await bot.say(msg, embed=embed)
    elif ctx.prefix == ".":
        await bot.whisper(msg, embed=embed)
   
"""
MAIN
"""


def main():
    bot.run(token)

if __name__ == "__main__":
    main()
