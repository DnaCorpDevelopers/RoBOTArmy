import json
import os

from discord import Client, Message


class BasicBot(object):

    def __init__(self, client: Client, env) -> None:
        super().__init__()

        self.client = client
        self.user = client.user
        self.env = env

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

            print('Anchored to ' + str(channel))
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

            print('Leaving ' + str(channel))
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
        # avoid self messages
        if message.author == self.user:
            return False

        # if we have a channel
        channels = self.getChannels()
        if len(channels) > 0:
            # avoid messages from not registered channels
            if message.channel.id not in channels:
                return False

        return True

    async def executeCommand(self, message: Message):
        """
        If the message contains a valid command, executes it.
        Current valid messages:
        - 'anchor' to register a channel
        - 'leave' to leave a registered channel

        :param message: the input message
        :return: an answer in bot-language :D
        """

        if not self.checkMessage(message):
            return

        for command in self.commandsSync:
            response = command(message)
            if response is not '':
                await self.client.send_message(message.channel, response)
                return

        for command in self.commandsAsync:
            response = await command(message)
            if response is not '':
                await self.client.send_message(message.channel, response)
                return

        if self.containsMention(message):
            await self.client.send_message(message.channel, '_...bip bip bip..._')
