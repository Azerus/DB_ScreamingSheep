import discord
from discord.ext import commands
import logging


class Amadeus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as ---->", self.bot.user)
        await self.bot.change_presence(status=discord.Status.invisible)

    @commands.command()
    async def join2(self, ctx):
        logging.info(f"Joined guild {ctx.author.name}")


def setup(main):
    main.add_cog(Amadeus(main))
