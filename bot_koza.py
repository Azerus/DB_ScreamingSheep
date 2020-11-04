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
import youtube_dl


token = str(os.environ.get('BOT_TOKEN'))
intents = discord.Intents.default()
intents.members = True
client = commands.Bot(command_prefix=koza_settings.PREFIX, intents=intents)

cluster = MongoClient(str(os.environ.get('DB')))
db = cluster["discord"]
collection = db["user_data"]
music_status = koza_settings.MusicStatus.NONE
music_collection = ["", "", "", "", ""]
max_music = 5

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    "options": "-vn -loglevel quiet -hide_banner -nostats",
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 0 -nostdin"
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


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

    # max_length = 25
    # name = koza_settings.special[0:max_length]
    # if len(koza_settings.special) > max_length:
    #     name += "..."

    # activity = discord.Game(name=name, application_id=501063122581454849, state="1194630", details="asd")
    # await client.change_presence(status=discord.Status.online, activity=activity)

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
            async with message.channel.typing():
                time.sleep(1)
            await message.channel.send("AAAAAAAAAAAAAA!")
            return

    # commands
    if str(message.channel) in koza_settings.command_channel:
        await client.process_commands(message)
        return
        # if "загон" not in [y.name.lower() for y in message.author.roles]:
            # await message.delete()
    elif msg.find("репортаж козы с места событий") != -1:
        async with message.channel.typing():
            time.sleep(1)
        await message.channel.send("https://www.youtube.com/watch?v=SIaFtAKnqBU")
    elif msg.find("коза орет") != -1:
        async with message.channel.typing():
            time.sleep(1)
        await message.channel.send("AAAAAAAAAAAAAA!")
    elif msg.find("коза") != -1 or msg.find("козу") != -1 or msg.find("козы") != -1 or msg.find("козой") != -1 or msg.find("козе") != -1:
        async with message.channel.typing():
            time.sleep(1)

        text = random.choice(koza_settings.reaction).format(message.author.name)

        emb = discord.Embed(title=f"Действия козы:",
                            description=text,
                            color=0x00ff00)

        await message.channel.send(embed=emb)

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
        cur_name = user["user_name"]
        if cur_level >= user_level_data.max_level:
            return

        new_xp = cur_xp + 1
        new_level = cur_level
        new_name = cur_name
        if cur_name != message.author.name:
            new_name = message.author.name

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
        collection.update_one({"id": author_id}, {"$set": {"user_name": new_name}}, upsert=True)

    # await message.channel.send("updated")


@client.command(brief='- Server online')
async def users(ctx):
    # emb = discord.Embed(title='Пользователи')
    # emb.add_field(name='{}help'.format(PREFIX), value='Список команд')
    server_id = client.get_guild(int(os.environ.get('SERVER_ID')))
    async with ctx.typing():
        time.sleep(1)
    await ctx.send(f"""Количество пользователей: {server_id.member_count}""")


@client.command(brief='- Remove messages from channel')
async def clear(ctx, channel, number):
    delete = False

    for role in ctx.author.roles:
        if role.name.lower() in [ignore for ignore in koza_settings.moderation_groups]:
            delete = True

    if not delete or not number.isdigit():
        emb = discord.Embed(title=f"Предупреждение",
                            description=f"Вы не администратор. Вам не доступна эта команда!",
                            color=0x00ff00)

        async with ctx.typing():
            time.sleep(1)
        await ctx.channel.send(embed=emb)
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

        async with ctx.typing():
            time.sleep(1)
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

    async with ctx.typing():
        time.sleep(1)
    await ctx.channel.send(embed=emb)


@client.command(brief='- Show server rank rewards')
async def rewards(ctx):
    emb = discord.Embed(title=f"Награды сервера",
                        description=f"1 уровень: {user_level_data.exp_data[1][1]} \n"
                                    f"2 уровень: {user_level_data.exp_data[2][1]} \n"
                                    f"3 уровень: {user_level_data.exp_data[3][1]} \n"
                                    f"4 уровень: {user_level_data.exp_data[4][1]} \n"
                                    f"5 уровень: {user_level_data.exp_data[5][1]} \n"
                                    f"6 уровень: {user_level_data.exp_data[6][1]} \n"
                                    f"7 уровень: {user_level_data.exp_data[7][1]} \n"
                                    f"8 уровень: {user_level_data.exp_data[8][1]} \n"
                                    f"9 уровень: {user_level_data.exp_data[9][1]} \n"
                                    f"10 уровень: {user_level_data.exp_data[10][1]} \n",
                        color=0x00ff00)

    async with ctx.typing():
        time.sleep(1)
    await ctx.channel.send(embed=emb)


@client.command(brief='- Koza join to your party')
async def koza_dj_start(ctx):
    server_id = client.get_guild(int(os.environ.get('SERVER_ID')))
    channel = discord.utils.get(server_id.voice_channels, name="KozaDJ")
    if channel is not None and ctx.guild.voice_client is None:
        await channel.connect()


@client.command(brief='- Koza leave your party')
async def koza_dj_stop(ctx):
    if ctx.guild.voice_client is not None:
        await ctx.guild.voice_client.disconnect() # Leave the channel


@client.command(brief='- Koza play music from youtube')
async def koza_dj_play(ctx, url: str):
    global music_status
    max_length = 15

    if len(url) > max_length or url.find("http") != -1:
        emb = discord.Embed(title=f"Коза диджей",
                            description=f"Коза орет с тебя!",
                            color=0x00ff00)

        async with ctx.typing():
            time.sleep(1)
        await ctx.channel.send(embed=emb)
        return

    if music_status != koza_settings.MusicStatus.NONE:
        error_text = "none"
        if music_status == koza_settings.MusicStatus.PLAYING:
            error_text = "Играет трек. Подождите."

        emb = discord.Embed(title=f"Коза диджей",
                            description=error_text,
                            color=0x00ff00)

        async with ctx.typing():
            time.sleep(1)
        await ctx.channel.send(embed=emb)
        return

    voice = ctx.guild.voice_client

    if voice is None:
        emb = discord.Embed(title=f"Коза диджей",
                            description=f"Коза не войс чате!",
                            color=0x00ff00)

        async with ctx.typing():
            time.sleep(1)
        await ctx.channel.send(embed=emb)
        return

    music_status = koza_settings.MusicStatus.PLAYING

    url = "https://www.youtube.com/watch?v=" + url

    def finish(file_name):
        print(f"{file_name} has finished")
        global music_status
        music_status = koza_settings.MusicStatus.NONE

    """Streams from a url (same as yt, but doesn't predownload)"""
    async with ctx.typing():
        try:
            player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
            ctx.voice_client.play(player, after=lambda e: finish(player.title))
            voice.source = discord.PCMVolumeTransformer(voice.source)
            voice.source.volume = 0.3

            emb = discord.Embed(title=f"Коза диджей",
                                description=f"Сейчас играет: {player.title}",
                                color=0x00ff00)

            await ctx.channel.send(embed=emb)
        except youtube_dl.utils.DownloadError as e:
            finish("ERROR")

            async with ctx.typing():
                time.sleep(1)

            emb = discord.Embed(title=f"Коза диджей",
                                description=f"Что-то пошло не так.",
                                color=0x00ff00)

            await ctx.channel.send(embed=emb)


@client.command(brief='- Remake ranks for all server users')
async def remake_ranks(ctx):
    access = False

    for role in ctx.author.roles:
        if role.name.lower() in [ignore for ignore in koza_settings.moderation_groups]:
            access = True

    if not access:
        emb = discord.Embed(title=f"Предупреждение",
                            description=f"Вы не администратор. Вам не доступна эта команда!",
                            color=0x00ff00)

        async with ctx.typing():
            time.sleep(1)
        await ctx.channel.send(embed=emb)
        return

    server_id = client.get_guild(int(os.environ.get('SERVER_ID')))
    for member in server_id.members:
        u_id = {"id": member.id}

        if collection.count_documents(u_id) == 0:
            continue

        user_data = collection.find(u_id)
        cur_level = 0

        for role in member.roles:
            if role.name == "@everyone":
                continue

            await member.remove_roles(role)

        for user in user_data:
            cur_level = user["level"]
            role = get(server_id.roles, name=user_level_data.exp_data[cur_level][1])
            if role is not None:
                await member.add_roles(role)
                print("Роль пользователя " + member.name + " переназначена на " + role.name)


client.run(token)
