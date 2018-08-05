import random
import re

from discord import Message, Client, User

from BasicBot.basic import BasicBot, log
from JoeTheBarman.languages.it.conversations import *
from JoeTheBarman.languages.it.drinks import initialDrinkList

ENV_CONFIG = 'JoeTheBarman/resources/environment.config'
IMAGES = 'JoeTheBarman/images/'


class Barman(BasicBot):
    def __init__(self, client: Client):
        super().__init__(client, ENV_CONFIG)

        self.user = client.user
        self.drinks = initialDrinkList

        self.orders = {}

        self.customers = set()

        self.addCommand(self.commandServeDrinks, True)

    def addDrink(self, drink):
        self.drinks[drink.lower()] = drink

    def register(self, user: User):
        self.customers.add(user)
        return random.choice(greetings)

    def checkCall(self, message: Message):
        content = message.content.lower()

        # must contain 'joe' or 'barman' or be in the watching list
        return any(x in content for x in names) or message.author in self.customers

    async def commandServeDrinks(self, message: Message):
        response, img = self.serveDrinks(message)

        if response is not None:
            await self.send(response, message.channel)
            if img is not None:
                await self.client.send_file(message.channel, img)
            return True

        return False

    def serveDrinks(self, message: Message):
        if not self.checkCall(message):
            return None, None

        mentions = message.mentions

        content = message.content
        clean = re.sub('[^A-Za-z0-9 ]+', '', content.lower())
        tokens = clean.split(' ')

        log.debug('tokens: ' + str(tokens))

        # search for any kind of drink
        foundDrinks = [d for d in self.drinks if d['key'] in tokens]
        mention = message.author.mention
        title = random.choice(titles)

        if len(tokens) == 1 and len(foundDrinks) == 0:
            log.info('send generic order request')
            return random.choice(orders).format(message.author.mention), None

        if len([a for a in thankAnswer if a in tokens]) > 0:
            # get a random thank string
            log.info('send thanks')
            return random.choice(thanks).format(title), None

        if len([d for d in drinkList if d in tokens]) > 0:
            # return the list of drinks
            log.info('send drink list')
            return random.choice(drinkListIncipit) + '\n - '.join([d['name'] for d in self.drinks]), None

        if len(foundDrinks) < 1:
            # if we haven't found a valid drink
            log.info('send not found ' + str(tokens))
            return random.choice(notFound), None

        # we have found a drink!
        foundDrink = foundDrinks[0]

        if everybodyRequest in tokens or message.mention_everyone:
            # if it is for @everyone or contains a special token
            log.info('send offer to everyone')
            return random.choice(sendToEveryone).format(
                mention, title, foundDrink['name']
            ), foundDrink['img']

        if len(mentions) > 0:
            # if we have mentions, notify to them
            log.info('offer to user')
            intro = ', '.join([str(m.mention) for m in mentions]) \
                    + ' ' + str(mention) + ' vi offre'
        else:
            # just answer the client
            log.info('answer the client')
            intro = random.choice(incipits).format(mention)

        drink = random.choice(drinkings).format(foundDrink['name'])
        conclusion = random.choice(conclusions)

        log.info('sending drink')
        log.info('drink: ' + drink)
        log.info('to: ' + mention)
        return intro + ' ' + drink + ' ' + conclusion, IMAGES + foundDrink['img']

    async def login(self):
        await super().login()
        await self.send(random.choice(greetings))
