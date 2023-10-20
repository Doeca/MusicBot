import json
from . import util
from . import config
from . import wxlib
from nonebot.log import logger
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg,  ArgStr
from nonebot import on_command,  on_regex
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER

# 帮助
help_matcher = on_regex('帮助|\/help')


@help_matcher.handle()
async def help(e: GroupMessageEvent, bot: Bot):
    fs = open("./help.store", "r")
    resp = fs.read()
    fs.close()
    await bot.send(e, message=resp, at_sender=True, reply_message=True)


# 1.歌单
song_list_matcher = on_regex('^(歌曲列表|播放列表|待播清单|歌单)$', rule=util.group_checker)


@song_list_matcher.handle()
async def song_list(e: GroupMessageEvent, bot: Bot):
    school_id = await config.get_id(str(e.group_id))
    resp = await util.generateSongList(school_id)
    await bot.send(e, message=resp, at_sender=True, reply_message=True)

# 2.正在播放
playing_matcher = on_regex(
    '正在播放|当前播放|放的是什么|现在.{1,8}什么|放的.{1,6}哪首歌', rule=util.group_checker)


@playing_matcher.handle()
async def playing(e: GroupMessageEvent, bot: Bot):
    school_id = await config.get_id(str(e.group_id))
    info = config.schoolInfo.get(school_id, None)
    title = info['current_song_title']
    if (title == ""):
        resp = '👁‍🗨当前没有在播放歌曲'
    else:
        resp = f"🅿️当前歌曲【{title}】"
    await bot.send(e, message=resp, at_sender=True, reply_message=True)

# 3.切歌
next_matcher = on_command("next", aliases={"切歌"}, rule=util.group_checker)


@next_matcher.handle()
async def next(e: GroupMessageEvent, bot: Bot):
    school_id = await config.get_id(str(e.group_id))
    info: dict = config.schoolInfo.get(school_id, dict())
    if (info.get("current_song_id", 0) == 0):
        resp = "当前没有在播放歌曲哦，无法切歌"
        await bot.send(e, message=resp, at_sender=True, reply_message=True)
        return

    # 读取权限
    userid = str(e.user_id)
    perm = (SUPERUSER | GROUP_ADMIN | GROUP_OWNER)
    res: bool = await perm(bot, e)

    vote_need = info['tzinfo']['voteneed']
    if (res == True):
        await util.addOperation(school_id, 'next')
        resp = "已切换到下一首歌"
        await bot.send(e, message=resp, at_sender=True, reply_message=True)
    else:
        vote_num = info['vote_num']
        vote_list = info['vote_list']
        if (userid in vote_list):
            resp = f"你已经参与过投票了，当前进度：{vote_num}/{vote_need}"
            await bot.send(e, message=resp, at_sender=True, reply_message=True)
            return
        vote_num += 1
        vote_list.append(userid)

        if (vote_num >= vote_need):
            await util.addOperation(school_id, 'next')
            resp = "切歌票数已达标，切换到下一首歌"
        else:
            resp = f"你已经参与过投票了，当前进度：{vote_num}/{vote_need}"
        async with config.lock:
            fs = open(f"./store/{school_id}/{info['log_file']}", "w")
            fs.write(json.dumps(info))
            fs.close()
        await bot.send(e, message=resp, at_sender=True, reply_message=True)


# 4.谁点的歌
who_matcher = on_command(
    "who", aliases={"谁点的", "点歌人"}, rule=util.group_checker)


@who_matcher.handle()
async def who_handle(e: GroupMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    school_id = await config.get_id(str(e.group_id))
    info: dict = config.schoolInfo.get(school_id, dict())
    id = args.extract_plain_text().strip()
    if id == '':
        id = info['current_song_id']
    elif id.isdigit():
        id = int(id)
    if id == 0:
        return
    if id <= len(info['song_list']):
        matcher.set_arg("arg", str(id))


@who_matcher.got("arg", prompt="请输入歌曲列表中的序号")
async def who_got(bot: Bot, e: GroupMessageEvent, arg: str = ArgStr('arg')):
    school_id = await config.get_id(str(e.group_id))
    info: dict = config.schoolInfo.get(school_id, dict())

    song_list = info['song_list']
    line = arg.strip()
    if line.isdigit():
        id = int(line)
        if id == 0 or id > len(song_list):
            await who_matcher.reject(f"歌曲序号：{id}不存在，请重新输入")
    else:
        await who_matcher.finish(f"操作已取消")
    userid: str = song_list[id-1]['uin']
    name = f"{song_list[id-1]['name']} - {song_list[id-1]['author']}"
    if userid.find("wx") != -1:
        userinfo = await wxlib.getMemberInfo(userid)
        card = f"微信用户 {userinfo['nickname']}({userinfo['account']})"
    else:
        stranger_info = await bot.get_stranger_info(user_id=userid)
        card = f"{stranger_info['nickname']}({userid})"
    resp = f"歌曲《{name}》的点歌人是：{card}"

    await bot.send(e, message=resp, at_sender=True, reply_message=True)

rule_matcher = on_command(
    "rule", aliases={"规则", "点歌规则"})


@rule_matcher.handle()
async def rule(bot: Bot, e: GroupMessageEvent):
    school_id = await config.get_id(str(e.group_id))
    if (school_id == ""):
        return
    setting: dict = config.schoolSettings[school_id]
    resp = "🤘🎵点歌规则：\n"
    id = 0
    for v in setting['timezone']:
        id = id + 1
        time = [util.handleTime(f"{v['settime'][0]}:{v['settime'][1]}"),
                util.handleTime(f"{v['settime'][2]}:{v['settime'][3]}")]
        resp += f"{id}. {time[0]}--{time[1]}\n"
        resp += f" 歌单上限{v['mainlimit']}首，每人限点{v['personlimit']}首\n"

    resp += "🧿支持平台: QQ音乐、网易云音乐"
    await bot.send(e, message=resp, at_sender=True, reply_message=True)

logger.info("用户端命令加载完成")
