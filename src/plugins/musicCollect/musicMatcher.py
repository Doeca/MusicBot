import re
import requests
import json
from . import util
from . import config
from typing import Union
from nonebot import on_regex
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, GroupMessageEvent

apiUrl = config.system.music_api


wyMatcher = on_regex('\[CQ:json.*?"appid":100495085',
                     priority=1, rule=util.group_checker)
qqMatcher = on_regex('\[CQ:json.*?"appid":100497308',
                     priority=1, rule=util.group_checker)


@qqMatcher.handle()
async def asyncfunc(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot, matcher: Matcher):
    matcher.stop_propagation()
    botid = await util.getID(bot)
    status = await util.isRunning(botid)
    if (status == False):
        await bot.send(e, "当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    msg = e.raw_message
    matchObj = re.search(r'"jumpUrl":"(.*?)"&#44;"p', msg, re.M | re.I)
    detailUrl = matchObj.group(1)
    detailUrl = util.unescape(detailUrl)
    resp = await util.httpGet(detailUrl)
    matchObj = re.search(r'"mid":"(.*?)"', resp.text, re.M | re.I)
    mid = matchObj.group(1)
    logger.debug(f"MID: {mid}")

    resp = await util.httpGet(f"{apiUrl}/qq/detail?id={mid}")
    if resp.status_code != 200:
        if (config.getVal(botid, 'debug') == 1):
            logger.debug(resp.text)
            await bot.send_private_msg(user_id=1124468334, message=f"点歌失败，相关日志：\n{resp.text}\nmid:{mid}\nraw msg:{msg}", auto_escape=True)
        await bot.send(e, "点歌失败，请稍后再试😢", at_sender=True, reply_message=True)
        return
    songInfo = resp.json()
    urls = [songInfo['playUrl'], songInfo['lrcUrl'], songInfo['cover']]

    await addToList(botid, e, bot, songInfo['name'], songInfo['author'], urls)


@wyMatcher.handle()
async def asyncfunc(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot, matcher: Matcher):
    matcher.stop_propagation()
    botid = await util.getID(bot)
    status = await util.isRunning(botid)
    if (status == False):
        await bot.send(e, "当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    msg = e.raw_message
    # print(msg)
    id = '0'
    try:
        matchObj = re.search(
            r'http:\/\/music\.163\.com\/song\/([0-9]{1,13})\?', msg, re.M | re.I)
        if (matchObj != None):
            id = matchObj.group(1)
        else:
            matchObj = re.search(
                r'\?id=([0-9]{1,13})', msg, re.M | re.I)
            id = matchObj.group(1)
    except:
        if (config.getVal(botid, 'debug') == 1):
            logger.debug(f"当前id:{id}")
            await bot.send_private_msg(user_id=1124468334, message=f"正则匹配失败，相关日志：\nraw msg:{msg}", auto_escape=True)
        await bot.send(e, "点歌失败，请稍后再试😢", at_sender=True, reply_message=True)
        return
    else:
        pass

    resp = await util.httpGet(f"{apiUrl}/wy/detail?id={id}")
    if resp.status_code != 200:
        if (config.getVal(botid, 'debug') == 1):
            logger.debug(resp.text)
            await bot.send_private_msg(user_id=1124468334, message=f"点歌失败，相关日志：\n{resp.text}\nid:{id}\nraw msg:{msg}", auto_escape=True)
        await bot.send(e, "点歌失败，请稍后再试😢", at_sender=True, reply_message=True)
        return
    songInfo = resp.json()
    urls = [songInfo['playUrl'], songInfo['lrcUrl'], songInfo['cover']]

    await addToList(botid, e, bot, songInfo['name'], songInfo['author'], urls)


async def addToList(botid, e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot, name: str, author: str, urls: list):
    # global orderList

    orderPeople = config.getVal(botid, 'orderPeople')
    orderList = config.getVal(botid, 'orderList')
    maxList = config.getVal(botid, 'maxList')
    maxPer = config.getVal(botid, "maxPer")
    if util.isBlack(botid, name):
        await bot.send(e, f"歌曲《{name}》在黑名单中，无法进行点歌🐵", at_sender=True, reply_message=True)
        return
    if ((0 if orderPeople.get(e.user_id) == None else orderPeople[e.user_id]) >= maxPer):
        await bot.send(e, f"每时段每人限点{maxPer}首，你无法继续点歌🫣", at_sender=True, reply_message=True)
        return
    if len(orderList) >= config.getVal(botid, 'maxList'):
        await bot.send(e, f"很抱歉，此时段点歌数量已达{maxList}首，无法继续点歌了💦",
                       at_sender=True, reply_message=True)
        return
    if name in util.getSongList(botid):
        await bot.send(e, f"很抱歉，《{name}》已经被别人点过了，换首别的歌吧😵",
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
    tempInfo['uin'] = e.user_id

    orderList.append(tempInfo)
    path = f"./store/{botid}/{config.getVal(botid,'fileLog')}"
    fp = open(path, "w")
    fp.write(json.dumps(orderList))
    fp.close()

    if (tempInfo['id'] >= config.getVal(botid, 'maxList')):
        for gid in config.getVal(botid, "groups"):
            await bot.set_group_card(group_id=gid, user_id=botid, card='点歌列表已满，努力播放中～')
    await bot.send(e, f"🥳点歌成功，点歌序号：{len(orderList)}/{maxList}", at_sender=True, reply_message=True)
