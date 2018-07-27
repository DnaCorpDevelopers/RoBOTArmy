import asyncio
import json
import traceback
from contextlib import suppress
from datetime import datetime
from pprint import pprint

from discord import Client, Message, Embed

from BasicBot.basic import BasicBot
from StalkyDroid.webscraper import WebScraper

envConfig = 'StalkyDroid/resources/environment.config'
envChecked = 'StalkyDroid/resources/checked.json'


def buildEmbed(topic, post):
    embed = Embed(title=topic['title'])
    embed.add_field(name='Author', value=post['author'], inline=False)
    embed.add_field(name='Date', value=post['date'], inline=False)
    embed.add_field(name='Link', value=post['link'], inline=False)

    values = []

    chunks = post['chunks']
    for i in range(min(20, len(chunks))):
        _field = chunks[i]

        _type = _field['type']
        _text = _field['text']

        pprint(_type)
        pprint(_text)

        if _type == 'genmed':
            values.append('**' + _text + '**')
        if _type == 'quote':
            values.append('_' + _text + '_')
        if _type == 'postbody':
            if '_________________' not in _text:
                values.append(_text.replace('"', "'"))

    fullText = "\n".join(values)

    truncated = False

    if len(fullText) > 1024:
        fullText = fullText[:1020] + '...'
        truncated = True

    if len(chunks) > 20:
        truncated = True

    embed.add_field(name='Post', value=fullText, inline=False)
    if truncated:
        embed.add_field(name='_Truncated message_',
                        value='_Check the link for the whole message_',
                        inline=False)

    print('fields: ', len(embed.fields))

    for field in embed.fields:
        print(field.name, len(field.value))

    return embed


class Stalker(BasicBot):
    """
    Source for async task: https://stackoverflow.com/a/37514633/1419058
    """

    def __init__(self, client: Client):
        super().__init__(client, envConfig)

        # async config
        self.time = 3600  # seconds, hardcoded min is 15
        self.is_started = False
        self._task = None

        self.addCommand(self.commandStart, True)
        self.addCommand(self.commandStop, True)
        self.addCommand(self.commandChangeFrequency)
        self.addCommand(self.commandOrder66)

        with open(envChecked, 'r') as f:
            self.checked = json.load(f)

    def checkTopic(self, topic):
        """
        Check if in the given topic there are new posts.
        :param topic: topic to check
        :return: True if the topic is checked, otherwise False
        """
        if topic['id'] in self.checked:
            if topic['posts'] <= self.checked[topic['id']]['posts']:
                # topic already checked in toto
                return True

        return False

    def topicStartReadFrom(self, topic):
        """
        Compute the page index to start read from (because the old message are already parsed).
        :param topic: input topic
        :return: the page index to start from
        """
        if topic['id'] not in self.checked:
            return 0

        n = self.checked[topic['id']]['posts']

        print('#{:8} +{:<4} {}'.format(topic['id'], (topic['posts'] - n), topic['title']))

        return n - (n % 15)

    def checkPost(self, topic, post):
        """
        Check if a post is already done or not.
        :param topic: topic reference
        :param post: post to check
        :return: True if the post is already done, otherwise False
        """
        if topic['id'] not in self.checked:
            return False
        return post['id'] in self.checked[topic['id']]['list']

    def updateTopic(self, topic, pid):
        """
        Update the internal topic list with the new parsed post id.
        :param topic: topic reference
        :param pid: id of a post
        """
        tid = topic['id']

        if tid not in self.checked:
            self.checked[tid] = {
                'posts': topic['posts'],
                'list': []
            }

        self.checked[tid]['list'].append(pid)

    def updateChecked(self):
        """
        Update the disk file with all the configuration data for the checked list.
        """
        print('update', str(datetime.now()))

        with open(envChecked, 'w+') as f:
            json.dump(self.checked, f)

    async def commandStart(self, msg: Message):
        if self.containsMention(msg) and 'start' in msg.content:
            print('start!')
            await self.start()
            return '_booting up sensors..._'

        return ''

    async def commandStop(self, msg: Message):
        if self.containsMention(msg) and 'stop' in msg.content:
            print('stop!')
            await self.stop()
            return '_Sensors shutting down..._'

        return ''

    def commandChangeFrequency(self, msg: Message):
        if self.containsMention(msg) and 'frequency' in msg.content:
            try:
                tokens = msg.content.split(' ')
                time = int(tokens[len(tokens) - 1])
                self.time = max(time, 900)
                response = '_New frequency: ' + str(self.time) + '_'
            except ValueError:
                response = '_Kzzzzzt! Invalid..._'

            return response

        return ''

    def commandOrder66(self, msg: Message):
        if self.containsMention(msg) and '66' in msg.content:
            return '_ :skull: KILL ALL THE JEDI! :skull: _'

        return ''

    async def webScraper(self):
        try:
            ws = WebScraper()
            topics = await ws.scrapeIndex()
            topics = sorted(topics, key=lambda x: -int(x['id']))

            for topic in topics:

                if self.checkTopic(topic):
                    # this topic has no news
                    continue

                page = self.topicStartReadFrom(topic)

                posts = await ws.scrapeTopic(topic, page)
                posts = sorted(posts, key=lambda x: -int(x['id']))

                for post in posts:
                    if self.checkPost(topic, post):
                        # already done
                        print('post from {} #{} already done'.format(post['author'], post['id']))
                        continue

                    # send all the messages!
                    embed = buildEmbed(topic, post)

                    for idx in self.getChannels():
                        try:
                            channel = self.client.get_channel(idx)
                            await self.client.send_message(channel, 'BIP!', embed=embed)

                            # register the posts
                            self.updateTopic(topic, post['id'])
                        except Exception as e:
                            print(e)
                            traceback.print_exc()

        except Exception as e:
            # if we have any kind of error with the remote site, call for help!
            print(e)
            traceback.print_exc()
            await self.client.send_message('@everyone _O-oh..._')
            await self.stop()
            return

        self.updateChecked()

    async def bipTime(self):
        """
        Just a debug function that print the current date and time
        """
        now = datetime.now()
        for idx in self.getChannels():
            channel = self.client.get_channel(idx)
            msg = '...check: ' + str(now) + '...'
            print('sending: ', msg)
            await self.client.send_message(channel, msg)

    async def start(self):
        """
        Start or restart the execution.
        """
        if not self.is_started:
            self.is_started = True
            print('starting...')
            # start task to call function periodically
            self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        """
        Stop the execution, if it is running.
        """
        if self.is_started:
            print('stopping...')
            self.is_started = False
            # stop task and await
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

    async def _run(self):
        """
        Execute the web scraping
        :return:
        """
        while True:
            await self.webScraper()
            # await self.bipTime()
            await asyncio.sleep(self.time)
