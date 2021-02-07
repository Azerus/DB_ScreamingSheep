import discord
from discord.ext import commands
import os
import functions
import settings
import time
import random
from bots import amadeus_interactions


class Amadeus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command("help")

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as ---->", self.bot.user)
        await self.bot.change_presence(status=discord.Status.invisible)

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
                    emb = discord.Embed(title=f"Оповещение о нарушении",
                                        description=f"{message.author.display_name}" + ": " + f"{msg} \n"
                                                    f"Плохое слово: {bot_react[1]}",
                                        color=0x00ff00)

                    await log_channel.send(embed=emb)

                async with message.channel.typing():
                    time.sleep(1)
                await message.reply(random.choice(amadeus_interactions.profanity_answer))
                return


def setup(main):
    main.add_cog(Amadeus(main))
