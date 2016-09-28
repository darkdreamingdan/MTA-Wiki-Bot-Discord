#! /usr/bin/env python
from bs4 import BeautifulSoup
import urllib2
import irc.bot
import irc.strings
import re
from irc.client import ip_numstr_to_quad, ip_quad_to_numstr
f = open("password.txt","r")
nspass = f.readline().rstrip()
f.close()

####################################################
#### CONFIG
####################################################
channels = ["#mta.scripting","#mta.dev"]
nick = "wikibot"
server = "irc.gtanet.com"
port = 6667
nspass = nspass

maxMessages = 4 # Maximum number of messages (exc url) before cutting off. Use private commands to avoid
maxTries = 6   # Maximum number of times to try getting info from wiki

####################################################
#### WIKI DEFINITIONS
####################################################

definitionData = {
    "Clientside event" : { 'color': 4, 'name' : 'Client Event' },
    "Serverside event" : { 'color': 7, 'name' : 'Client Event' },
    "Client-only function" : { 'color': 4, 'name' : 'Client' },
    "Server-only function" : { 'color': 7, 'name' : 'Server' },
    "Shared function" : { 'color': 12, 'name' : 'Both' }
}

####################################################
#### SYNTAX HIGHLIGHTS DEFS
####################################################
#keyword:ircColor
keywords = {
"matrix":3,
"vector2":3,
"vector3":3,
"vector4":3,
"ban":3,
"blip":3,
"bool":3,
"boolean":3,
"callback":3,
"client":3,
"colcircle":3,
"colcube":3,
"colshape":3,
"colsphere":3,
"colsquare":3,
"coltube":3,
"console":3,
"element":3,
"float":3,
"int":3,
"marker":3,
"object":3,
"ped":3,
"pickup":3,
"player":3,
"radararea":3,
"remoteclient":3,
"resource":3,
"string":3,
"table":3,
"team":3,
"textdisplay":3,
"textitem":3,
"vehicle":3,
"xmlnode":3,
"false":6,
"true":6,
"nil":6,
"function":6,
}

puns = {
"\\":10,
"\"":10,
"'":10,
"-":10,
"+":10,
"=":10,
"[":10,
"]":10,
"(":10,
")":10,
"*":10,
"/":10,
"^":10,
",":10,
}

####################################################
#### PURE IRC LOGIC
####################################################
class WikiBot(irc.bot.SingleServerIRCBot):
    def __init__(self, channels, nickname, server, port=6667):
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port)], nickname, nickname)
        self.stack = 0;
        self.channelJoinList = channels

    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def on_welcome(self, c, e):
        for ch in self.channelJoinList:
            c.join(ch)
        c.privmsg("nickserv","identify "+nspass)

    def on_privmsg(self, c, e):
        self.do_command(e, e.arguments[0].split(), e.source.nick)

    def on_pubmsg(self, c, e):
        self.do_command(e, e.arguments[0].split(), e.target)
        return

    def on_dccmsg(self, c, e):
        return

    def on_dccchat(self, c, e):
        return
        
    def on_kick(self, c, e):
        print(c.join,e.target,e)
        c.join(e.target)  # Try to rejoin channel once when kicked
        
    def on_invite(self, c, e):
        print(c.join,e.target,e,e.source,e.arguments,e.type)
        c.join(e.arguments[0])
        
    def msg(self,target,output,useNotice): #Wrapper to catch any errors
        if useNotice:
            try:
                print("notice:",target,output)
                self.connection.notice(target,output)    
            except Exception,e: 
                print str(e)
        else:
            try:
                print(target,output)
                self.connection.privmsg(target,output)    
            except Exception,e: 
                print str(e)

    def do_command(self, e, args, target):
        c = self.connection
        cmd = args[0]
        if cmd == "!wiki" and len(args)>1:
            self.wiki(c,args,target,False)
        elif cmd == ".wiki" and len(args)>1:
            self.wiki(c,args,e.source.nick,True)

   
####################################################
#### COMMAND LOGIC
####################################################
    def wiki(self,c,args,target,useNotice=False):
        if self.stack == maxTries:
            self.stack = 0;
            return;
        self.stack += 1
         
        fnName = args[1];
        url = 'http://wiki.multitheftauto.com/wiki/'+fnName
        try:
            page = urllib2.urlopen(url)
        except urllib2.URLError, err: #To-do: Try again
            print(urllib2.URLError, err)
            return self.wiki(c,args,target,useNotice)
        try:
            page = page.read()
        except urllib2.URLError, err:
            print(urllib2.URLError, err)
            return self.wiki(c,args,target,useNotice)
            
        # Let's strip out examples onwards if we've found them            
        exampleStart = page.find('<span class="mw-headline" id="Example')
        if exampleStart != -1:
            page = page[:exampleStart]
        
        soup = BeautifulSoup(page, 'html.parser')           
        #Scan for deprecated functions
        deprecated = soup.find(text=re.compile('This function is deprecated. This means that its use is discouraged and that it might not exist in future versions.'))
        if deprecated > 0:
            a = deprecated.parent.parent.parent.find("a")
            if a:
                args[1] = a.get('href').replace('/wiki/','')
                return self.wiki(c,args,target,useNotice)
        
        for meta in soup.find_all('meta'):
            if meta.get('name') == 'headingclass':
                fnName = soup.select("h1")[0].string
                fnName = fnName[0].lower() + fnName[1:]                   
                fnType = meta.get('data-subcaption')
                if definitionData.get(fnType):
                    keywords[fnName] = definitionData[fnType]['color']
                else:
                    continue
                
                msgQueue = []
                
                codeList = soup.select("pre.lang-lua")
                if codeList[0]:
                    #Try and find a server syntax
                    serverCodeList = soup.select("div.serverContent pre.lang-lua")
                    for code in serverCodeList:
                        fnTypeNow = "Server-only function" if fnType.find("function") != -1 else "Serverside event"
                        msgQueue.append( markup(fnName,fnTypeNow,code.string) )
                    
                    #Then a client syntax
                    clientCodeList = soup.select("div.clientContent pre.lang-lua")
                    for code in clientCodeList:
                        fnTypeNow = "Client-only function" if fnType.find("function") != -1 else "Clientside event"
                        msgQueue.append( markup(fnName,fnTypeNow,code.string) )
                    
                    #Fall back to content without a <section/> tag
                    if len(serverCodeList) == 0 and len(clientCodeList) == 0:
                        for code in codeList:
                            msgQueue.append( markup(fnName,fnType,code.string) )
                
                count = 0
                urlMsg = "\x02"+url+"\x02"
                for msg in msgQueue:
                    if (count == maxMessages) and not useNotice and (target[0] in "#&+!"):
                        urlMsg = "\x02...tl;dr -\x02 " + urlMsg;
                        break
                    self.msg(target,msg,useNotice)
                    count += 1
                    
                self.msg(target,urlMsg,useNotice)

                self.stack = 0
                return
   
####################################################
#### STRING OPERATIONS
####################################################
def cleanString(str):
    return (" ").join(str.replace("\t",' ').replace("\n",'').replace("\r",'').split())
    
def reg_repl(m):
    color = "%02d" %keywords[m.group(0)]
    return "\x03" + color + m.group(0) + "\x03"
    
def syntaxHighlight(str,fnName,color):
    for k in keywords:
        str = re.sub(r"\b%s\b"%k,reg_repl,str)   
    
    for p in puns:
        color = "%02d" % puns[p]
        str = str.replace(p,"\x03" + color + p + "\x03\x0F")
    
    return str
        

def markup(fnName,fnType,text):
    text = cleanString(text)
    color = "%02d" % definitionData[fnType]['color']
    text = syntaxHighlight(text,fnName,color)
    output = "\x02\x03"+color+definitionData[fnType]['name']+"\x02\x03\x0F"
    output += ": " + text
    return output


####################################################
#### MAIN
####################################################
def main():
    import sys
    bot = WikiBot(channels, nick, server, port)
    bot.start()

if __name__ == "__main__":
    main()