import discord
import os
import scipy
import numpy
import pandas
import matplotlib


client = discord.Clent()


@client.event
async def on_ready():
    print("Logged in as {0.user}".format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith($nld):
        await message.channel.send("Well come back!")


client.run(os.getenv("CHATLAB"))
