import re
import requests
import json
from . import util
from . import config
from typing import Union
from nonebot import on_regex
from nonebot.log import logger
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, GroupMessageEvent

apiUrl = "https://musicback.doeca.cc:20050"

wyMatcher = on_regex('\[CQ:json.*?"appid":100495085')
qqMatcher = on_regex('\[CQ:json.*?"appid":100497308')


@qqMatcher.handle()
async def asyncfunc(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot):
    if (config.getValue('orderSwitch') == 0):
        await bot.send(e, "当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    msg = e.raw_message
    matchObj = re.search(r'"jumpUrl":"(.*?)"&#44;"p', msg, re.M | re.I)
    detailUrl = matchObj.group(1)
    detailUrl = util.unescape(detailUrl)
    resp = requests.get(detailUrl)
    matchObj = re.search(r'"mid":"(.*?)"', resp.text, re.M | re.I)
    mid = matchObj.group(1)
    logger.debug(f"MID: {mid}")

    resp = requests.get(f"{apiUrl}/qq/detail?id={mid}")
    if resp.status_code != 200:
        logger.debug(resp.text)
        await bot.send(e, "点歌失败，请稍后再试😢", at_sender=True, reply_message=True)
        return
    songInfo = resp.json()
    urls = [songInfo['playUrl'], songInfo['lrcUrl'], songInfo['cover']]

    await addToList(e, bot, songInfo['name'], songInfo['author'], urls)


@wyMatcher.handle()
async def asyncfunc(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot):
    if (config.getValue('orderSwitch') == 0):
        await bot.send(e, "当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    msg = e.raw_message
    matchObj = re.search(r'id=([0-9]{1,13}).*', msg, re.M | re.I)
    id = matchObj.group(1)
    logger.debug(f"ID: {id}")
    resp = requests.get(f"{apiUrl}/wy/detail?id={id}")
    if resp.status_code != 200:
        logger.debug(resp.text)
        await bot.send(e, "点歌失败，请稍后再试😢", at_sender=True, reply_message=True)
        return
    songInfo = resp.json()
    urls = [songInfo['playUrl'], songInfo['lrcUrl'], songInfo['cover']]

    await addToList(e, bot, songInfo['name'], songInfo['author'], urls)
    # 访问musicAPI，获取songURL等信息，若获取失败则提示点歌失败


async def addToList(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot, name: str, author: str, urls: list):
    # global orderList
    blackList = config.getValue('blackList')
    orderPeople = config.getValue('orderPeople')
    orderList = config.getValue('orderList')
    maxList = config.getValue('maxList')
    if name in blackList:
        await bot.send(e, f"歌曲《{name}》在黑名单中，无法进行点歌🐵", at_sender=True, reply_message=True)
        return
    if ((0 if orderPeople.get(e.user_id) == None else orderPeople[e.user_id]) >= 2):
        await bot.send(e, f"每时段每人限点2首，你无法继续点歌🫣", at_sender=True, reply_message=True)
        return
    if len(orderList) >= config.getValue('maxList'):
        await bot.send(e, f"很抱歉，此时段点歌数量已达{maxList}首，无法继续点歌了💦",
                       at_sender=True, reply_message=True)
        return
    orderPeople[e.user_id] = (0 if orderPeople.get(
        e.user_id) == None else orderPeople[e.user_id])
    orderPeople[e.user_id] = orderPeople[e.user_id] + 1

    tempInfo = dict()
    tempInfo['name'] = name
    tempInfo['author'] = author
    tempInfo['playUrl'] = urls[0]
    tempInfo['lrcUrl'] = urls[1]
    tempInfo['cover'] = urls[2]
    tempInfo['played'] = 0
    tempInfo['id'] = len(orderList) + 1

    orderList.append(tempInfo)
    path = f"./store/{config.getValue('fileLog')}"
    fp = open(path, "w")
    fp.write(json.dumps(orderList))
    fp.close()

    if(tempInfo['id'] >= config.getValue('maxList')):
        await bot.set_group_card(config.bot.notice_id,config.bot.bot_id,'点歌列表已满，努力播放中～')
    await bot.send(e, f"🥳点歌成功，点歌序号：{len(orderList)}/{maxList}", at_sender=True, reply_message=True)
