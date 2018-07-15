import random
import re

from JoeTheBarman.languages.it.drinks import initialDrinkList
from JoeTheBarman.languages.it.conversations import *


class Barman:
    def __init__(self, client):
        super().__init__()

        self.user = client.user
        self.channel = client.get_channel('467294663032963102')
        self.drinks = initialDrinkList

    def addDrink(self, drink):
        self.drinks[drink.lower()] = drink

    def greetings(self):
        return random.choice(greetings)

    def checkMessage(self, message):
        # must be in the bar
        if message.channel.id != self.channel.id:
            return False

        # must not anwer to itself
        if message.author == self.user:
            return False

        content = message.content.lower()

        # must contain 'joe' or 'barman'
        if any(x in content for x in names):
            return True

        return False

    def serveDrinks(self, message):
        mentions = message.mentions

        content = message.content
        clean = re.sub('[^A-Za-z0-9 ]+', '', content.lower())
        tokens = clean.split(' ')

        print(tokens)

        # search for any kind of drink
        foundDrinks = [d for d in self.drinks if d['key'] in clean]
        mention = message.author.mention
        title = random.choice(titles)

        if len(tokens) == 1 and len(foundDrinks) == 0:
            return random.choice(orders).format(message.author.mention), None

        if 'grazie' in tokens:
            # get a random thank string
            return random.choice(thanks).format(title), None

        if 'drinks' in tokens:
            # return the list of drinks
            return 'Abbiamo ' + ', '.join(self.drinks.values()), None

        if len(foundDrinks) < 1:
            # if we haven't found a valid drink
            return random.choice(notFound), None

        # we have found a drink!
        foundDrink = foundDrinks[0]

        if 'tutti' in tokens or message.mention_everyone:
            # if it is for @everyone or contains a special token
            return '@everyone il prossimo giro di {2} lo offre {1} {0}!'\
                .format(mention, title, foundDrink['name']), foundDrink['img']

        if len(mentions) > 0:
            # if we have mentions, notify to them
            intro = ', '.join([str(m.mention) for m in mentions]) \
                    + ' ' + str(mention) + ' vi offre'
        else:
            # just answer the client
            intro = random.choice(incipits).format(mention)

        drink = random.choice(drinkings).format(foundDrink['name'])
        conclusion = random.choice(conclusions)

        return intro + ' ' + drink + ' ' + conclusion, foundDrink['img']
