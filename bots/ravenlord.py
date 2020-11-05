import discord
from discord.ext import commands


class RavenLord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as ---->", self.bot.user)

    @commands.command()
    async def join(self, ctx):
        print('client2 ready')


def setup(bot):
    bot.add_cog(RavenLord(bot))