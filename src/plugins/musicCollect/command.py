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



debugMatcher = on_command("debug", permission=(
    SUPERUSER), rule=util.group_checker)
listMatcher = on_regex('^(歌曲列表|播放列表|待播清单|歌单)$', rule=util.group_checker)
playingMatcher = on_regex(
    '正在播放|当前播放|放的是什么|现在.{1,8}什么|放的.{1,6}哪首歌', rule=util.group_checker)
commandMatcher = on_command(
    "orderStart", permission=SUPERUSER, rule=util.group_checker)
stopMatcher = on_command(
    "orderStop", permission=SUPERUSER, rule=util.group_checker)
banMatcher = on_command("ban", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER), rule=util.group_checker)
keyMatcher = on_command("addkey", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER), rule=util.group_checker)
nextMatcher = on_command("next", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER), rule=util.group_checker)

blackMatcher = on_fullmatch("黑名单列表", rule=util.group_checker)
setPriorMatcher = on_command(
    "setPrior", aliases={"提前", "生日快乐"}, rule=util.group_checker)


@blackMatcher.handle()
async def blackhandle(e: Event, bot: Bot):
    await bot.send(e, util.generateBlack(await util.getID(bot)), at_sender=True, reply_message=True)


@nextMatcher.handle()
async def next(e: Event, bot: Bot):
    util.addOperation(await util.getID(bot), 'next')
    await bot.send(e, "已切换到下一首歌", at_sender=True, reply_message=True)


@listMatcher.handle()
async def retList(e: Event, bot: Bot):
    await bot.send(e, util.generateList(await util.getID(bot)), at_sender=True, reply_message=True)


@playingMatcher.handle()
async def retList(e: Event, bot: Bot):
    await bot.send(e, util.generatePlay(await util.getID(bot)), at_sender=True, reply_message=True)


@banMatcher.handle()
async def banHandle(bot: Bot, matcher: Matcher, args: Message = CommandArg()):
    botid = await util.getID(bot)
    id = args.extract_plain_text().strip()
    logger.debug(f"ID : {id}")
    if id == '':
        id = util.currentPlay(botid)
    elif id.isdigit():
        id = int(id)
    else:
        matcher.set_arg("arg", id.strip())
        return
    if id == 0:
        return
    if id <= len(config.getVal(botid, 'orderList')):
        matcher.set_arg("arg", str(id))


@banMatcher.got("arg", prompt="请输入歌曲列表中的序号 or 直接输入歌曲名")
async def banID(bot: Bot, arg: str = ArgStr('arg')):
    botid = await util.getID(bot)
    blackList = config.getVal(botid, 'blackList')
    orderList = config.getVal(botid, 'orderList')

    line = arg.strip()
    name = ''
    if line == '':
        await banMatcher.finish(f"操作已取消")
    elif line.isdigit():
        id = int(line)
        if id == 0 or id > len(orderList):
            await banMatcher.reject(f"歌曲序号：{id}不存在，请重新输入")
        name = orderList[id-1]['name']
        rawList: list = config.getVal(botid, 'orderList')
        if id == util.currentPlay(botid):
            util.addOperation(botid, 'next')
        if id > util.currentPlay(botid):
            rawList.pop(id - 1)
        id = 1
        for v in rawList:
            v['id'] = id
            id = id + 1
    else:
        name = line

    if name in blackList:
        await banMatcher.finish(f"歌曲《{name}》已存在于黑名单中，无需重复拉黑")
    blackList.append(name)

    fs = open(f"./settings/{botid}/blackList.json", 'w')
    blackListStr = json.dumps(blackList)
    fs.write(blackListStr)
    fs.close()

    await banMatcher.finish(f"歌曲《{name}》已加入黑名单")


@commandMatcher.handle()
async def startOrder(e: Event, bot: Bot):
    botid = await util.getID(bot)
    await cron.run_start_order(botid)
    if config.getVal(botid, "debug") == 1:
        path = f"./debug.log"
        fp = open(path, "r")
        config.setVal(botid, 'orderList', json.loads(fp.read()))
        fp.close()
        logger.debug("已载入本地听歌列表")
        await bot.send(e, "已载入本地听歌列表", at_sender=True, reply_message=True)


@stopMatcher.handle()
async def stopOrder(e: Event, bot: Bot):
    await cron.run_stop_order(await util.getID(bot))


@keyMatcher.handle()
async def banHandle(bot: Bot, matcher: Matcher, args: Message = CommandArg()):
    key = args.extract_plain_text().strip()
    logger.debug(f"Key : {key}")
    if key != '':
        matcher.set_arg("arg", key)


@keyMatcher.got("arg", prompt="请输入关键词（注意，若关键词过短会影响其他歌曲）")
async def banID(bot: Bot, arg: str = ArgStr('arg')):
    botid = await util.getID(bot)
    blackKeyList = config.getVal(botid, 'blackKeyList')
    name = arg.strip()
    if name == '':
        await keyMatcher.finish(f"操作已取消")

    if name in blackKeyList:
        await keyMatcher.finish(f"关键词'{name}'已存在于黑名单中，无需重复加入")
    blackKeyList.append(name)

    fs = open(f"./settings/{botid}/blackKeyList.json", 'w')
    blackKeyListStr = json.dumps(blackKeyList)
    fs.write(blackKeyListStr)
    fs.close()

    await banMatcher.finish(f"关键词'{name}'已加入黑名单")


@setPriorMatcher.handle()
async def setPriorhandle(e: Event, bot: Bot):
    botid = await util.getID(bot)
    if (config.getVal(botid, 'orderSwitch') == 0):
        await bot.send(e, "当前不在点歌时间段内，不能使用该功能哦🥺", at_sender=True, reply_message=True)
        return
    if (config.getVal(botid, 'prioritified') == 1):
        await bot.send(e, f"很抱歉，该时段已经有人使用过提前播放功能了，不能再次使用😥", at_sender=True, reply_message=True)
        return
    qq = int(e.get_user_id())
    res = util.getOrder(botid, qq)
    nameList = util.getSongList(botid, res)

    if ('生日快乐' not in nameList):
        await bot.send(e, f"很抱歉，你点的歌不能提前播放，只有生日快乐歌才能提前播放哦🤧", at_sender=True, reply_message=True)
        return
    id = 0
    if (nameList[0].find("生日快乐") != -1):
        id = res[0]['id']
    else:
        id = res[1]['id']
    if (util.currentPlay(botid) >= id):
        await bot.send(e, f"很抱歉，此歌已经播放过了，不能重复播放😿", at_sender=True, reply_message=True)
        return
    if (util.currentPlay(botid)+1 == id):
        await bot.send(e, f"很抱歉，此歌本来就在下一首，无需提前播放😿", at_sender=True, reply_message=True)
        return
    util.changeOrder(botid, util.currentPlay(botid), id)
    config.setVal(botid, 'orderSwitch', 1)
    await bot.send(e, f"你点的生日快乐歌已经提前到下一首播放啦，祝你生日快乐🥳", at_sender=True, reply_message=True)


@debugMatcher.handle()
async def func(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher):
    botid = await util.getID(bot)
    matcher.stop_propagation()
    if (config.getVal(botid, 'debug') == 1):
        config.setVal(botid, 'debug', 0)
        await bot.send(message=f"🤐Turn off debug mode", event=e)
    else:
        config.setVal(botid, 'debug', 1)
        await bot.send(message=f"😆Switch to debug mode", event=e)
