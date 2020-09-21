import discord
import profanity_filter
import os
import time
import koza_settings


PREFIX = "!"


def check_message(msg):
    for word in profanity_filter.bad_words:
        if msg.find(word) != -1:
            return True

    return False


# token = read_token()
token = str(os.environ.get('BOT_TOKEN'))

client = discord.Client()


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('Наблюдаю за тобой!'), )


@client.event
async def on_message(message):
    channels = ["загон"]

    msg = message.content.lower()

    # profanity_filter
    bot_react = check_message(msg)

    if bot_react:
        delete = True
        for role in message.author.roles:
            if role.name.lower() in [ignore for ignore in koza_settings.profanity_ignore_groups]:
                delete = False

        if delete:
            await message.delete()
            time.sleep(1)
            await message.channel.send("AAAAAAAAAAAAAA!")
            return

    # commands
    if str(message.channel) in koza_settings.command_channel:
        if msg == '{}help'.format(PREFIX):
            await command_help(message.channel)
        elif msg == '{}users'.format(PREFIX):
            await command_users(message.channel)
        elif "загон" not in [y.name.lower() for y in message.author.roles]:
            await message.delete()
    elif msg.find("коза") != -1:
        time.sleep(1)
        await message.channel.send("AAAAAAAAAAAAAA!")


async def command_help(channel):
    emb = discord.Embed(title='Навигация по командам')
    emb.add_field(name='{}help'.format(PREFIX), value='Список команд')
    await channel.send(embed=emb)


async def command_users(channel):
    # emb = discord.Embed(title='Пользователи')
    # emb.add_field(name='{}help'.format(PREFIX), value='Список команд')
    server_id = client.get_guild(int(os.environ.get('SERVER_ID')))
    await channel.send(f"""Количество пользователей: {server_id.member_count}""")

client.run(token)
