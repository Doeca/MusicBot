import time
import datetime
import json
import aiohttp
from . import config
from . import wxlib
from nonebot import get_bot as nbget_bot
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Event
import asyncio


def unescape(str: str):
    str = str.replace("\\/", "/")
    return str.replace("&#44;", ",").replace("&#91;", "[").replace("&#93;", ']').replace("&amp;", "&")


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
    res = await get_switch(school_id)
    return res

# 检查歌曲名中是否有违禁词


async def is_black(school_id: str, name: str):
    setting: dict = config.schoolSettings[school_id]
    bankeywords: list = setting.get('bankeywords', [])
    for word in bankeywords:
        if name.find(word) != -1:
            return True
    return False

lock = asyncio.Lock()


async def get_bot():
    # 方案已废弃，不再使用

    # 使用本函数意味着事件源不来自QQ，为自行创建的事件（例如定时任务）
    # 调用地方：
    # 1. 定时任务开启任务、关闭任务
    # 2. WebAPI播报当前歌曲
    # 3. Wechat “谁点的”命令获取点歌人的信息

    # botid为shamrock中默认登录的那个qq号，也就是bot_ids的第一个qq号，通过pop读取然后丢弃，如果这个账号出现问题需要切换，那么再从后续的id中读取
    async with lock:
        bot: Bot = nbget_bot()
        # 如果这里是None的话说明Shamrock已经丢失连接了
        if bot == None:
            logger.error("Shamrock已掉线，无法正常通信")
            return None
        try:
            await bot.call_api("get_stranger_info", user_id=1124468334)
            logger.info("账号正常")
        except:
            # 如果调用失败则需要切换账号
            await bot.call_api("switch_account", user_id=config.system.bot_ids.pop(0))
            logger.info("账号切换请求已完成")
            await asyncio.sleep(3)
            await bot.send_private_msg(user_id=1124468334, message=f"Shamrock原账号已掉线，已自动切换账号为本号")
        return bot


async def get_switch(school_id: str):
    # 获取当前点歌状态
    """
    通过schoolid尝试获取schoolInfo，然后get switch_status，如果开启则直接返回开启
    否则去读取学校设置，判断是否在某个时间段里，如果在就执行cron的开启点歌计划
    """
    if (school_id == ""):
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
        fs = open(f"./store/{school_id}/{info['log_file']}", "w")
        fs.write(json.dumps(info))
        fs.close()

    if song_info['id'] >= info['tzinfo']['mainlimit']:
        setting: dict = config.schoolSettings[school_id]
        for gid in setting['groups']:
            if gid.find("@chatroom") != -1:
                wxlib.changeCard(gid, '点歌列表已满，努力播放中～')
            else:
                bot: Bot = bot_para
                botid = (await bot.call_api("get_login_info"))['user_id']
                # await bot.set_group_card(group_id=gid, user_id=botid, card='点歌列表已满，努力播放中～')

    return {'code': 0, "msg": f"🥳点歌成功，点歌序号：{song_info['id']}/{info['tzinfo']['mainlimit']}"}

# 生成歌单


async def generateSongList(school_id):
    info = config.schoolInfo.get(school_id, None)
    song_list = info['song_list']
    length = len(song_list)
    res = '🗒歌曲列表（🅿️正在播放）：'
    id = info['current_song_id']
    if length == 0:
        return '😗当前歌曲列表为🈳️'
    else:
        for v in song_list:
            res += "\n"
            if v['id'] == id:
                res += '🅿️'
            elif (v['played'] == 1):
                res += '✅'
            else:
                res += '💮'
            res += f"No.{v['id']} {v['name']} - {v['author']}"
        return res


# 将操作加入操作列表
async def addOperation(school_id, type: str, para=0):
    async with config.lock:
        info = config.schoolInfo.get(school_id, None)
        if (info == None):
            return
        info['operation_list'].append({"type": type, "para": para})
        fs = open(f"./store/{school_id}/{info['log_file']}", "w")
        fs.write(json.dumps(info))
        fs.close()


# 处理时间的显示格式
def handleTime(s: str):
    a = s.split(":")
    if (len(a[0]) == 1):
        a[0] = '0' + a[0]
    if (len(a[1]) == 1):
        a[1] = '0' + a[1]
    return f'{a[0]}:{a[1]}'
