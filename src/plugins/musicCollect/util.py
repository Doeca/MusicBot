import time
import random
import requests
from . import config
from typing import Union
from nonebot.utils import run_sync
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Event
waitForSend = dict()


@run_sync
def httpGet(url):
    return requests.get(url)


def unescape(str: str):
    str = str.replace("\\/", "/")
    return str.replace("&#44;", ",").replace("&#91;", "[").replace("&#93;", ']').replace("&amp;", "&")


def currentPlay(id):
    return config.getVal(id, 'currentID')


def generateList(id):
    orderList = config.getVal(id, 'orderList')
    length = len(orderList)
    res = '🗒歌曲列表（🅿️正在播放）：'
    id = currentPlay(id)
    if length == 0:
        return '😗当前歌曲列表为🈳️'
    else:
        for v in orderList:
            res += "\n"
            if v['id'] == id:
                res += '🅿️'
            elif (v['played'] == 1):
                res += '✅'
            else:
                res += '💮'
            res += f"No.{v['id']} {v['name']} - {v['author']}"
        return res


def addOperation(id, type: str, para=0):
    opertaionList = config.getVal(id, 'opertaionList')
    temp = dict()
    temp['type'] = type
    temp['para'] = para
    opertaionList.append(temp)


def generatePlay(id):
    title = config.getVal(id, 'currentTitle')
    if (title == ""):
        return '👁‍🗨当前没有在播放歌曲'
    return f"🅿️当前歌曲【{title}】"


def generateBlack(id):
    blackList = config.getVal(id, 'blackList')
    length = len(blackList)
    res = '📄歌曲黑名单：\n'
    i = 0
    for v in blackList:
        res += f"《{v}》"
        if i != length - 1:
            res += "，"
        i += 1
    if i == 0:
        res += "🈚️任何歌曲"

    blackKeyList = config.getVal(id, 'blackKeyList')
    length = len(blackKeyList)
    res += '\n关键词列表：\n'
    j = 0
    for v in blackKeyList:
        res += f"'{v}'"
        if j != length - 1:
            res += "，"
        j += 1
    if j == 0:
        res += "🈚️任何关键词\n"
    return res


def isBlack(id, name: str):
    blackList = config.getVal(id, 'blackList')
    blackKeyList = config.getVal(id, 'blackKeyList')
    if name in blackList:
        return True
    for v in blackKeyList:
        if name.find(v) != -1:
            return True
    return False


def getSongList(id, ex=None):
    """
    获取歌名列表，若传入ex则返回ex的歌名列表（配合获取指定人歌单）
    """
    songList = list()
    if (ex == None):
        orderList = config.getVal(id, 'orderList')
    else:
        orderList = ex
    for v in orderList:
        songList.append(v['name'])
    return songList


def getOrder(id, qq: int):
    """
    根据QQ获取其所点的所有歌曲
    """
    songList = list()
    orderList = config.getVal(id, 'orderList')
    for v in orderList:
        if (v['uin'] == qq):
            songList.append(v)
    return songList


def changeOrder(id, fir: int, sec: int):
    orderList = config.getVal(id, 'orderList')[:]
    rawList: list = config.getVal(id, 'orderList')
    sec_data = orderList[sec-1]

    rawList.pop(sec-1)
    rawList.insert(fir, sec_data)

    sid = 1
    for v in rawList:
        v['id'] = sid
        sid = sid + 1
    return True


async def isRunning(botid):
    status = config.getVal(botid, 'orderSwitch')
    ntime = int(time.strftime("%H", time.localtime()))*60 + \
        int(time.strftime("%M", time.localtime()))
    set_time = config.getVal(botid, 'set_time')
    amStart = set_time[0] * 60 + set_time[1]
    pmStart = set_time[2] * 60 + set_time[3]
    amStop = set_time[4] * 60 + set_time[5]
    pmStop = set_time[6] * 60 + set_time[7]

    # 点歌时间段内会自动开启，点歌时间段外不能自动关闭
    if ((amStart < ntime and ntime < amStop) or (pmStart < ntime and ntime < pmStop)):
        if (status != 1):
            from . import cron
            await cron.run_start_order(botid)
        return True
    else:
        if (status == 1):
            return True
        return False


async def getID(bot: Bot):
    v = await bot.get_login_info()
    while not isinstance(v, dict):
        v = await bot.get_login_info()
    return v['user_id']


async def group_checker(e: Union[GroupMessageEvent, PrivateMessageEvent], bot: Bot) -> bool:
    botid = await getID(bot)
    if (config.getSetting(botid) == None):
        return False
    if e.message_type == 'private':
        return True
    return e.group_id in config.getVal(botid, 'groups')


def handleTime(s: str):
    a = s.split(":")
    if (len(a[0]) == 1):
        a[0] = '0' + a[0]
    if (len(a[1]) == 1):
        a[1] = '0' + a[1]
    return f'{a[0]}:{a[1]}'


async def sendMsg(bot: Bot, event: Event, message: str, at_sender=True, reply_message=True):
    botid = await getID(bot)
    num = waitForSend.get(botid, 0)
    waitForSend.set(botid, num+1)
    time.sleep(num)
    time.sleep(random.randint(1, 3))
    time.sleep(int(len(message)/20))
    await bot.send(event, message, at_sender=at_sender, reply_message=reply_message)
    num = waitForSend.get(botid)
    waitForSend[botid] = num-1
