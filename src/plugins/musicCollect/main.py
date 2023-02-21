import re
import urllib.parse
import requests
from .util import *
from typing import Union
from nonebot import on_command, on_fullmatch, on_regex
from nonebot.log import logger
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, ArgPlainText, ArgStr
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, GroupMessageEvent, Event
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER


wyMatcher = on_regex('\[CQ:json.*?"appid":100495085')
qqMatcher = on_regex('\[CQ:json.*?"appid":100497308')

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



@wyMatcher.handle()
async def asyncfunc(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot):
    if (orderStatus() == 0):
        await bot.send(e, "当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    msg = e.raw_message
    matchObj = re.search(r'id=([0-9]{1,13}).*', msg, re.M | re.I)
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


