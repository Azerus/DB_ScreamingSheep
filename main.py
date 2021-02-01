import discord
from discord.ext import commands
import asyncio
import os
import settings


intents = discord.Intents.default()
intents.members = True

ss_token = str(os.environ.get('SS_BOT_TOKEN'))
am_token = str(os.environ.get('AM_BOT_TOKEN'))

koza = commands.Bot(command_prefix=settings.PREFIX, intents=intents)
amadeus = commands.Bot(command_prefix=settings.PREFIX, intents=intents)

koza.load_extension('bots.koza')
amadeus.load_extension('bots.amadeus')

loop = asyncio.get_event_loop()
loop.create_task(koza.start(ss_token))
loop.create_task(amadeus.start(am_token))
loop.run_forever()
