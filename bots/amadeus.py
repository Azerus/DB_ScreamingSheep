import discord
import dialogflow
from google.api_core.exceptions import InvalidArgument
from discord.ext import commands
from discord.utils import get
from discord.ext import tasks
import os
import sys
import traceback
import functions
import settings
import user_level_data
import DB
import time
import random
from bots import amadeus_interactions


class Amadeus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.status_task.start()

    @tasks.loop(seconds=4100.0)
    async def status_task(self):
        status = random.randint(1, 2)

        if status == 1:
            await self.bot.change_presence(status=discord.Status.invisible)

        elif status == 2:
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching,
                                                                     name=random.choice(amadeus_interactions.watching)))

    @status_task.before_loop
    async def before_printer(self):
        print('Loading Amadeus...')
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as ---->", self.bot.user)

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
                    emb = discord.Embed(title=f"Оповещение о нарушении",
                                        description=f"{message_after.author.display_name}" + ": " + f"{msg} \n"
                                                    f"Плохое слово: {bot_react[1]}",
                                        color=0x00ff00)

                    await log_channel.send(embed=emb)

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

                answer = random.choice(amadeus_interactions.profanity_answer)
                count = len(answer)
                async with message.channel.typing():
                    time.sleep(0.1 * count)
                await message.reply(answer)
                return

        # AmadeusAI
        bot_ai = False

        if self.bot.user.mentioned_in(message):
            bot_ai = True

        if bot_ai is True:

            if message.author != self.bot.user:
                DIALOGFLOW_PROJECT_ID = 'small-talk-c9av'
                DIALOGFLOW_LANGUAGE_CODE = 'ru'
                SESSION_ID = 'me'
                session_client = dialogflow.SessionsClient()
                session = session_client.session_path(DIALOGFLOW_PROJECT_ID, SESSION_ID)
                text_input = dialogflow.types.TextInput(text=message.content, language_code=DIALOGFLOW_LANGUAGE_CODE)
                query_input = dialogflow.types.QueryInput(text=text_input)
                try:
                    response = session_client.detect_intent(session=session, query_input=query_input)
                except InvalidArgument:
                    raise

                answer = response.query_result.fulfillment_text
                if answer is None or answer == '':
                    answer = random.choice(amadeus_interactions.not_understand)

                count = len(answer)

                async with message.channel.typing():
                    time.sleep(0.1 * count)
                await message.reply(answer)

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
                            reward_text = random.choice(amadeus_interactions.reward_messages)
                            await com_channel.send(reward_text.format(message.author.mention, role.mention))

            collection.update_one({"id": author_id}, {"$set": {"xp": new_xp}}, upsert=True)
            collection.update_one({"id": author_id}, {"$set": {"level": new_level}}, upsert=True)
            collection.update_one({"id": author_id}, {"$set": {"user_name": new_name}}, upsert=True)

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

    @commands.command(brief='- Server online')
    @functions.is_channel(settings.command_channel)
    async def users(self, ctx):
        server_id = self.bot.get_guild(int(os.environ.get('SERVER_ID')))
        async with ctx.typing():
            time.sleep(1)
        await ctx.send(f"""Количество пользователей: {server_id.member_count}""")


def setup(main):
    main.add_cog(Amadeus(main))
