from bs4 import BeautifulSoup
import requests
import pandas as pd
import json
import os
import sys

# scape useful information from youtube videos
url = 'https://www.youtube.com/watch?v=BxV14h0kFs0' # user input for the link
source= requests.get(url)
soup=BeautifulSoup(source.text,'html.parser')
category = soup.find(itemprop='genre')['content']
link = soup.find('link')['href']
title = soup.find('title').text
tags = soup.find_all(property='og:video:tag')
tags = [item['content'] for item in tags]
description = soup.find(property='og:description')['content']
channel = soup.find('link',itemprop='name')['content']
isFamilyFriendly = soup.find(itemprop='isFamilyFriendly')['content']
uploadDate = soup.find(itemprop="uploadDate")['content']
views = soup.find(itemprop='interactionCount')['content']

#cant get likes or dislikes