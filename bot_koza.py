import discord
import profanity_filter
import os
import time
import koza_settings
import random
import asyncio


token = str(os.environ.get('BOT_TOKEN'))
client = discord.Client()


def check_message(msg):
    for word in profanity_filter.bad_words:
        if msg.find(word) != -1:
            return [True, word]

    return [False, ""]


def get_log_channel(name):
    for channel in client.get_guild(int(os.environ.get('SERVER_ID'))).channels:
        if channel.name == name:
            return channel

    return None


async def status_task():
    while True:
        status = random.randint(1, 4)
        if status == 1:
            await client.change_presence(status=discord.Status.online, activity=discord.Game(koza_settings.game), )
        elif status == 2:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                   name=koza_settings.watching))
        elif status == 3:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
                                                                   name=koza_settings.listening))
        elif status == 4:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                   name=koza_settings.happy_derg))
        await asyncio.sleep(3600)


@client.event
async def on_ready():

    client.loop.create_task(status_task())

    # Setting `Playing in Heroes of the Storm` status
    # await client.change_presence(status=discord.Status.online, activity=discord.Game(koza_settings.game), )

    # Setting `Watching for you` status
    # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
    #                                                       name=koza_settings.watching))

    # Setting `Streaming happyderg` status
    # await client.change_presence(activity=discord.Streaming(name=koza_settings.scream, url=koza_settings.happy_zerg))

    # Setting `Listening RoadRadio ` status
    # await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
    #                                                       name=koza_settings.listening))


@client.event
async def on_message(message):
    msg = message.content.lower()

    # profanity_filter
    bot_react = check_message(msg)

    if bot_react[0]:
        delete = True
        for role in message.author.roles:
            if role.name.lower() in [ignore for ignore in koza_settings.profanity_ignore_groups]:
                delete = False

        if delete:
            log_channel = get_log_channel(koza_settings.log_channel)
            if log_channel is not None:
                await log_channel.send(message.author.name + ": " + msg + "\n" "Плохое слово: " + bot_react[1])

            await message.delete()
            time.sleep(1)
            await message.channel.send("AAAAAAAAAAAAAA!")
            return

    # commands
    if str(message.channel) in koza_settings.command_channel:
        if msg == '{}help'.format(koza_settings.PREFIX):
            await command_help(message.channel)
        elif msg == '{}users'.format(koza_settings.PREFIX):
            await command_users(message.channel)
        elif "загон" not in [y.name.lower() for y in message.author.roles]:
            await message.delete()
    elif msg.find("коза") != -1:
        time.sleep(1)
        await message.channel.send("AAAAAAAAAAAAAA!")


async def command_help(channel):
    emb = discord.Embed(title='Навигация по командам')
    emb.add_field(name='{}help'.format(koza_settings.PREFIX), value='Список команд')
    await channel.send(embed=emb)


async def command_users(channel):
    # emb = discord.Embed(title='Пользователи')
    # emb.add_field(name='{}help'.format(PREFIX), value='Список команд')
    server_id = client.get_guild(int(os.environ.get('SERVER_ID')))
    await channel.send(f"""Количество пользователей: {server_id.member_count}""")


client.run(token)
