import discord
from discord.ext import commands
from discord.utils import get
import profanity_filter
import os
import time
import koza_settings
import random
import asyncio
import pymongo
from pymongo import MongoClient
import user_level_data


token = str(os.environ.get('BOT_TOKEN'))
client = commands.Bot(command_prefix=koza_settings.PREFIX)

cluster = MongoClient(str(os.environ.get('DB')))
db = cluster["discord"]
collection = db["user_data"]
# client = discord.Client()


def check_message(msg):
    for word in profanity_filter.bad_words:
        if msg.find(word) != -1:
            return [True, word]

    return [False, ""]


def get_channel(name):
    for channel in client.get_guild(int(os.environ.get('SERVER_ID'))).channels:
        if channel.name == name:
            return channel

    return None


async def status_task():
    while True:
        status = random.randint(1, 3)

        if status == 1:
            await client.change_presence(status=discord.Status.online,
                                         activity=discord.Game(random.choice(koza_settings.games)), )
        elif status == 2:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                   name=random.choice(koza_settings.watching)))
        elif status == 3:
            await client.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
                                                                   name=random.choice(koza_settings.listening)))

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
            log_channel = get_channel(koza_settings.log_channel)
            if log_channel is not None:
                await log_channel.send(message.author.name + ": " + msg + "\n" "Плохое слово: " + bot_react[1])

            await message.delete()
            time.sleep(1)
            await message.channel.send("AAAAAAAAAAAAAA!")
            return

    # commands
    if str(message.channel) in koza_settings.command_channel:
        await client.process_commands(message)
        return
        # if "загон" not in [y.name.lower() for y in message.author.roles]:
            # await message.delete()
    elif msg.find("коза") != -1:
        time.sleep(1)
        await message.channel.send("AAAAAAAAAAAAAA!")

    # level system
    for role in message.author.roles:
        if role.name.lower() in [ignore for ignore in koza_settings.level_system_ignore]:
            return

    author_id = message.author.id
    guild_id = message.guild.id

    u_id = {"id": author_id}

    if message.author == client.user:
        return

    if message.author.bot:
        return

    if collection.count_documents(u_id) == 0:
        user_info = {"id": author_id, "guild_id": guild_id, "user_name": message.author.name, "level": 0, "xp": 0}
        collection.insert_one(user_info)

    user_data = collection.find(u_id)

    for user in user_data:
        cur_xp = user["xp"]
        cur_level = user["level"]

        if cur_level >= user_level_data.max_level:
            return

        new_xp = cur_xp + 1
        new_level = cur_level

        if new_xp >= user_level_data.exp_data[cur_level][2]:
            new_level = cur_level+1
            new_xp = 0

            server_id = client.get_guild(int(os.environ.get('SERVER_ID')))

            role = get(server_id.roles, name=user_level_data.exp_data[cur_level][1])
            if role is not None:
                await message.author.remove_roles(role)

            role = get(server_id.roles, name=user_level_data.exp_data[new_level][1])
            if role is not None:
                await message.author.add_roles(role)

    collection.update_one({"id": author_id}, {"$set": {"xp": new_xp}}, upsert=True)
    collection.update_one({"id": author_id}, {"$set": {"level": new_level}}, upsert=True)

    # await message.channel.send("updated")


@client.command(brief='- Server online')
async def users(ctx):
    # emb = discord.Embed(title='Пользователи')
    # emb.add_field(name='{}help'.format(PREFIX), value='Список команд')
    server_id = client.get_guild(int(os.environ.get('SERVER_ID')))
    await ctx.send(f"""Количество пользователей: {server_id.member_count}""")


@client.command(brief='- Remove messages from channel')
async def clear(ctx, channel, number):
    delete = False

    for role in ctx.author.roles:
        if role.name.lower() in [ignore for ignore in koza_settings.moderation_groups]:
            delete = True

    if not delete or not number.isdigit():
        return

    channel_purge = get_channel(str(channel))

    if channel_purge is None:
        return

    number = int(number)
    await channel_purge.purge(limit=number)


@client.command(brief='- Show your rank')
async def rank(ctx):

    author_id = ctx.author.id

    u_id = {"id": author_id}

    if collection.count_documents(u_id) == 0:
        emb = discord.Embed(title=f"Профиль {ctx.author.name}",
                            description=f"У вас нет системы уровня!!!",
                            color=0x00ff00)

        await ctx.channel.send(embed=emb)
        return

    user_data = collection.find(u_id)

    cur_xp = 0
    cur_level = 0

    for user in user_data:
        cur_xp = user["xp"]
        cur_level = user["level"]

    emb = discord.Embed(title=f"Профиль {ctx.author.name}",
                        description=f"Уровень: {cur_level} \n"
                                    f"Текущий опыт: {cur_xp} ед. \n"
                                    f"До следующего уровня: {user_level_data.exp_data[cur_level][2] - cur_xp} ед.",
                        color=0x00ff00)

    await ctx.channel.send(embed=emb)


@client.command(brief='- Show server rank rewards')
async def rewards(ctx):
    emb = discord.Embed(title=f"Награды сервера",
                        description=f"1 уровень: {user_level_data.exp_data[1][1]} \n"
                                    f"2 уровень: {user_level_data.exp_data[2][1]} \n"
                                    f"3 уровень: {user_level_data.exp_data[3][1]} \n"
                                    f"4 уровень: {user_level_data.exp_data[4][1]} \n"
                                    f"5 уровень: {user_level_data.exp_data[5][1]} \n",
                        color=0x00ff00)

    await ctx.channel.send(embed=emb)

client.run(token)
