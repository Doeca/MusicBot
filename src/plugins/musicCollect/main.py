﻿import re
import urllib.parse
import requests
from .util import *
from typing import Union
from nonebot import on_command, on_fullmatch, on_regex
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, GroupMessageEvent, Event


# neteaseMatcher = on_regex("http(s|):\/\/music\.163\.com.*id=([0-9]*)",)

# @neteaseMatcher.handle()
# def func(foo = RegexGroup(),e : PrivateMessageEvent):
#     musicID = foo[1]

#     print(musicID)


"""
歌曲黑名单设计：
通过歌名进行拉黑，title是歌名 + 作者，但是feat版如何，判断关键词是否存在于之中？这样容易误判，就一个一个拉黑吧
"""


# @anyMatcher.handle()
# def func(e: Event):
#     print("Received: "+e.get_plaintext())
#     a = str(e.get_message())

#     # logger.add(e.get_plaintext(),level="INFO")
#     # print(e.get_message())

wyMatcher = on_regex('\[CQ:json.*?"appid":100495085')
qqMatcher = on_regex('\[CQ:json.*?"appid":100497308')
listMatcher = on_regex('^(歌曲列表|播放列表|待播清单)$')
playingMatcher = on_regex('正在播放|当前播放|放的是什么')
commandMatcher = on_command("orderStart", permission=SUPERUSER)

"""
点歌时间段，11点30分-12:30分，超时后将停止点歌
点歌时间段，17:30分-18:30分，超时后将停止点歌
"""


@listMatcher.handle()
async def retList(e: Event, bot: Bot):
    await bot.send(e, generateList(), at_sender=True, reply_message=True)


@playingMatcher.handle()
async def retList(e: Event, bot: Bot):
    await bot.send(e, generatePlay(), at_sender=True, reply_message=True)


@qqMatcher.handle()
async def asyncfunc(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot):
    if (orderStatus() == 0):
        await bot.send(e, "当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    msg = e.raw_message
    matchObj = re.search(r'"jumpUrl":"(.*?)"&#44;"p', msg, re.M | re.I)
    detailUrl = matchObj.group(1)
    detailUrl = unescape(detailUrl)
    resp = requests.get(detailUrl)
    matchObj = re.search(r'"mid":"(.*?)"', resp.text, re.M | re.I)
    mid = matchObj.group(1)
    logger.debug(f"MID: {mid}")

    resp = requests.get(f"https://musicapi.doeca.cc/qq/detail?id={mid}")
    if resp.status_code != 200:
        logger.debug(resp.text)
        await bot.send(e, "点歌失败，请稍后再试😢", at_sender=True, reply_message=True)
        return
    songInfo = resp.json()
    urls = [songInfo['playUrl'], songInfo['lrcUrl'], songInfo['cover']]

    await addToList(e, bot, songInfo['name'], songInfo['author'], urls)

    # 访问musicAPI，获取songURL等信息，若获取失败则提示点歌失败


@wyMatcher.handle()
async def asyncfunc(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot):
    if (orderStatus() == 0):
        await bot.send(e, "当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    msg = e.raw_message
    matchObj = re.search(r'id=([0-9]{1,12})"', msg, re.M | re.I)
    id = matchObj.group(1)
    logger.debug(f"ID: {id}")
    resp = requests.get(f"https://musicapi.doeca.cc/wy/detail?id={id}")
    if resp.status_code != 200:
        logger.debug(resp.text)
        await bot.send(e, "点歌失败，请稍后再试😢", at_sender=True, reply_message=True)
        return
    songInfo = resp.json()
    urls = [songInfo['playUrl'], songInfo['lrcUrl'], songInfo['cover']]

    await addToList(e, bot, songInfo['name'], songInfo['author'], urls)
    # 访问musicAPI，获取songURL等信息，若获取失败则提示点歌失败


@commandMatcher.handle()
async def startOrder():
    await run_start_order()
    await commandMatcher.send("已开启点歌")
