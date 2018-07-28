import json
import os
import logging

from discord import Client, Message

logging.basicConfig(level=logging.INFO, format='%(asctime)s : %(levelname)s : %(message)s')
log = logging.getLogger('BasicBot')


class Content(object):

    def __init__(self, message=None, channel=None, embed=None) -> None:
        super().__init__()
        self.message = message
        self.channel = channel
        self.embed = embed


class BasicBot(object):

    def __init__(self, client: Client, env) -> None:
        super().__init__()

        self.client = client
        self.env = env
        self.user = None

        self.commandsSync = [self.anchorToChannel, self.leaveChannel]
        self.commandsAsync = []

        if os.path.isfile(self.env):
            with open(self.env, 'r') as f:
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

        with open(self.env, 'w') as f:
            json.dump(self.config, f)
            log.info('Config updated, file written to ' + self.env)

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

    def addCommand(self, command, async=False):
        """
        Register a new command in this bot.
        :param command: the function to execute the command
        :param async: if True the command will be execute as an async function, otherwise as synchronized.
        """
        if async:
            self.commandsAsync.append(command)
        else:
            self.commandsSync.append(command)

    def containsMention(self, message: Message):
        """
        :param message: input message
        :return: True if it contains a mention to this bot, otherwise False.
        """
        for mention in message.mentions:
            if mention.name == self.user.name:
                return True

        return False

    def anchorToChannel(self, message: Message):
        """
        Add a channel to listen from.
        :param message: input message
        :return: a confirmation message if successful, otherwise None
        """
        content = message.content
        channel = message.channel

        if self.containsMention(message) and 'anchor' in content:
            self.addChannel(channel.id)

            log.info('Anchored to ' + str(channel))
            return '_Anchored to_ #' + channel.name

        return ''

    def leaveChannel(self, message: Message):
        """
        Removes a previously registered channel.
        :param message: input message
        :return: a confirmation message if successful, otherwise None
        """
        content = message.content
        channel = message.channel

        if self.containsMention(message) and 'leave' in content:
            self.removeChannel(channel.id)

            log.info('Leaving ' + str(channel))
            return '_Bye!_'

        return ''

    def checkMessage(self, message: Message):
        """
        Check if the message:
        - is not from itself,
        - and it is from an anchored channel.

        :param message: input message
        :return: True if the message is for this bot, otherwise False
        """
        log.debug('checking message ' + str(message))

        # avoid self messages
        if message.author == self.user:
            log.debug('avoid answer message from self')
            return False

        # if we have a channel
        channels = self.getChannels()
        if len(channels) > 0:
            # avoid messages from not registered channels
            if message.channel.id not in channels:
                log.debug('message is not from anchored channel')
                return False

        log.debug('message is valid')

        return True

    def getChannelList(self, channel=None):
        """
        Resovle a list of all channels to Channel objects, or the given channel in list format.
        :param channel: destination channel
        :return: a list of Channle objects
        """
        if channel is None:
            channels = [self.client.get_channel(chid) for chid in self.getChannels()]
        else:
            channels = [channel]
        return channels

    async def send(self, message: str, channel=None, embed=None):
        """
        Send a message through the client to all connected channels.
        :param channel: specify the destination channel. If None, it will be sent to all anchored channels
        :param embed: set the embed to use
        :param message: the message to send
        """
        log.debug('send message: ' + str(message))
        log.debug('to channel:   ' + str(channel))
        log.debug('with embed:   ' + str(embed))

        channels = self.getChannelList(channel)

        for ch in channels:
            log.debug('sending message to ' + str(ch))
            await self.client.send_message(ch, message, embed=embed)

    async def login(self):
        """
        Perform basic login stuff.
        """
        log.info('Logged in as')
        log.info(self.client.user.name)
        log.info(self.client.user.id)

        self.user = self.client.user

        log.info('Anchored channels:')
        for _id in self.getChannels():
            channel = self.client.get_channel(_id)
            log.info('+ {} {}'.format(channel.name, channel.id))

    async def executeCommand(self, message: Message):
        """
        If the message contains a valid command, executes it.
        Current valid messages:
        - 'anchor' to register a channel
        - 'leave' to leave a registered channel

        :param message: the input message
        :return: an answer in bot-language :D
        """

        log.debug('received message ' + str(message))

        if not self.checkMessage(message):
            log.debug('message check FAILED')
            return

        log.debug('check async commands')
        for command in self.commandsSync:
            log.debug('check command ' + str(command))
            response = command(message)
            if response:
                log.info('command executed')
                return

        log.debug('check sync commands')
        for command in self.commandsAsync:
            log.debug('check command ' + str(command))
            response = await command(message)
            if response:
                log.info('command executed')
                return

        if self.containsMention(message):
            log.debug('no command executed')
            await self.send('_...bip bip bip..._', message.channel)
