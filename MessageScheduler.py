import asyncio
from http import server
from time import sleep
import discord
import datetime
import json

tokenFile = open('BotToken.txt')
TOKEN = tokenFile.read()
tokenFile.close()
client = discord.Client()

commandlist = ["-help", '-list', '-schedule', '-delete']

def isInteger (string):
    try:
        int(string)
        return True
    except:
        return False

def loadMessages():
    f = open('messages.json')
    data = json.load(f)
    f.close()
    return data

def saveMessages(data):
    f = open('messages.json', 'w')
    json.dump(data, f, indent = 2)
    f.close()

def listMessage(message):
    data = loadMessages()
    serverid = str(message.guild.id)
    userid = str(message.author.id)
    try:
        if (len(data[serverid][userid]) == 0):
            raise Exception
        else:
            retval = 'You have the following scheduled messages: \n'
            index = 1
            for scheduledMessage in data[serverid][userid]:
                if(scheduledMessage["Active"]):
                    retval = retval + str(index) + ':```' + scheduledMessage["Message"] + '``` is scheduled at ' + (datetime.datetime.strptime(scheduledMessage["Schedule Time"], "%Y-%d-%m %H:%M:%S")).strftime('%d-%B-%Y %H:%M') + ' in <#' + scheduledMessage["Channel"] + '>\n'
                index += 1
            return retval

    except:
        return 'You have no scheduled messages'

def delMessage(message):
    data = loadMessages()
    serverid = str(message.guild.id)
    userid = str(message.author.id)
    try:
        lastIndex = len(data[serverid][userid])
        if(len(message.content.split(' ')) != 2):
            return 'Incorrect format used. Use ```-help``` to learn more '
        else:
            if(isInteger(message.content.split(' ')[1])):
                try:
                    if(int(message.content.split(' ')[1]) < 1):
                        raise Exception
                    data[serverid][userid].pop(int(message.content.split(' ')[1]) - 1)
                    saveMessages(data)
                    return 'Deleted!'
                except:
                    return 'Index out of range'
            else:
                return 'Incorrect format used. Use ```-help``` to learn more '
    except:
        return 'You have no scheduled messages'

def scheduleMessage(message):
    serverid = str(message.guild.id)
    userid = str(message.author.id)
    try:
        if(len(message.content.split("'''"))!=3):
            raise Exception
        
        schMessage = message.content.split("'''")[1]
        if(message.content.split("'''")[0] != '-schedule '):
            raise Exception
        
        args = message.content.split("'''")[2].split(' ')
        if(args[0] == ''):
            args.pop(0)
        numArgs = len(args)
        if(not (numArgs == 2 or numArgs == 3 or numArgs == 4)):
            raise Exception

        time = datetime.datetime.strptime(args[0] + ' ' + args[1], "%d/%m/%Y %H:%M")
        channel = str(message.channel.id)
        delayInMins = 0

        if(numArgs > 2):
            if(args[2][0:2] == '<#' and args[2][-1] == '>'):
                channel = args[2][2:-1]
                if(numArgs == 4):
                    delayInMins = int(args[3])
            else:
                channel = str(message.channel.id)
                delayInMins = int(args[2])

        newschedule = {
            "Message": schMessage,
            "Channel": channel,
            "Active": True,
            "Schedule Time": str(time),
            "isRepetitive": (delayInMins > 60),
            "Repetition Time in minutes": delayInMins
        }

        messageData = loadMessages()

        if(serverid in messageData.keys()):
            if(userid in messageData[serverid].keys()):
                messageData[serverid][userid].append(newschedule)
            else:
                messageData[serverid][userid] = [newschedule]
        else:
            newuser = {
                userid: [newschedule]
            }
            messageData[serverid] = newuser

        saveMessages(messageData)

        return 'success'
    except:
        return 'Incorrect format, use -help to know more'    

async def sendmessage (channel, message):
    channel = client.get_channel(int(channel))
    await channel.send(message)
    
async def parseCommand(message):
    command = message.content
    if(command.split(' ')[0] == '-help'):
        await sendmessage (message.channel.id, '''
```The available commands are:
  -help
  -list
  -schedule
  -delete```
        ''')
    elif(command.split(' ')[0] == '-delete'):
        await sendmessage (message.channel.id, delMessage(message))
    elif(command.split(' ')[0] == '-list'):
        await sendmessage (message.channel.id, listMessage(message))
    elif(command.split(' ')[0] == '-schedule'):
        await sendmessage (message.channel.id, scheduleMessage(message))

async def idle():
    data = loadMessages()
    now = datetime.datetime.now()
    
    print(now.date())

@client.event
async def on_ready():
    #await client.change_presence(status=discord.Status.online, activity=discord.CustomActivity(name=''))
    await idle()

@client.event
async def on_message(message):
    if((str(message.content).split(' '))[0] in commandlist):
        await parseCommand(message)

client.run(TOKEN)

