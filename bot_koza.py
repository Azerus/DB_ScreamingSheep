import discord
from discord.ext import commands
import os

Bot = commands.Bot(command_prefix="!")
Bot.remove_command('help')

# token = read_token()
token = str(os.environ.get('BOT_TOKEN'))


@Bot.event
async def on_ready():
    await Bot.change_presence(status=discord.Status.online, activity=discord.Game('Наблюдаю за тобой!'), )

Bot.run(token)
