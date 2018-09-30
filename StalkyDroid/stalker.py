import asyncio
import json
import re
from contextlib import suppress
from datetime import datetime

from discord import Client, Message, Embed

from BasicBot.basic import BasicBot, log
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

        log.debug(_type)
        log.debug(_text)

        if _type == 'quote':
            cs = _text.split(' wrote:')

            values.append('**{} wrote:**\n{}'.format(cs[0], cs[1]))

        if _type == 'text':
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
        self.lastUpdate = None

        self.addCommand(self.commandStart, True)
        self.addCommand(self.commandStop, True)
        self.addCommand(self.commandChangeFrequency, True)
        self.addCommand(self.commandOrder66, True)
        self.addCommand(self.commandLastUpdate, True)

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

        log.info('#{:8} +{:<4} {}'.format(topic['id'], (topic['posts'] - n), topic['title']))

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
        self.lastUpdate = datetime.now()
        log.info('update {}'.format(self.lastUpdate))

        with open(envChecked, 'w+') as f:
            json.dump(self.checked, f)

    async def commandStart(self, msg: Message):
        """
        Start the current registered routine if it is not already started.
        :param msg: must contain the 'start' keyword, and mention this bot
        :return: a startup message, or an empty string if the command is invalid
        """
        if self.containsMention(msg) and 'start' in msg.content:
            log.info('start!')
            await self.start()
            await self.send('_booting up sensors..._')
            return True

        return False

    async def commandStop(self, msg: Message):
        """
        Stop the current registered routine if it is running.
        :param msg: must contain the 'stop' keyword, and mention this bot
        :return: a shutdown message, or an empty string if the command is invalid
        """
        if self.containsMention(msg) and 'stop' in msg.content:
            log.info('stop!')
            await self.stop()
            await self.send('_Sensors shutting down..._')
            return True

        return False

    async def commandChangeFrequency(self, msg: Message):
        """
        Change the current update frequency. The input value is in seconds and has 900s (15min) as lower bound.
        No upper bound is defined. Default value is 3600.
        The previous interval must expire before the new one will be used.
        :param msg: must contain the 'frequency' keyword, mention this bot, and have a valid number
        :return: a message, or an empty string if the command is invalid
        """
        if self.containsMention(msg) and 'frequency' in msg.content:
            try:
                tokens = msg.content.split(' ')
                time = int(tokens[len(tokens) - 1])
                self.time = max(time, 900)
                response = '_New frequency {}_'.format(str(self.time))
                log.info('new frequency: {}'.format(self.time))
            except ValueError:
                response = '_Kzzzzzt! Invalid..._'
                log.info('cannot parse number: {}'.format(msg.content))

            await self.send(response)
            return True

        return False

    async def commandOrder66(self, msg: Message):
        """
        Start the kill-all-jedi routine. Long live the Emperor!
        :param msg: must contain the keyword '66', and mention this bot.
        :return an easter egg message :)
        """
        if self.containsMention(msg) and '66' in msg.content:
            log.info("killing jedi...")
            await self.send('_ :skull: KILL ALL THE JEDI! :skull: _')
            return True

        return False

    async def commandLastUpdate(self, msg: Message):
        """
        Return the last time the bot checked the forum for news.
        :param msg: must contain the keyword 'info', and mention this bot.
        """
        if self.containsMention(msg) and 'info':
            log.info('last update done: {}'.format(self.lastUpdate))
            await self.send('_Last update: {}_'.format(self.lastUpdate))
            return True

        return False

    async def webScraper(self):
        """
        Routine to perform the web scraping of the forum.
        """
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
                        log.info('post from {} #{} already done'.format(post['author'], post['id']))
                        continue

                    # send all the messages!
                    embed = buildEmbed(topic, post)

                    try:
                        await self.send('BIP!', embed=embed)

                        # register the posts
                        self.updateTopic(topic, post['id'])
                    except Exception as e:
                        log.error(e)
                        # traceback.print_exc()

        except Exception as e:
            # if we have any kind of error with the remote site, call for help!
            log.error(e)
            # traceback.print_exc()
            await self.send('@everyone _O-oh..._')
            await self.stop()
            return

        self.updateChecked()

    async def bipTime(self):
        """
        Just a debug function that print the current date and time
        """
        now = datetime.now()
        msg = '...check: {}...'.format(now)
        log.info('sending: {}'.format(msg))
        await self.send(msg)

    async def start(self):
        """
        Start or restart the execution.
        """
        if not self.is_started:
            self.is_started = True
            log.info('starting...')
            # start task to call function periodically
            self._task = asyncio.ensure_future(self._run())

    async def stop(self):
        """
        Stop the execution, if it is running.
        """
        if self.is_started:
            log.info('stopping...')
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

    async def login(self):
        await super().login()
        await self.start()
