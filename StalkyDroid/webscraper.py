import asyncio
import re

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
        self.waiting = 1  # todo: put something like 10 or 20  # seconds between searches

        with open(resourceDir + 'urls.config') as f:
            content = [line.split('=', 1) for line in f.readlines()]
            for tokens in content:
                self.config[tokens[0].strip()] = tokens[1].strip()

        with open(resourceDir + 'members.txt') as f:
            self.config['members'] = [line.strip() for line in f.readlines()]

    async def scrape(self):
        loop = asyncio.get_event_loop()

        messages = {}
        count = 0

        # for each member...
        for member in self.config['members']:
            if member.startswith('#'):
                continue

            print('Scraping ', member)

            messages[member] = []

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

                count += 1

                postdetail = postRow.find_all('span', {'class': 'postdetails'})[1]

                pdRxDate = re.findall('Posted: (.+)Post subject:.*', postdetail.text)
                pdRxTitle = re.findall('.*Post subject: (.+)', postdetail.text)

                pdDate = pdRxDate[0][0] if len(pdRxDate) > 0 else ''
                pdTitle = pdRxTitle[0][0] if len(pdRxTitle) > 0 else ''

                postbody = postRow.find_all(['span', 'td'], {'class': ['postbody', 'genmed', 'quote']})
                chunks = [
                    {
                        'type': x['class'][0],
                        'text': x.getText().rstrip()
                    }
                    for x in postbody
                    if x.getText().rstrip() != ''
                ]

                messages[member].append({
                    'id': postId,
                    'url': postUrl,
                    'date': pdDate.rstrip(),  # publication date
                    'title': pdTitle.rstrip(),  # topic title
                    'body': chunks,
                })

                await asyncio.sleep(self.waiting)

        print('total messages: ', count)

        return messages
