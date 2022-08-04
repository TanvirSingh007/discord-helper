import asyncio
from http import server
from time import sleep
from click import command
import discord
import datetime
import json

tokenFile = open('BotToken.txt')
TOKEN = tokenFile.read()
tokenFile.close()
client = discord.Client()

commandlist = ["-help", '-list', '-schedule', '-delete', '-info', '-time']

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
    getScheduledTime()

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
                    retval = retval + str(index) + ':```' + scheduledMessage["Message"] + '``` is scheduled at ' + (datetime.datetime.strptime(scheduledMessage["Schedule Time"], '%d/%m/%Y %H:%M')).strftime('%d-%B-%Y %H:%M') + ' in <#' + scheduledMessage["Channel"] + '>\n'
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
        
        time = datetime.datetime.strptime(args[0] + ' ' + args[1], '%d/%m/%Y %H:%M')
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
        
        while '```' in schMessage:
            i = schMessage.find('```')
            schMessage = schMessage[0:i] + schMessage[i+3:]
        
        while schMessage[0] == '`':
            schMessage = schMessage[1:]
        
        while schMessage[len(schMessage)-1] == '`':
            schMessage = schMessage[0:len(schMessage)-2]

        newschedule = {
            "Message": schMessage,
            "Channel": channel,
            "Active": True,
            "Schedule Time": time.strftime('%d/%m/%Y %H:%M'),
            "isRepetitive": ((delayInMins >= 360) and (delayInMins <= 5256000)),
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

        if(len(messageData[serverid][userid]) < 10):
            saveMessages(messageData)
            return 'Message Scheduled'
        
        else:
            return 'Message Limit Reached'

    except:
        return 'Incorrect format, use -help to know more'    

async def sendmessage (channel, message):
    channel = client.get_channel(int(channel))
    await channel.send(message)
    
async def parseCommand(message):
    command = message.content
    info = '''
        ```Message scheduler for discord by bjsbrar
        https://github.com/bjsbrar/DiscordMessageScheduler
        Waring: Bad Code``` 
    '''
    help = '''
```Command List:
  -help     : List Commands
  -info     : Bot Information
  -list     : Provides a list of all scheduled messages
  -schedule : Schedules a message\n''' + "              Usage: -schedule '''[message text]''' [Schedule Date (format: DD/MM/YYYY)] [Schedule Time (format: HH:MM)] *[#message channel] *[Repetetion time in minutes]\n" + '''
              * Optional Parameters
              Repetetion time must be 6 hours (360 minutes) or more to avoid spamming 
  -delete   : Deletes a scheduled message at a given index 
              Usage: -delete [index]
  -time     : Displays server time```'''

    if(command.split(' ')[0] == '-help'):
        await sendmessage (message.channel.id, help)
    elif(command.split(' ')[0] == '-delete'):
        await sendmessage (message.channel.id, delMessage(message))
    elif(command.split(' ')[0] == '-list'):
        await sendmessage (message.channel.id, listMessage(message))
    elif(command.split(' ')[0] == '-schedule'):
        await sendmessage (message.channel.id, scheduleMessage(message))
    elif(command.split(' ')[0] == '-info'):
        await sendmessage (message.channel.id, info)
    elif(command.split(' ')[0] == '-time'):
        await sendmessage (message.channel.id, datetime.datetime.now().strftime('%d-%B-%Y %H:%M'))

def getScheduledTime():
    data = loadMessages()
    global timeDict
    timeDict = {}
    for serverid in data.keys():
        for userid in data[serverid].keys():
            index  = 0
            for message in data[serverid][userid]:
                try:
                    timeDict[(message["Schedule Time"])].append([serverid, userid, index])
                except:
                    timeDict[(message["Schedule Time"])] = [[serverid, userid, index]]
                index = index + 1

async def sendScheduledMessage(timeInfo):
    global commandQueue
    print('Sending Message')
    data = loadMessages()
    for messageInfo in timeInfo:
        serverid, userid, index = messageInfo
        if data[serverid][userid][index]["Active"]:
            await sendmessage(data[serverid][userid][index]["Channel"], data[serverid][userid][index]["Message"])
            if data[serverid][userid][index]["isRepetitive"]:
                now = datetime.datetime.strptime(data[serverid][userid][index]["Schedule Time"], '%d/%m/%Y %H:%M')
                now += datetime.timedelta(minutes=data[serverid][userid][index]["Repetition Time in minutes"])
                data[serverid][userid][index]["Schedule Time"] = now.strftime('%d/%m/%Y %H:%M')
            else:
                data[serverid][userid].pop(index)
    saveMessages(data)

async def idle():
    global timeDict
    getScheduledTime()

    while True:
        now = datetime.datetime.now()
        now = now.strftime('%d/%m/%Y %H:%M')
        try:
            await sendScheduledMessage(timeDict[now])
        except:
            try:
                message = commandQueue.pop(0)
                await parseCommand(message)
            except:
                await asyncio.sleep(1)

@client.event
async def on_ready():
    await idle()

@client.event
async def on_message(message):
    global commandQueue
    if((str(message.content).split(' '))[0] in commandlist):
        try:
            commandQueue.append(message)
        except:
            commandQueue = [message]

client.run(TOKEN)

