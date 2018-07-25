import asyncio
import json
import os.path
import traceback

from StalkyDroid.webscraper import WebScraper
from contextlib import suppress

from datetime import datetime
from discord import Client, Message, Embed

envConfig = 'StalkyDroid/resources/environment.config'


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
            messages = await ws.scrape()

            # ...else lets explore the results
            for member, posts in messages.items():

                for post in posts:

                    embed = Embed(title=post['title'])
                    embed.add_field(name='Author', value=member, inline=False)

                    values = []
                    for field in post['body']:
                        type = field['type']
                        text = field['text']

                        if type == 'genmed':
                            values.append('**' + text + '**')
                        if type == 'quote':
                            values.append('_' + text + '_')
                        if type == 'postbody':
                            values.append(text.replace('"', "'"))

                    embed.add_field(name='Post', value="\n".join(values), inline=False)
                    embed.add_field(name='Link', value=post['url'], inline=False)

                    for f in embed.fields:
                        print(f)
                        # with open('test.txt', 'a') as x:
                        #     x.write(str(f))

                    print('------------------------')

                    for idx in self.getChannels():
                        try:
                            channel = self.client.get_channel(idx)
                            await self.client.send_message(channel, 'BIP!', embed=embed)
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
