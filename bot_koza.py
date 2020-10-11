import discord
import profanity_filter
import os
import time
from discord.ext import commands
import random
import youtube_dl
import koza_settings


token = str(os.environ.get('BOT_TOKEN'))
client = commands.Bot(command_prefix = '!')


def check_message(msg):
    for word in profanity_filter.bad_words:
        if msg.find(word) != -1:
            return True

    return False


def get_log_channel(name):
    for channel in client.get_guild(int(os.environ.get('SERVER_ID'))).channels:
        if channel.name == name:
            return channel


@client.event
async def on_ready():
    status = koza_settings.statuses[1]
    await client.change_presence(status=discord.Status.online, activity=discord.Game(status), )


@client.event
async def on_message(message):
    msg = message.content.lower()

    # profanity_filter
    bot_react = check_message(msg)

    if bot_react:
        delete = True
        for role in message.author.roles:
            if role.name.lower() in [ignore for ignore in koza_settings.profanity_ignore_groups]:
                delete = False

        if delete:
            log_channel = get_log_channel(koza_settings.log_channel)
            await log_channel.send(message.author.name + ": " + msg)
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
