import asyncio
import re
import requests
from bs4 import BeautifulSoup
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
    return {
        'id': topic['href'].split('=')[1],
        'title': topic.getText(),
        'posts': int(topic.parent.parent.parent.find('span', {'class', 'postdetails'}).getText())
    }


def parsePost(block: BeautifulSoup):
    """
    Parse the input block and extract all the information regarding a post
    :param block: input code block
    :return: an dictionary representing a post
    """
    post = block.parent.parent
    postId = [a for a in post.findAll('a') if a.has_attr('name')][0]['name']

    postBody = post.find_all(['span', 'td'], {'class': ['postbody', 'genmed', 'quote']})
    postDetails = post.find_all('span', {'class': 'postdetails'})

    publicationDate = re.findall('Posted: (.+)Post subject:.*', postDetails[1].getText())[0]

    chunks = []

    for pb in postBody:
        text = pb.getText().strip()
        if text == '':
            continue

        chunk = {
            'type': pb.attrs['class'][0],
            'text': re.sub('\n+', '\n', text),
            'images': [],
            'links': []
        }

        for img in pb.findAll('img'):
            chunk['images'].append(img['src'])

        for a in pb.findAll('a', {'class': 'postlink'}):
            chunk['links'].append(a['href'])

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

        for start in range(page, 300, 15):
            content = await getRequest(
                self.config['URL_ROOT'] +
                self.config['URL_TOPIC'] +
                topic['id'] + "&start=" + str(start)
            )

            if 'General Error' in content.getText():
                break

            for block in content.findAll('span', {'class': 'name'}):
                name = block.getText().strip()
                if name in self.config['members']:
                    post = parsePost(block)

                    log.info('found post from {} {}'.format(name, post['id']))

                    post['author'] = name
                    post['link'] = (
                        self.config['URL_ROOT'] +
                        self.config['URL_POST'] +
                        post['id'] + "#" + post['id']
                    )

                    posts.append(post)

            asyncio.sleep(self.waiting)

        return posts
