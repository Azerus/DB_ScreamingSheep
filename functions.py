from discord.ext import commands
import profanity_filter
import settings


def check_message(msg):
    for word in profanity_filter.bad_words:
        if msg.find(word) != -1:
            return [True, word]

    return [False, ""]


def is_not_ignore_group(roles):
    for role in roles:
        if role.name.lower() in [ignore for ignore in profanity_filter.profanity_ignore_groups]:
            return False

    return True


def is_moderation_group(roles):
    for role in roles:
        if role.name.lower() in [ignore for ignore in settings.moderation_groups]:
            return True

    return False


def get_channel(name, server_id):
    for channel in server_id.channels:
        if channel.name == name:
            return channel

    return None


def is_channel(name):
    def predicate(ctx):
        return ctx.message.channel.name == name

    return commands.check(predicate)
