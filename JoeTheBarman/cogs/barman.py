import json
import logging
import os
import random
import re

import discord
from discord import Message
from discord.ext import commands

logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(levelname)s : %(message)s')
log = logging.getLogger('BasicBot')

images_dir = os.getenv('STORAGE_IMAGES')
drinks_file = os.path.join(os.getenv('STORAGE_LANGUAGES'), 'drinks.it.json')
convs_file = os.path.join(os.getenv('STORAGE_LANGUAGES'), 'conversations.it.json')


class Drink:
    def __init__(self, js):
        self.keys = js['key'].split(' ')
        self.name = js['name']
        self.img = js['img']

    def get_file(self):
        return discord.File(os.path.join(images_dir, self.img), filename="drink.png")

    def get_embed(self):
        embed = discord.Embed()
        embed.set_image(url=f'attachment://{self.img}')
        return embed


def load_drinks():
    file_list = json.load(open(drinks_file, 'r', encoding='utf-8'))
    drink_map = {}
    drink_list = []
    for d in file_list:
        drink = Drink(d)
        drink_list.append(drink)
        for k in drink.keys:
            drink_map[k] = drink

    return drink_list, drink_map


drink_list, drink_map = load_drinks()
convs = json.load(open(convs_file, 'r', encoding='utf-8'))


class Barman(commands.Cog):

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.user = bot.user

        self.orders = {}
        self.customers = set()

    def _checkCall(self, message: Message):
        content = message.content.lower()

        # must contain 'joe' or 'barman' or be in the watching list
        return any(x in content for x in convs['names']) or message.author in self.customers

    def _serveDrinks(self, message: Message):
        mentions = message.mentions

        content = message.content
        clean = re.sub('[^A-Za-z0-9 ]+', ' ', content.lower())
        tokens = clean.split(' ')

        log.debug('tokens: ' + str(tokens))

        # search for any kind of drink
        found_drinks = [d for k, d in drink_map.items() if k in tokens]

        mention = message.author.mention
        title = random.choice(convs['titles'])

        if len(found_drinks) == 0:
            log.info('send generic order request')
            self.customers.add(message.author)
            return random.choice(convs['orders']).format(message.author.mention), None

        if message.author in self.customers:
            self.customers.remove(message.author)

        if len([a for a in convs['thankAnswer'] if a in tokens]) > 0 and len(found_drinks) == 0:
            # get a random thank string
            log.info('send thanks')
            # TODO: increase reputation
            return random.choice(convs['thanks']).format(title), None

        if len([d for d in convs['drinkList'] if d in tokens]) > 0:
            # return the list of drinks
            log.info('send drink list')
            incipit = random.choice(convs['drinkListIncipit'])
            drinks = '\n - '.join([d.name for d in drink_list])
            return f'{incipit}\n{drinks}', None

        if len(found_drinks) < 1:
            # if we haven't found a valid drink
            log.info('send not found ' + str(tokens))
            return random.choice(convs['notFound']), None

        # we found a drink!
        found_drink = found_drinks[0]

        if convs['everybodyRequest'] in tokens or message.mention_everyone:
            # if it is for @everyone or contains a special token
            log.info('send offer to everyone')
            return random.choice(convs['sendToEveryone']).format(
                mention, title, found_drink.name
            ), found_drink.img

        if len(mentions) > 0:
            # if we have mentions, notify to them
            log.info('offer to user')
            mens = ', '.join([str(m.mention) for m in mentions])
            offer = random.choice(convs['offers'])

            intro = f'{mens}, {mention} {offer}'
        else:
            # just answer the client
            log.info('answer the client')
            intro = random.choice(convs['incipits']).format(mention)

        drink = random.choice(convs['drinkings']).format(found_drink.name)
        conclusion = random.choice(convs['conclusions'])

        log.info(f'sending message="{drink}" to mention={mention}')

        return intro + ' ' + drink + ' ' + conclusion, found_drink

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author == self.bot.user:
            return

        if not self._checkCall(message):
            return

        response, drink = self._serveDrinks(message)

        if response:
            await message.channel.send(response)

            if drink:
                await message.channel.send(file=drink.get_file())  # , embed=drink.get_embed())


def setup(bot):
    bot.add_cog(Barman(bot))
