import time
import random
import requests
import asyncio
import aiohttp
from typing import Union
from nonebot.utils import run_sync
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Event

schoolInfo = dict()


async def httpGet(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return resp


async def get_realurl(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=False) as resp:
            return resp.headers.get('Location', '')

# 做测试

schoolInfo['testid'] = {"a": "1"}


def testprint():
    print(schoolInfo['testid'])
