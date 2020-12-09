import discord
from discord.ext import commands
from discord.ext import tasks
from discord.utils import get
import os
import random
import time
import sys
import traceback
import youtube_dl
import settings
from bots import koza_interactions
import functions
import user_level_data
import DB
import youtube_module


class Koza(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_task.start()

    @tasks.loop(seconds=3600.0)
    async def status_task(self):
        status = random.randint(1, 3)

        if status == 1:
            await self.bot.change_presence(status=discord.Status.online,
                                           activity=discord.Game(random.choice(koza_interactions.games)), )
        elif status == 2:
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                     name=random.choice(koza_interactions.watching)))
        elif status == 3:
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening,
                                                                     name=random.choice(koza_interactions.listening)))

    @status_task.before_loop
    async def before_printer(self):
        print('waiting...')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            pass
        else:
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as ---->", self.bot.user)

    @commands.Cog.listener()
    async def on_message_edit(self, message_before, message_after):
        msg = message_after.content.lower()
        server = self.bot.get_guild(int(os.environ.get('SERVER_ID')))

        # profanity_filter
        bot_react = functions.check_message(msg)

        if bot_react[0]:
            delete = functions.is_not_ignore_group(message_after.author.roles)

            if delete:
                log_channel = functions.get_channel(settings.log_channel, server)
                if log_channel is not None:
                    await log_channel.send(
                        message_after.author.display_name + ": " + msg + "\n" "Плохое слово: " + bot_react[1])

                await message_after.delete()
                async with message_after.channel.typing():
                    time.sleep(1)
                await message_after.channel.send(koza_interactions.scream)
                return

        # koza
        msg_before = message_before.content.lower()

        if "коза орет" in msg_before and "коза орет" not in msg:
            async with message_after.channel.typing():
                time.sleep(1)

            emb = discord.Embed(title=f"Действия козы:",
                                description=f"Коза с подозрением смотрит на {message_after.author.display_name} "
                                            f"и не хочет, чтобы с ней так шутили!",
                                color=0x00ff00)

            await message_before.channel.send(embed=emb)

    @commands.Cog.listener()
    async def on_message(self, message):
        msg = message.content.lower()
        server = self.bot.get_guild(int(os.environ.get('SERVER_ID')))

        # profanity_filter
        bot_react = functions.check_message(msg)

        if bot_react[0]:
            delete = functions.is_not_ignore_group(message.author.roles)

            if delete:
                log_channel = functions.get_channel(settings.log_channel, server)
                if log_channel is not None:
                    await log_channel.send(message.author.display_name + ": " +
                                           msg + "\n" "Плохое слово: " + bot_react[1])

                await message.delete()
                async with message.channel.typing():
                    time.sleep(1)
                await message.channel.send(koza_interactions.scream)
                return

        # interactions
        if msg.find("репортаж козы с места событий") != -1:
            async with message.channel.typing():
                time.sleep(1)
            await message.channel.send("https://www.youtube.com/watch?v=SIaFtAKnqBU")
        elif koza_interactions.scream_respond in msg:
            async with message.channel.typing():
                time.sleep(1)
            await message.channel.send(koza_interactions.scream)
        elif any(word in msg for word in koza_interactions.respond):
            async with message.channel.typing():
                time.sleep(1)

            text = random.choice(koza_interactions.reaction).format(message.author.display_name)

            emb = discord.Embed(title=f"Действия козы:",
                                description=text,
                                color=0x00ff00)

            await message.channel.send(embed=emb)

        # level system
        for role in message.author.roles:
            if role.name.lower() in [ignore for ignore in user_level_data.ignore_group]:
                return

        author_id = message.author.id
        guild_id = message.guild.id

        u_id = {"id": author_id}

        if message.author == self.bot.user:
            return

        if message.author.bot:
            return

        collection = DB.collection
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
            if cur_name != message.author.display_name:
                new_name = message.author.display_name

            if new_xp >= user_level_data.exp_data[cur_level][2]:
                new_level = cur_level+1
                new_xp = 0

                server_id = self.bot.get_guild(int(os.environ.get('SERVER_ID')))

                for role in message.author.roles:
                    if role.name == "@everyone":
                        continue

                    await message.author.remove_roles(role)

                role = get(server_id.roles, name=user_level_data.exp_data[new_level][1])
                if role is not None and role not in message.author.roles:
                    await message.author.add_roles(role)

                    if role.name != user_level_data.exp_data[1][1]:
                        com_channel = functions.get_channel(settings.command_channel, server)

                        if com_channel is not None:
                            emb = discord.Embed(title=f"Система оповещения \"Koza v2.1.3.4.5\"",
                                                description=f"Коза присваивает {message.author.display_name} "
                                                            f"звание \"{role.name}\"",
                                                color=0x00ff00)

                            await com_channel.send(embed=emb)

            collection.update_one({"id": author_id}, {"$set": {"xp": new_xp}}, upsert=True)
            collection.update_one({"id": author_id}, {"$set": {"level": new_level}}, upsert=True)
            collection.update_one({"id": author_id}, {"$set": {"user_name": new_name}}, upsert=True)

        # await message.channel.send("updated")

    @commands.command(brief='- Server online')
    @functions.is_channel(settings.command_channel)
    async def users(self, ctx):
        server_id = self.bot.get_guild(int(os.environ.get('SERVER_ID')))
        async with ctx.typing():
            time.sleep(1)
        await ctx.send(f"""Количество пользователей: {server_id.member_count}""")

    @commands.command(brief='- Remove messages from channel')
    @functions.is_channel(settings.command_channel)
    async def clear(self, ctx, channel, number):
        delete = functions.is_moderation_group(ctx.author.roles)

        if not delete or not number.isdigit():
            emb = discord.Embed(title=f"Предупреждение",
                                description=f"Вы не администратор. Вам не доступна эта команда!",
                                color=0x00ff00)

            async with ctx.typing():
                time.sleep(1)
            await ctx.channel.send(embed=emb)
            return

        server = self.bot.get_guild(int(os.environ.get('SERVER_ID')))
        channel_purge = functions.get_channel(str(channel), server)

        if channel_purge is None:
            return

        number = int(number)
        await channel_purge.purge(limit=number)

    @commands.command(brief='- Show your rank')
    @functions.is_channel(settings.command_channel)
    async def rank(self, ctx):
        author_id = ctx.author.id
        u_id = {"id": author_id}
        collection = DB.collection

        if collection.count_documents(u_id) == 0:
            emb = discord.Embed(title=f"Профиль {ctx.author.display_name}",
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

        emb = discord.Embed(title=f"Профиль {ctx.author.display_name}",
                            description=f"Уровень: {cur_level} \n"
                                        f"Текущий опыт: {cur_xp} ед. \n"
                                        f"До следующего уровня: {user_level_data.exp_data[cur_level][2] - cur_xp} ед.",
                            color=0x00ff00)

        async with ctx.typing():
            time.sleep(1)
        await ctx.channel.send(embed=emb)

    @commands.command(brief='- Show server rank rewards')
    @functions.is_channel(settings.command_channel)
    async def rewards(self, ctx):
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
                                        f"10 уровень: {user_level_data.exp_data[10][1]} \n"
                                        f"11 уровень: {user_level_data.exp_data[11][1]} \n"
                                        f"12 уровень: {user_level_data.exp_data[12][1]} \n",
                            color=0x00ff00)

        async with ctx.typing():
            time.sleep(1)
        await ctx.channel.send(embed=emb)

    @commands.command(brief='- Koza join to KozaDJ channel')
    @functions.is_channel(settings.command_channel)
    async def koza_dj_start(self, ctx):
        server = self.bot.get_guild(int(os.environ.get('SERVER_ID')))
        channel = discord.utils.get(server.voice_channels, name="KozaDJ")
        if channel is not None and ctx.guild.voice_client is None:
            await channel.connect()

    @commands.command(brief='- Koza leave your party')
    @functions.is_channel(settings.command_channel)
    async def koza_dj_stop(self, ctx):
        if ctx.guild.voice_client is not None:
            await ctx.guild.voice_client.disconnect()  # Leave the channel

    @commands.command(brief='- Koza play music from youtube')
    @functions.is_channel(settings.command_channel)
    async def koza_dj_play(self, ctx, url: str):
        max_length = 15

        if len(url) > max_length or url.find("http") != -1:
            emb = discord.Embed(title=f"Коза диджей",
                                description=f"Коза орет с тебя!",
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

        url = "https://www.youtube.com/watch?v=" + url

        def finish(file_name):
            print(f"{file_name} has finished")

        async with ctx.typing():
            try:
                player = await youtube_module.YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                ctx.voice_client.play(player, after=finish(player.title))
                voice.source = discord.PCMVolumeTransformer(voice.source)
                voice.source.volume = 0.3

                emb = discord.Embed(title=f"Коза диджей",
                                    description=f"Сейчас играет: {player.title}",
                                    color=0x00ff00)

                await ctx.channel.send(embed=emb)
            except youtube_dl.utils.DownloadError:
                finish("ERROR")

                async with ctx.typing():
                    time.sleep(1)

                emb = discord.Embed(title=f"Коза диджей",
                                    description=f"Что-то пошло не так.",
                                    color=0x00ff00)

                await ctx.channel.send(embed=emb)

    @commands.command(brief='- Remake ranks for all server users')
    @functions.is_channel(settings.command_channel)
    async def remake_ranks(self, ctx):
        access = functions.is_moderation_group(ctx.author.roles)

        if not access:
            emb = discord.Embed(title=f"Предупреждение",
                                description=f"Вы не администратор. Вам не доступна эта команда!",
                                color=0x00ff00)

            async with ctx.typing():
                time.sleep(1)
            await ctx.channel.send(embed=emb)
            return

        server = self.bot.get_guild(int(os.environ.get('SERVER_ID')))
        collection = DB.collection

        for member in server.members:
            u_id = {"id": member.id}

            if collection.count_documents(u_id) == 0:
                continue

            user_data = collection.find(u_id)

            for role in member.roles:
                if role.name == "@everyone":
                    continue

                await member.remove_roles(role)

            for user in user_data:
                role = get(server.roles, name=user_level_data.exp_data[user["level"]][1])
                if role is not None:
                    await member.add_roles(role)
                    print("Роль пользователя " + member.display_name + " переназначена на " + role.name)


def setup(main):
    main.add_cog(Koza(main))
