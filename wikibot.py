#! /usr/bin/env python
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
import re
import requests

f = open("password.txt","r")
token = f.readline().rstrip()
f.close()

####################################################
#### CONFIG
####################################################
description = '''MTA wiki bot to grab function syntaxes from the wiki.'''
bot = commands.Bot(command_prefix='!', description=description)

maxMessages = 4 # Maximum number of messages (exc url) before cutting off. Use private commands to avoid
maxTries = 6   # Maximum number of times to try getting info from wiki

####################################################
#### STRING OPERATIONS
####################################################
def cleanString(str):
    return (" ").join(str.replace("\t",' ').replace("\n",'').replace("\r",'').split())

def make_output(queue, name):
    msg = ""
    if len(queue) != 0:
        msg = "**"+name+":**\n```lua\n"
        msg += "\n".join(queue)
        msg += "```"

    return msg



####################################################
#### COMMAND LOGIC
####################################################
@bot.command()
async def wiki(fnName : str):
    url = 'http://wiki.multitheftauto.com/wiki/'+fnName
    page = requests.get(url).text
    print("yo1")
    # Let's strip out examples onwards if we've found them
    exampleStart = page.find('<span class="mw-headline" id="Example')
    if exampleStart != -1:
        page = page[:exampleStart]

    soup = BeautifulSoup(page, 'html.parser')
    #Scan for deprecated functions
    deprecated = soup.find(text=re.compile('This function is deprecated. This means that its use is discouraged and that it might not exist in future versions.'))
    if deprecated:
        a = deprecated.parent.parent.parent.find("a")
        if a:
            args[1] = a.get('href').replace('/wiki/','')
            return wiki(c,args,target,useNotice)
    print("yo")
    for meta in soup.find_all('meta'):
        if meta.get('name') == 'headingclass':
            msgQueue = {
                "Server-only function": [],
                "Serverside event": [],
                "Client-only function": [],
                "Clientside event": [],
                "Shared function": [],
            }

            fnName = soup.select("h1")[0].string
            fnName = fnName[0].lower() + fnName[1:]
            fnType = meta.get('data-subcaption')
            print(fnType)
            if msgQueue.get(fnType) is None:
                print("NOPE")
                continue

            print(fnType)
            codeList = soup.select("pre.lang-lua")
            if codeList[0]:
                #Try and find a server syntax
                serverHeadingAdded = False
                serverCodeList = soup.select("div.serverContent pre.lang-lua")
                for code in serverCodeList:
                    if not serverHeadingAdded:

                        serverHeadingAdded = True
                    fnTypeNow = "Server-only function" if fnType.find("function") != -1 else "Serverside event"
                    msgQueue[fnTypeNow].append( cleanString(code.string) )

                #Then a client syntax
                clientCodeList = soup.select("div.clientContent pre.lang-lua")
                for code in clientCodeList:
                    fnTypeNow = "Client-only function" if fnType.find("function") != -1 else "Clientside event"
                    msgQueue[fnTypeNow].append(cleanString(code.string))

                #Fall back to content without a <section/> tag
                if len(serverCodeList) == 0 and len(clientCodeList) == 0:
                    for code in codeList:
                        msgQueue[fnType].append(cleanString(code.string))

            msg = ""
            msg += make_output(msgQueue["Server-only function"], "Server")
            msg += make_output(msgQueue["Client-only function"], "Client")
            msg += make_output(msgQueue["Serverside event"], "Server event")
            msg += make_output(msgQueue["Clientside event"], "Client event")
            msg += make_output(msgQueue["Shared function"], "Both")

            embed = discord.Embed(title="View on Wiki", url=url)
            print(msg)
            await bot.say(msg, embed=embed)
            return
   
####################################################
#### MAIN
####################################################
def main():
    bot.run(token)

if __name__ == "__main__":
    main()