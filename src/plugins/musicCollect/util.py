import time
import datetime
import json
import aiohttp
from . import config
import urllib.parse
import hashlib
from nonebot import get_bot as nbget_bot
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Event
import asyncio
import socket
from openai import OpenAI


def unescape(str: str):
    str = str.replace("\\/", "/")
    return str.replace("&#44;", ",").replace("&#91;", "[").replace("&#93;", ']').replace("&amp;", "&")


def urlencode(str: str):
    return urllib.parse.quote(str)


def getmd5(data):
    md5 = hashlib.md5()
    md5.update(data.encode('utf-8'))
    hash_result = md5.hexdigest()
    return hash_result


async def httpGet(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:  # Check if the response status is OK
                data = await resp.text()  # Parse JSON from the response
                return data
            else:
                return None


async def httpPost(url, json_data, head={}):
    head['Content-Type'] = 'application/json'  # 设置请求头为 JSON 格式
    async with aiohttp.ClientSession(headers=head) as session:
        async with session.post(url, json=json_data,) as response:
            if response.status == 200:
                response_data = await response.json()  # 解析响应的 JSON 数据
                return response_data
            else:
                return None


async def get_realurl(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=False) as resp:
            return resp.headers.get('Location', '')


async def group_checker(e: GroupMessageEvent) -> bool:
    school_id = await config.get_id(str(e.group_id))
    if (school_id == ''):
        return False
    if config.schoolSettings[school_id]['switch'] == 0:
        return False
    return True

# 检查歌曲名中是否有违禁词


async def is_black(name: str):
    bankeywords: list = config.globalConfig.get('bankeywords', [])
    for word in bankeywords:
        word = word.lower()
        name = name.lower()
        name = name.replace(" ", "")
        if name.find(word) != -1:
            return True
    return False


async def get_switch(school_id: str):
    # 获取当前点歌状态
    """
    通过schoolid尝试获取schoolInfo，然后get switch_status，如果开启则直接返回开启
    否则去读取学校设置，判断是否在某个时间段里，如果在就执行cron的开启点歌计划
    """
    if (school_id == ""):
        return False
    if config.schoolSettings[school_id]['switch'] == 0:
        # 这个是全局开关
        return False
    info: dict = config.schoolInfo.get(school_id, {})
    if (info.get('switch_status', 0) == 1):
        return True
    setting: dict = config.schoolSettings[school_id]
    now_time = int(time.strftime("%H", time.localtime()))*60 + \
        int(time.strftime("%M", time.localtime()))
    weekday_number = datetime.date.today().weekday() + 1

    # 点歌时间段内会自动开启，点歌时间段外不能自动关闭，防止手动开启点歌等情况
    # 同一个点歌时间段，配合不同的星期数，可以设置多个点歌时间段
    for tzinfo in setting['timezone']:
        set_time = tzinfo['settime']
        minute_start = set_time[0] * 60 + set_time[1]
        minute_stop = set_time[2] * 60 + set_time[3]
        if (minute_start < now_time and now_time < minute_stop and weekday_number in tzinfo['setdate']):
            from . import cron
            await cron.run_start_order(school_id, tzinfo)
            return True
    return False


async def addTolist(bot_para, school_id: str, songid: str, type: str, user_id: str):
    try:
        """
        点歌实际处理逻辑，将数据添加到info中，type选填wy或qq
        """
        apiUrl = config.system.music_api
        resp = await httpGet(f"{apiUrl}/{type}/detail?id={songid}&key=D8as1gv34")
        if resp == None:
            return {'code': -1, "msg": "该平台维护中，请稍后再试😢"}
        res: dict = json.loads(resp)

        info: dict = config.schoolInfo.get(school_id, {})
        setting: dict = config.schoolSettings[school_id]

        song_list: list = info.get('song_list', [])
        play_list: list = info.get('play_list', [])
        order_users: dict = info.get('order_users', {})
        if (order_users.get(f"user{user_id}", 0) >= info['tzinfo']['personlimit']):
            return {'code': -3, "msg": f"该时段每人限点{info['tzinfo']['personlimit']}首，你无法继续点歌🫣"}
        if (len(song_list) >= info['tzinfo']['mainlimit']):
            return {'code': -4, "msg": f"很抱歉，此时段点歌数量已达{info['tzinfo']['mainlimit']}首，无法继续点歌了💦"}

        # 针对关键词进行审查
        if await is_black(res['name']+"#"+res['author']):
            return {'code': -5, "msg": "awa，不知道为什么点歌失败了！🥺"}

        # 针对语言进行检查
        lang_list = setting.get("languages_whitelist", [])
        if len(lang_list) > 0 and res['lang'] not in lang_list:
            logger.debug(f"{res['name']} : {res['lang']}")
            return {'code': -5, "msg": "awa，不知道为什么点歌失败了！🥺"}
        lang_max = setting.get('languages_limit', {}).get(
            res['lang'], None)  # 时段设置中不一定有languages_limit，所以使用get函数
        if lang_max != None:
            lang_num = info['languagerecords'].get(res['lang'], 0)
            if lang_num >= lang_max:
                return {'code': -5, "msg": f"awa，不知道为什么点歌失败了！🥺"}
            lang_num += 1
            async with config.lock:
                info['languagerecords'][res['lang']] = lang_num

        song_info = {
            "name": res['name'],
            "author": res['author'],
            "playUrl": res['playUrl'],
            "lrcUrl": res['lrcUrl'],
            "cover": res['cover'],
            "id": len(song_list) + 1,
            "uin": user_id,
            "lang": res['lang']
        }

        async with config.lock:
            info['order_users'][f"user{user_id}"] = order_users.get(
                f"user{user_id}", 0) + 1
            song_list.append(song_info)
            play_list.append({'id': song_info['id'], 'played': 0})
            config.upsert_info(info['log_id'], json.dumps(info))

        if song_info['id'] >= info['tzinfo']['mainlimit']:
            for gid in setting['groups']:
                bot: Bot = bot_para
                botid = (await bot.call_api("get_login_info"))['user_id']
                await bot.set_group_card(group_id=gid, user_id=botid, card='点歌列表已满，努力播放中～')

        return {'code': 0, "msg": f"🥳点歌成功，点歌序号：{song_info['id']}/{info['tzinfo']['mainlimit']}"}
    except Exception as e:
        logger.error(f"点歌失败，错误信息：{e}")
        logger.opt(exception=True).error("点歌失败")
        return {'code': -1, "msg": "系统、Err、错..误，请稍后再试😢"}

# 生成歌单


async def generateSongList(school_id):
    info: dict = config.schoolInfo.get(school_id, {})
    play_list = info.get('play_list', [])
    song_list = info.get('song_list', [])
    length = len(song_list)
    res = '🗒歌曲列表（🅿️正在播放）：'
    id = info.get('current_song_id', 0)
    if length == 0:
        return '😗当前歌曲列表为🈳️'
    else:
        for v in play_list:
            if v['id'] > 10000:
                continue
            song_info = song_list[v['id']-1]
            res += "\n"
            if song_info['id'] == id:
                res += '🅿️'
            elif (v['played'] == 1):
                res += '✅'
            else:
                res += '💮'
            res += f"No.{song_info['id']} {song_info['name']} - {song_info['author']}"
        return res


# 将操作加入操作列表
async def addOperation(school_id, type: str, para=0):
    info = config.schoolInfo.get(school_id, None)
    if (info == None):
        return
    async with config.lock:
        info['operation_list'].append({"type": type, "para": para})
        config.upsert_info(info['log_id'], json.dumps(info))


# 处理时间的显示格式
def handleTime(s: str):
    a = s.split(":")
    if (len(a[0]) == 1):
        a[0] = '0' + a[0]
    if (len(a[1]) == 1):
        a[1] = '0' + a[1]
    return f'{a[0]}:{a[1]}'


def get_music_info(text: str):
    client = OpenAI(
        api_key="sk-RYAWYlFFrC0lQ6vOEypwwvNZG3kXISIsN4ysU5EkuHwTltOF",
        base_url="https://api.moonshot.cn/v1",
    )
    system_prompt = """帮我从用户的输入中获取如下参数：
    1. 歌曲名-歌手名（歌手名可能不存在）
    2. 消息（是祝福词后面的内容，如果没有则置空）
    并以json格式回传：
    {"keywords":"歌曲名 歌手名","msg":"消息内容"}"""
    completion = client.chat.completions.create(
        model="moonshot-v1-auto",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": text,
            },
            {
                "role": "assistant",
                "content": "{",
                "partial": True
            },
        ],
        temperature=0.6,
    )

    res = '{'+completion.choices[0].message.content
    return json.loads(res)


def get_lan_ip() -> str | None:
    for info in socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET):
        ip = info[4][0]
        if ip.startswith("192."):
            return ip
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        try:
            probe.connect(("192.168.0.1", 80))
            candidate = probe.getsockname()[0]
            if candidate.startswith("192."):
                return candidate
        except OSError:
            return None
    return None
