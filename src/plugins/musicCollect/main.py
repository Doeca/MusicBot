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
listMatcher = on_regex('^(歌曲列表|播放列表|待播清单)$')
playingMatcher = on_regex('正在播放|当前播放|放的是什么')
commandMatcher = on_command("orderStart", permission=SUPERUSER)
banMatcher = on_command("ban", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER))

@listMatcher.handle()
async def retList(e: Event, bot: Bot):
    await bot.send(e, generateList(), at_sender=True, reply_message=True)


@playingMatcher.handle()
async def retList(e: Event, bot: Bot):
    await bot.send(e, generatePlay(), at_sender=True, reply_message=True)


@banMatcher.handle()
async def banHandle(matcher: Matcher, args: Message = CommandArg()):
    id = args.extract_plain_text().strip()
    logger.debug(f"ID : {id}")
    if id == '':
        id = currentPlay()
    elif id.isdigit():
        id = int(id)
    else:
        matcher.set_arg("arg", id.strip())
        return
    if id == 0:
        return
    if id <= len(orderList):
        matcher.set_arg("arg", str(id))


@banMatcher.got("arg",prompt="请输入歌曲列表中的序号 or 直接输入歌曲名")
async def banID(arg: str = ArgStr('arg')):
    line = arg.strip()
    name = ''
    if line == '':
        await banMatcher.finish(f"操作已取消")
    elif line.isdigit():
        id = int(line)
        if id == 0 or id > len(orderList):
            await banMatcher.reject(f"歌曲序号：{id}不存在，请重新输入")
        name = orderList[id-1]['name']
        if id == currentPlay():
            addOperation('next')
    else:
        name = line

    if name in blackList:
        await banMatcher.reject(f"歌曲《{name}》已存在于黑名单中，无需重复拉黑")
    blackList.append(name)

    fs = open("./store/blackList.json", 'w')
    blackListStr = json.dumps(blackList)
    fs.write(blackListStr)
    fs.close()

    await banMatcher.finish(f"歌曲《{name}》已加入黑名单")


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


@commandMatcher.handle()
async def startOrder():
    await run_start_order()
    await commandMatcher.send("已开启点歌")
