import asyncio
import re

import requests
from bs4 import BeautifulSoup

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
        'title': topic.getText()
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
            'type': pb.attrs['class'],
            'text': text,
            'images': [],
            'links': []
        }

        for img in pb.findAll('img'):
            chunk['images'].append(img['src'])

        for a in pb.findAll('a', {'class': 'postlink'}):
            chunk['links'].append(a['src'])

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
        self.waiting = 2  # todo: put something like 10 or 20  # seconds between searches

        with open(resourceDir + 'urls.config') as f:
            content = [line.split('=', 1) for line in f.readlines()]
            for tokens in content:
                self.config[tokens[0].strip()] = tokens[1].strip()

        with open(resourceDir + 'members.txt') as f:
            self.config['members'] = [line.strip() for line in f.readlines()]

    async def scrapeIndex(self):
        content = await getRequest(
            self.config['URL_ROOT'] +
            self.config['URL_FORUM'] +
            self.config['FORUM_X4']
        )

        topicsList = content.findAll('a', {'class': 'topictitle'})
        topics = [topicInfo(t) for t in topicsList]

        return topics

    async def scrapeTopic(self, topicId):

        posts = []

        for start in range(0, 300, 15):
            content = await getRequest(
                self.config['URL_ROOT'] +
                self.config['URL_TOPIC'] +
                topicId + "&start=" + start
            )

            if 'General Error' in content.getText():
                break

            for block in content.findAll('span', {'class': 'name'}):
                name = block.getText().strip()
                if name in self.config['members']:
                    print('found post from ', name)

                    post = parsePost(block)
                    post['author'] = name

                    posts.append(post)

            asyncio.sleep(self.waiting)

        return posts
