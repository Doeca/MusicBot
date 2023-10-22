import re
import json
from . import config
from . import wxlib
from . import util
from nonebot import logger, get_bot

# 群消息处理

commands = list()


def commandReg(command_reg: str):
    def decorator(func):
        commands.append({"reg": command_reg, "func": func})

        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            return result
        return wrapper
    return decorator


async def entrance(gid: str, user_id, msg: str):
    school_id = await config.get_id(str(gid))
    if (school_id == ""):
        return
    await music_handle(school_id, gid, user_id, msg)
    for crg in commands:
        match = re.search(crg['reg'], msg)
        if (match != None):
            await crg['func'](school_id, gid, user_id, match)


async def music_handle(school_id: str, gid: str, user_id, msg: str):
    qqid = await qq_matcher(msg)
    wyid = await wyy_matcher(msg)
    if qqid == "" and wyid == "":
        return
    status = await util.get_switch(school_id)
    if status == False:
        await wxlib.sendMsg(gid, "当前不在点歌时间段内，不能点歌哦🥺", user_id)
        return
    if qqid != "":
        res = await util.addTolist(school_id, qqid, 'qq', user_id)
    else:
        res = await util.addTolist(school_id, wyid, 'wy', user_id)
    await wxlib.sendMsg(gid, res['msg'], user_id)


@commandReg('^/音量(\d+)%$')
async def help_handle(school_id: str, gid: str, user_id: str, match):
    res = await util.get_switch(school_id)
    if not res:
        return
    res: bool = await wxlib.isAdmin(gid, user_id)
    if not res:
        return
    volume = float(match.group(1))
    await util.addOperation(school_id, "volume", volume*0.01)
    resp = f"已将音量调整为{volume}%"
    await wxlib.sendMsg(gid, resp, user_id)


@commandReg('^/点歌规则$')
async def rule_handle(school_id: str, gid: str, user_id: str, match):
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
    await wxlib.sendMsg(gid, resp, user_id)


@commandReg('^/谁点的(\d*)$')
async def who_handle(school_id: str, gid: str, user_id: str, match):
    res = await util.get_switch(school_id)
    if not res:
        return
    info: dict = config.schoolInfo.get(school_id, dict())
    song_list = info['song_list']
    line: str = match.group(1)
    if line == "":
        line = info['current_song_id']
    id = int(line)
    if id > 10000:
        resp = f"当前播放的是随机歌曲哦🎵"
        await wxlib.sendMsg(gid, resp, user_id)
        return
    if id == 0 or id > len(song_list):
        resp = f"歌曲序号：{id}不存在"
        await wxlib.sendMsg(gid, resp, user_id)
        return
    userid: str = song_list[id-1]['uin']
    name = f"{song_list[id-1]['name']} - {song_list[id-1]['author']}"
    if userid.find("wx") != -1:
        userinfo = await wxlib.getMemberInfo(userid)
        card = f"{userinfo['nickname']}({userinfo['account']})"
    else:
        bot = get_bot(config.system.bot_id)
        stranger_info = await bot.get_stranger_info(user_id=userid)
        card = f"QQ用户 {stranger_info['nickname']}({userid})"
    resp = f"歌曲《{name}》的点歌人是：{card}"
    await wxlib.sendMsg(gid, resp, user_id)


@commandReg('帮助|/help')
async def help_handle(school_id: str, gid: str, user_id: str, match):
    fs = open("./help.store", "r")
    resp = fs.read()
    fs.close()
    await wxlib.sendMsg(gid, resp, user_id)


@commandReg('^(歌曲列表|播放列表|待播清单|歌单)$')
async def list_handle(school_id: str, gid: str, user_id: str, match):
    res = await util.get_switch(school_id)
    if not res:
        return
    resp = await util.generateSongList(school_id)
    await wxlib.sendMsg(gid, resp, user_id)


@commandReg('正在播放|当前播放|放的是什么|现在.{1,8}什么|放的.{1,6}哪首歌')
async def now_handle(school_id: str, gid: str, user_id: str, match):
    res = await util.get_switch(school_id)
    if not res:
        return
    info = config.schoolInfo.get(school_id, None)
    title = info['current_song_title']
    if (title == ""):
        resp = '👁‍🗨当前没有在播放歌曲'
    else:
        resp = f"🅿️当前歌曲【{title}】"
    await wxlib.sendMsg(gid, resp, user_id)


@commandReg('^/切歌$')
async def next_handle(school_id: str, gid: str, user_id: str, match):
    res = await util.get_switch(school_id)
    if not res:
        return
    info: dict = config.schoolInfo.get(school_id, dict())
    if (info.get("current_song_id", 0) == 0):
        resp = "当前没有在播放歌曲哦，无法切歌"
        await wxlib.sendMsg(gid, resp, user_id)
        return

    # 读取权限
    res: bool = await wxlib.isAdmin(gid, user_id)

    vote_need = info['tzinfo']['voteneed']
    if (res == True):
        await util.addOperation(school_id, 'next')
        resp = "已切换到下一首歌"
        await wxlib.sendMsg(gid, resp, user_id)
        return
    else:
        vote_num = info['vote_num']
        vote_list = info['vote_list']
        if (user_id in vote_list):
            resp = f"你已经参与过投票了，当前进度：{vote_num}/{vote_need}"
            await wxlib.sendMsg(gid, resp, user_id)
            return
        vote_num += 1
        vote_list.append(user_id)

        if (vote_num >= vote_need):
            await util.addOperation(school_id, 'next')
            resp = "切歌票数已达标，切换到下一首歌"
        else:
            resp = f"你已经参与过投票了，当前进度：{vote_num}/{vote_need}"
        async with config.lock:
            fs = open(f"./store/{school_id}/{info['log_file']}", "w")
            fs.write(json.dumps(info))
            fs.close()
    await wxlib.sendMsg(gid, resp, user_id)


async def qq_matcher(content: str):
    # 格式一
    match = re.search(
        'https:\/\/c6.y.qq.com\/base\/fcgi-bin\/u\?__=([a-zA-Z0-9]{10,15})', content)
    if match != None:
        resp = await util.httpGet(match.group(0))
        matchObj = re.search(r'"mid":"(.*?)"', resp, re.M | re.I)
        if matchObj != None:
            return matchObj.group(1)

    # 可以直接获取songmid的格式
    reg_str = [
        "<dataurl>.*?songmid=(.*?)&.*?</dataurl>"
    ]
    for rs in reg_str:
        match = re.search(rs, content)
        if match != None:
            return match.group(1)
    return ""


async def wyy_matcher(content: str):

    # 特殊格式一
    match = re.search('http(s|):\/\/163cn\.tv\/[a-zA-Z0-9]{3,7}', content)
    if match != None:
        link = await util.get_realurl(match.group(0))
        matches = re.search('&id=([0-9]{1,})', link)
        if matches != None:
            return matches.group(1)
        
    # 可以直接取到songid的格式
    reg_str = [
        "http.*?music\.163\.com.*?&amp;id=([0-9]{1,})",
        "https:.*y\.music.*m\/song\?id=([0-9]{1,})&"
    ]
    for rs in reg_str:
        match = re.search(rs, content)
        if match != None:
            return match.group(1)
    return ""

# QQ处理器
# 网易云处理器
# 其它命令处理器
# 加好友事件处理 -> testanything ok.still can use
