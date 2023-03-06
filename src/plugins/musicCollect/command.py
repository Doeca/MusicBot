import json
from . import cron
from . import util
from . import config
from typing import Union
from nonebot import on_command,  on_regex, on_fullmatch
from nonebot.log import logger
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg,  ArgStr
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER


async def group_checker(e: Union[GroupMessageEvent, PrivateMessageEvent]) -> bool:
    if e.message_type == 'private':
        return True
    return e.group_id == config.bot.notice_id


listMatcher = on_regex('^(歌曲列表|播放列表|待播清单|歌单)$', rule=group_checker)
playingMatcher = on_regex(
    '正在播放|当前播放|放的是什么|现在.{1,8}什么|放的.{1,6}哪首歌', rule=group_checker)
commandMatcher = on_command(
    "orderStart", permission=SUPERUSER, rule=group_checker)
banMatcher = on_command("ban", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER), rule=group_checker)
keyMatcher = on_command("addkey", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER), rule=group_checker)
nextMatcher = on_command("next", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER), rule=group_checker)
blackMatcher = on_fullmatch("黑名单列表", rule=group_checker)


@blackMatcher.handle()
async def blackhandle(e: Event, bot: Bot):
    await bot.send(e, util.generateBlack(), at_sender=True, reply_message=True)


@nextMatcher.handle()
async def next(e: Event, bot: Bot):
    util.addOperation('next')
    await bot.send(e, "已切换到下一首歌", at_sender=True, reply_message=True)


@listMatcher.handle()
async def retList(e: Event, bot: Bot):
    await bot.send(e, util.generateList(), at_sender=True, reply_message=True)


@playingMatcher.handle()
async def retList(e: Event, bot: Bot):
    await bot.send(e, util.generatePlay(), at_sender=True, reply_message=True)


@banMatcher.handle()
async def banHandle(matcher: Matcher, args: Message = CommandArg()):
    id = args.extract_plain_text().strip()
    logger.debug(f"ID : {id}")
    if id == '':
        id = util.currentPlay()
    elif id.isdigit():
        id = int(id)
    else:
        matcher.set_arg("arg", id.strip())
        return
    if id == 0:
        return
    if id <= len(config.getValue('orderList')):
        matcher.set_arg("arg", str(id))


@banMatcher.got("arg", prompt="请输入歌曲列表中的序号 or 直接输入歌曲名")
async def banID(arg: str = ArgStr('arg')):
    blackList = config.getValue('blackList')
    orderList = config.getValue('orderList')

    line = arg.strip()
    name = ''

    if line == '':
        await banMatcher.finish(f"操作已取消")
    elif line.isdigit():
        id = int(line)
        if id == 0 or id > len(orderList):
            await banMatcher.reject(f"歌曲序号：{id}不存在，请重新输入")
        name = orderList[id-1]['name']
        if id == util.currentPlay():
            util.addOperation('next')
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


@commandMatcher.handle()
async def startOrder():
    logger.debug("receive")
    await cron.run_start_order()


@keyMatcher.handle()
async def banHandle(matcher: Matcher, args: Message = CommandArg()):
    key = args.extract_plain_text().strip()
    logger.debug(f"Key : {key}")
    if key != '':
        matcher.set_arg("arg", key)


@keyMatcher.got("arg", prompt="请输入关键词（注意，若关键词过短会影响其他歌曲）")
async def banID(arg: str = ArgStr('arg')):
    blackKeyList = config.getValue('blackKeyList')
    name = arg.strip()
    if name == '':
        await keyMatcher.finish(f"操作已取消")

    if name in blackKeyList:
        await keyMatcher.reject(f"关键词'{name}'已存在于黑名单中，无需重复加入")
    blackKeyList.append(name)

    fs = open("./store/blackKeyList.json", 'w')
    blackKeyListStr = json.dumps(blackKeyList)
    fs.write(blackKeyListStr)
    fs.close()

    await banMatcher.finish(f"关键词'{name}'已加入黑名单")
