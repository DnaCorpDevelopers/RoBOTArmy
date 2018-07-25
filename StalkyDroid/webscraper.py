import asyncio

import requests
from bs4 import BeautifulSoup

resourceDir = 'StalkyDroid/resources/'


async def getRequest(loop, search):
    searchFut = loop.run_in_executor(None, requests.get, search)
    searchRes = await searchFut
    searchContent = BeautifulSoup(searchRes.content, 'html5lib')
    return searchContent


class WebScraper(object):

    def __init__(self) -> None:
        super().__init__()

        self.config = {}
        self.limit = 5  # todo: increase
        self.waiting = 10  # seconds between searches

        with open(resourceDir + 'urls.config') as f:
            content = [line.split('=', 1) for line in f.readlines()]
            for tokens in content:
                self.config[tokens[0].strip()] = tokens[1].strip()

        with open(resourceDir + 'members.txt') as f:
            self.config['members'] = [line.strip() for line in f.readlines()]

    async def scrape(self):
        loop = asyncio.get_event_loop()

        messages = {}

        # for each member...
        for member in self.config['members']:
            print('Scraping ', member)

            messages[member] = {'posts': []}

            search = self.config['SEARCH'] + member
            site = self.config['ROOT']

            print(search)

            searchContent = await getRequest(loop, search)

            posts = []
            searchPages = []

            # ...run a search...
            for a in searchContent.find_all('a'):
                if a.has_attr('href'):
                    href = a['href']
                    if 'p=' in href:
                        posts.append(href)
                    if 'search_id=' in href:
                        searchPages.append(href)

            print('found ', len(posts), ' posts')
            print('found ', len(searchPages), ' search pages')

            # ... and extract all the posts...
            for i in range(min(self.limit, len(posts))):
                # todo: add a check from the last posts ids

                post = posts[i]
                postUrl = site + post

                postContent = await getRequest(loop, postUrl)
                postId = post.split('#')[1]

                print('get post #', postId)

                anchorPost = postContent.find('a', {'name': postId})
                postRow = anchorPost.parent.parent.parent

                messages[member]['posts'].append({
                    'postId': postId,
                    'postUrl': postUrl,
                    'postbody': postRow.find_all('span', {'class': 'postbody'}),
                    'postdetails': postRow.find_all('span', {'class': 'postdetails'})
                })

            await asyncio.sleep(self.waiting)

        return messages
