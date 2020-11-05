import discord
from discord.ext import commands
import asyncio
import os
import settings


intents = discord.Intents.default()
intents.members = True

ss_token = str(os.environ.get('SS_BOT_TOKEN'))
rl_token = str(os.environ.get('RL_BOT_TOKEN'))

koza = commands.Bot(command_prefix=settings.PREFIX, intents=intents)
raven_lord = commands.Bot(command_prefix=settings.PREFIX, intents=intents)

koza.load_extension('bots.koza')
raven_lord.load_extension('bots.ravenlord')

loop = asyncio.get_event_loop()
loop.create_task(koza.start(ss_token))
loop.create_task(raven_lord.start(rl_token))
loop.run_forever()
