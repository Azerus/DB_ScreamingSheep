import discord
import profanity_filter
import os

PREFIX = '!'


def read_token():
    with open("token.txt", "r") as f:
        lines = f.readlines()
        return lines[0].strip()


def check_message(message):
    msg = message.content.lower()

    for word in profanity_filter.bad_words:
        if msg.find(word) != -1:
            return True

    return False


# token = read_token()
token = os.environ.get('BOT_TOKEN')

client = discord.Client()


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Наблюдаю за тобой!'), )


@client.event
async def on_message(message):
    channels = ["загон"]

    # profanity_filter
    bot_react = check_message(message)

    if bot_react:
        await message.delete()
        await message.channel.send("AAAAAAAAAAAAAA!")

    # commands
    if str(message.channel) in channels:
        if message.content.find("коза") != -1:
            await message.channel.send("AAAAAAAAAAAAAA!")
        elif message.content == '{}help'.format(PREFIX):
            await command_help(message.channel)
        elif message.content == '{}users'.format(PREFIX):
            await command_users(message.channel)


async def command_help(channel):
    emb = discord.Embed(title='Навигация по командам')
    emb.add_field(name='{}help'.format(PREFIX), value='Список команд')
    await channel.send(embed=emb)


async def command_users(channel):
    # emb = discord.Embed(title='Пользователи')
    # emb.add_field(name='{}help'.format(PREFIX), value='Список команд')
    server_id = os.environ.get('SERVER_ID')
    await channel.send(f"""Количество пользователей: {server_id.member_count}""")

client.run(token)
