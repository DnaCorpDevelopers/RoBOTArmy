# bot.py
import os

import discord

from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
BASE_DIR = os.path.dirname(os.path.realpath(__file__))

os.environ['STORAGE_LANGUAGES'] = os.path.join(BASE_DIR, 'storage', 'languages')
os.environ['STORAGE_IMAGES'] = os.path.join(BASE_DIR, 'storage', 'images')

TOKEN: str = os.getenv('DISCORD_TOKEN')
GUILD: str = os.getenv('DISCORD_GUILD')
CHANNEL: str = os.getenv('DISCORD_CHANNEL')

bot = commands.Bot(command_prefix='$', description='Just a Barman')

initial_extensions = ['cogs.manage', 'cogs.barman']

if __name__ == '__main__':
    for extension in initial_extensions:
        bot.load_extension(extension)


@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    guild: discord.Guild = discord.utils.get(bot.guilds, name=GUILD)

    print(
        f'{bot.user} is connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')


bot.run(TOKEN, bot=True, reconnect=True)
