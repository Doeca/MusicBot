import time
import datetime
import random
import asyncio
import json
import aiohttp
from . import config
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Event


async def httpGet(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:  # Check if the response status is OK
                data = await resp.text()  # Parse JSON from the response
                return data
            else:
                return None


async def get_realurl(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, allow_redirects=False) as resp:
            return resp.headers.get('Location', '')


async def group_checker(e: GroupMessageEvent) -> bool:
    if (config.get_id(e.group_id) == ''):
        return False
    return True


async def is_black(school_id: str, name: str):
    setting: dict = config.schoolSettings[school_id]
    bankeywords: list = setting.get('bankeywords', [])
    for word in bankeywords:
        if name.find(word) != -1:
            return True
    return False


async def get_switch(school_id: str):
    # 获取当前点歌状态
    """
    通过schoolid尝试获取schoolInfo，然后get switch_status，如果开启则直接返回开启
    否则去读取学校设置，判断是否在某个时间段里，如果在就执行cron的开启点歌计划
    """
    info: dict = config.schoolInfo.get(school_id, {})
    if (info.get('switch_status', 0) == 1):
        return True
    # print("学校id", school_id)
    # print(config.schoolSettings)
    setting: dict = config.schoolSettings[school_id]
    now_time = int(time.strftime("%H", time.localtime()))*60 + \
        int(time.strftime("%M", time.localtime()))
    weekday_number = datetime.date.today().weekday() + 1

    # 点歌时间段内会自动开启，点歌时间段外不能自动关闭，防止手动开启点歌等情况
    for tzinfo in setting['timezone']:
        set_time = tzinfo['settime']
        minute_start = set_time[0] * 60 + set_time[1]
        minute_stop = set_time[2] * 60 + set_time[3]
        if (minute_start < now_time and now_time < minute_stop and weekday_number in tzinfo['setdate']):
            from . import cron
            await cron.run_start_order(school_id, tzinfo)
            return True
    return False


async def addTolist(school_id: str, songid: str, type: str, user_id: int):
    """
    点歌实际处理逻辑，将数据添加到info中，type选填wy或qq
    """
    apiUrl = config.system.music_api
    resp = await httpGet(f"{apiUrl}/{type}/detail?id={songid}")
    if resp == None:
        return {'code': -1, "msg": "点歌失败，请稍后再试😢"}

    res: dict = json.loads(resp)
    black = await is_black(school_id, res['name'])
    if black:
        return {'code': -2, "msg": f"歌曲《{res['name']}》在黑名单中，无法进行点歌🐵"}

    info: dict = config.schoolInfo.get(school_id, {})
    song_list: list = info.get('song_list', [])
    order_users: dict = info.get('order_users', {})
    print(order_users)
    if (order_users.get(f"user{user_id}", 0) >= info['tzinfo']['personlimit']):
        return {'code': -3, "msg": f"该时段每人限点{info['tzinfo']['personlimit']}首，你无法继续点歌🫣"}
    if (len(song_list) >= info['tzinfo']['mainlimit']):
        return {'code': -4, "msg": f"很抱歉，此时段点歌数量已达{info['tzinfo']['mainlimit']}首，无法继续点歌了💦"}

    async with config.lock:
        info['order_users'][f"user{user_id}"] = order_users.get(
            f"user{user_id}", 0) + 1
        song_info = {
            "name": res['name'],
            "author": res['author'],
            "playUrl": res['playUrl'],
            "lrcUrl": res['lrcUrl'],
            "cover": res['cover'],
            "played": 0,
            "id": len(song_list) + 1,
            "uin": user_id
        }
        song_list.append(song_info)
        fs = open(f"./store/{info['log_file']}", "w")
        fs.write(json.dumps(info))
        fs.close()

    if song_info['id'] >= info['tzinfo']['mainlimit']:
        botid = config.system.bot_id
        bot: Bot = get_bot(str(botid))
        setting: dict = config.schoolSettings[school_id]
        for gid in setting['groups']:
            await bot.set_group_card(group_id=gid, user_id=botid, card='点歌列表已满，努力播放中～')

    return {'code': 0, "msg": f"🥳点歌成功，点歌序号：{song_info['id']}/{info['tzinfo']['mainlimit']}"}
