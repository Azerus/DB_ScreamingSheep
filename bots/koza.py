import discord
from discord.ext import commands
from discord.ext import tasks
import os
import random
import time
import sys
import traceback
import youtube_dl
import settings
from bots import koza_interactions
import functions
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
        print('Loading Koza...')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CheckFailure):
            pass
        elif isinstance(error, commands.errors.CommandNotFound):
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


def setup(main):
    main.add_cog(Koza(main))
