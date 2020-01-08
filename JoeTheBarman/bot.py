# bot.py
import logging
import os

import discord

from discord.ext import commands
from commons.utils import setup_logging

setup_logging()
log = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

os.environ['STORAGE_LANGUAGES'] = os.path.join(BASE_DIR, 'storage', 'languages')
os.environ['STORAGE_IMAGES'] = os.path.join(BASE_DIR, 'storage', 'images')

TOKEN: str = os.getenv('DISCORD_TOKEN')
GUILD: str = os.getenv('DISCORD_GUILD')

bot = commands.Bot(command_prefix='$', description='Just a Barman')

initial_extensions = ['commons.cogs.manage', 'JoeTheBarman.cogs.barman']

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    guild: discord.Guild = discord.utils.get(bot.guilds, name=GUILD)

    log.info(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )


bot.run(TOKEN, bot=True, reconnect=True)
