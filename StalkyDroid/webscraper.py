import asyncio
import re
import requests
from bs4 import BeautifulSoup, NavigableString
from random import randint

from BasicBot.basic import log

resourceDir = 'StalkyDroid/resources/'


def getLoop():
    """
    :return: the current asyncio loop
    """
    return asyncio.get_event_loop()


async def getRequest(url: str):
    """
    :param url: destination url
    :return: the content of the request
    """
    future = getLoop().run_in_executor(None, requests.get, url)
    results = await future
    content = BeautifulSoup(results.content, 'html5lib')
    return content


def topicInfo(topic: BeautifulSoup):
    """
    Parse a topic block and extract its id and title.
    :param topic: input code block
    :return: a dictionary composed by id and title of the topic
    """
    m = re.search('.*t=(\d*).*', topic['href'])
    return {
        'id': m.group(1),
        'title': topic.getText(),
        'posts': int(topic.parent.parent.parent.find('dd', {'class', 'posts'}).getText().split(' ', 1)[0])
    }


def parsePost(block: BeautifulSoup):
    """
    Parse the input block and extract all the information regarding a post
    :param block: input code block
    :return: an dictionary representing a post
    """
    post = block.parent
    postId = post['id'][12:]

    postBody = post.find('div', {'class': 'content'})
    publicationDate = re.findall('» (.*)', post.find('p', {'class': 'author'}).getText().strip())[0]

    chunks = []
    last = None

    for pb in postBody.children:
        if str(pb).strip() in ['', '<br/>']:
            continue

        add = True

        isQuote = None
        try:
            isQuote = pb.findAll('cite')
        except AttributeError:
            pass

        if isinstance(pb, NavigableString):
            _text = str(pb)
        else:
            _text = pb.getText()

        if isQuote and len(isQuote) > 0:
            chunk = {
                'type': 'quote',
                'text': re.sub('\n+', '\n', _text),
            }

        elif last and last['type'] == 'text':
            chunk = last
            chunk['text'] += ' ' + re.sub('\n+', '\n', _text)
            add = False

        else:
            chunk = {
                'type': 'text',
                'text': re.sub('\n+', '\n', _text),
            }

        last = chunk
        if add:
            chunks.append(chunk)

    return {
        'id': postId,
        'date': publicationDate,
        'chunks': chunks
    }


class WebScraper(object):

    def __init__(self) -> None:
        super().__init__()

        self.config = {}
        self.waiting = randint(10, 30)

        log.info('current waiting: {}'.format(self.waiting))

        with open(resourceDir + 'urls.config') as f:
            content = [line.split('=', 1) for line in f.readlines()]
            for tokens in content:
                self.config[tokens[0].strip()] = tokens[1].strip()

        with open(resourceDir + 'members.txt') as f:
            self.config['members'] = [line.strip() for line in f.readlines()]

    async def scrapeIndex(self):
        log.info(self.config)
        content = await getRequest(
            self.config['URL_ROOT'] +
            self.config['URL_FORUM'] +
            self.config['FORUM_X4']
        )

        topicsList = content.findAll('a', {'class': 'topictitle'})
        topics = [topicInfo(t) for t in topicsList]

        return topics

    async def scrapeTopic(self, topic, page=0):

        posts = []

        for start in range(page, topic['posts'] + 1, 15):
            content = await getRequest(
                self.config['URL_ROOT'] +
                self.config['URL_TOPIC'] +
                topic['id'] + "&start=" + str(start)
            )

            for block in content.findAll('p', {'class': 'author'}):
                x = block.find('strong')

                if x is None:
                    continue

                name = x.getText().strip()
                if name in self.config['members']:
                    post = parsePost(block)

                    log.info('found post from {} {}'.format(name, post['id']))

                    post['author'] = name
                    post['link'] = (
                        self.config['URL_ROOT'] +
                        self.config['URL_POST'] +
                        post['id'] + "#p" + post['id']
                    )

                    posts.append(post)

            asyncio.sleep(self.waiting)

        return posts
