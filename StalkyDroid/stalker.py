import asyncio
import json
import os.path
import traceback
from pprint import pprint

from StalkyDroid.webscraper import WebScraper
from contextlib import suppress

from datetime import datetime
from discord import Client, Message, Embed

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


class Stalker(object):
    """
    Source for async task: https://stackoverflow.com/a/37514633/1419058
    """

    def __init__(self, client: Client):
        super().__init__()

        self.client = client
        self.user = client.user

        # async config
        # todo: this should be in config and changeable with commands
        self.time = 300  # seconds
        self.is_started = False
        self._task = None

        if os.path.isfile(envConfig):
            with open(envConfig, 'r') as f:
                self.config = json.load(f)
        else:
            self.config = {'channel_ids': []}

        with open(envChecked, 'r') as f:
            self.checked = json.load(f)

    def updateConfig(self, key: str, value):
        """
        Update generic configuration.
        :param key: key in the configuration
        :param value: new value
        """

        self.config[key] = value

        with open(envConfig, 'w') as f:
            json.dump(self.config, f)

    def getChannels(self):
        """
        :return: all the channels where this bot is anchored
        """
        return self.config['channel_ids']

    def addChannel(self, idx: str):
        """
        Add a channel id to the current channel list and update the configuration.
        :param idx: channel id
        """
        channels = self.getChannels()
        channels.append(idx)
        self.updateConfig('channel_ids', channels)

    def removeChannel(self, idx: str):
        """
        Remove a channel id from the current channel list and update the configuration.
        :param idx: id to remove
        """
        channels = self.getChannels()
        channels.remove(idx)
        self.updateConfig('channel_ids', channels)

    def checkMessage(self, message: Message):
        """
        Check if the message:
        - is not from itself,
        - it contains a mention to this bot,
        - or, it is from an anchored channel.

        :param message: input message
        :return: True if the message is for this bot, otherwise False
        """
        # avoid self messages
        if message.author == self.user:
            return False

        # it must contain a mention
        for mention in message.mentions:
            if mention.name == self.user.name:
                return True

        # if we have a channel
        channels = self.getChannels()
        if len(channels) > 0:
            # avoid messages from not registered channels
            if message.channel.id not in channels:
                return False

        return False

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

    def checkPost(self, topic, post):
        if topic['id'] not in self.checked:
            return False
        return post['id'] in self.checked[topic['id']]['list']

    def updateTopic(self, topic, pid):
        tid = topic['id']

        if tid not in self.checked:
            self.checked[tid] = {
                'posts': topic['posts'],
                'list': []
            }

        self.checked[tid]['list'].append(pid)

    def updateChecked(self):
        with open(envChecked, 'w+') as f:
            json.dump(f, self.checked)

    async def executeCommand(self, message: Message):
        """
        If the message contains a valid command, executes it.
        Current valid messages:
        - 'anchor' to register a channel
        - 'leave' to leave a registered channel

        :param message: the input message
        :return: an answer in bot-language :D
        """
        content = message.content
        channel = message.channel

        response = '_...bip bip bip..._'

        if 'anchor' in content:
            self.addChannel(channel.id)

            print('Anchored to ' + str(channel))
            response = '_Anchored to_ #' + channel.name

        if 'leave' in content:
            self.removeChannel(channel.id)

            print('Leaving ' + str(channel))
            response = '_Bye!_'

        if 'start' in content:
            await self.start()
            response = '_booting up sensors..._'

        if 'stop' in content:
            await self.stop()
            response = '_Sensors shutting down..._'

        await self.client.send_message(message.channel, response)

    async def webScraper(self):
        try:
            ws = WebScraper()
            topics = await ws.scrapeIndex()
            topics = sorted(topics, key=lambda x: -int(x['id']))

            for topic in topics:

                if self.checkTopic(topic):
                    # this topic has no news
                    continue

                print(topic)
                posts = await ws.scrapeTopic(topic)
                posts = sorted(posts, key=lambda x: -int(x['id']))

                for post in posts:
                    if self.checkPost(topic, post):
                        # already done
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
        Execute the current function.
        :return:
        """
        while True:
            print('exec...')
            # await self.bipTime()
            await self.webScraper()
            await asyncio.sleep(self.time)
