from discord import Client, Message
import os.path
import json

envConfig = 'StalkyDroid/resources/environment.config'


class Stalker(object):

    def __init__(self, client: Client):
        super().__init__()

        self.client = client
        self.user = client.user

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

    def executeCommand(self, message: Message):
        """
        If the message contains a valid command, executes it.
        Current valid messages:
        - 'anchor' to register a channel
        - 'leave' to leave a registered channel

        :param message: the input message
        :return: an answer in bot-language :D
        """
        content = message.content

        if 'anchor' in content:
            channel = message.channel
            self.addChannel(channel.id)

            print('Anchored to ' + str(channel))
            return '_Anchored to_ #' + channel.name

        if 'leave' in content:
            channel = message.channel
            self.removeChannel(channel.id)

            print('Leaving ' + str(channel))
            return '_Bye!_'

        return "_...bip bip bip..._"
