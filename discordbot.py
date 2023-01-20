import discord
from discord.ext import commands, tasks
from datetime import datetime
import asyncio
import os
from trycourier import Courier

TOKEN = os.environ['TOKEN']
COURIER_TOKEN = os.environ['COURIER_TOKEN']
RECEIVE_EMAIL = os.environ['RECEIVE_EMAIL']
CHANNEL_ID = 1065442694773620776
MAX_SESSION_TIME_MINUTES = 1
courier_client = Courier(auth_token=COURIER_TOKEN)

messageIDList = []
messageContentList = []
pcNameList = []
nonWorkingPCNameList = []
pcStatusList = []
isSentList = []
timeList = []
timeTemp = datetime.now().strftime("%H%M%S")
now = int(str(timeTemp)[0:2])*3600 + int(str(timeTemp)[2:4])*60 + int(str(timeTemp)[4:6])

client = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@client.event
async def on_ready():
    print('Hello, Checking bot is ready!')
    channel = client.get_channel(CHANNEL_ID)
    async for message in channel.history(limit=100):
        await message.delete()
    client.loop.create_task(watch())
    await channel.send("Hello, Checking bot is ready!")

async def watch():
    channel = client.get_channel(CHANNEL_ID)

    while True:
        bound = MAX_SESSION_TIME_MINUTES * 10
        intTime = bound
        while intTime > 2:
            async for message in channel.history(limit=1):
                timeTemp = datetime.now().strftime("%H%M%S")
                now = int(str(timeTemp)[0:2]) * 3600 + int(str(timeTemp)[2:4]) * 60 + int(str(timeTemp)[4:6])
                if message.content.endswith('is working'):
                    pcName = getMachine_Name(message.content)
                    if message.id in messageIDList:
                        break
                    messageIDList.append(message.id)
                    messageContentList.append(message.content)
                    if setdiff(messageIDList, messageContentList) != 0:
                        msg = await channel.fetch_message(setdiff(messageIDList, messageContentList))
                        await msg.delete()

                    if pcName in pcNameList:
                        order = orderFunction(pcName, pcNameList)
                        if pcStatusList[order] == 0:
                            pcStatusList[order] = 1
                            timeList[order] = now
                            isSentList[order] = 0
                        else:
                            pcStatusList[order] = 2
                            timeList[order] = now
                            isSentList[order] = 0
                    else:
                        pcNameList.append(pcName)
                        pcStatusList.append(1)
                        timeList.append(now)
                        isSentList.append(0)

            await asyncio.sleep(1)
            intTime -= 1

        # get element that exceed specified time
        order = 0
        timeTemp = datetime.now().strftime("%H%M%S")
        now = int(str(timeTemp)[0:2]) * 3600 + int(str(timeTemp)[2:4]) * 60 + int(str(timeTemp)[4:6])
        for pastTime in timeList:
            if (int(now - pastTime)) > 20:
                if pcStatusList[order] == 0:
                    if isSentList[order] == 0:
                        isSentList[order] = 0
                    else:
                        isSentList[order] = 1
                else:
                    isSentList[order] = 0
                pcStatusList[order] = 0
                nonWorkingPCNameList.append(str(pcNameList[order]))
                timeList[order] = now

            order += 1

        order = 0
        for pcStatus in pcStatusList:
            if pcStatus == 0 and isSentList[order] == 0:
                isSentList[order] = 1
                send_email(str(pcNameList[order]) + " Was Stopped")
                print(str(pcNameList[order]) + " was Stopped")
            if pcStatus == 1 and isSentList[order] == 0:
                isSentList[order] = 1
                if str(pcNameList[order]) in nonWorkingPCNameList:
                    nonWorkingPCNameList.remove(str(pcNameList[order]))
                    print(str(pcNameList[order]) + " was Started again")
                else:
                    send_email(str(pcNameList[order]) + " Was Started")
                    print(str(pcNameList[order]) + " was Started")
            if pcStatus == 2:
                isSentList[order] = 0
            order += 1

def getMachine_Name (content):
    return str(content.split()[0].strip())

def setdiff(messageIDList, messageContentList):
    order = 0
    id = 0
    for content in messageContentList:
        if order == len(messageContentList) - 1:
            break
        if content == messageContentList[len(messageContentList) - 1]:
            id = messageIDList[order]
        order += 1
    return id

def orderFunction(item, l, n=0):
    if l:
        if l[0] == item:
            return n
        elif len(l) >= 2:
            return orderFunction(item, l[1:], n+1)

def is_me(m):
    return m.author == client.user

def send_email(str):
    result = courier_client.send_message(
        message={
            "to": {
                "email": RECEIVE_EMAIL
            },
            "content": {
                "title": "Request from Discord",
                "body": "{{pc}}!"
            },
            "data": {
                "pc": str
            }
        }
    )
    return result

try:
    client.run(TOKEN)
except discord.errors.LoginFailure as e:
    print("Improper token has been passed.")
