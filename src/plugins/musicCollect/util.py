import time
import json
import os
import nonebot
from .config import Config
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, GroupMessageEvent
from nonebot_plugin_apscheduler import scheduler
from typing import Union
from nonebot.log import logger
from nonebot import get_bot, get_driver
from nonebot import require
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


app: FastAPI = nonebot.get_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)
logger.debug(plugin_config.bot_id)
logger.debug(str(plugin_config.notice_id))

if os.path.exists("./store/blackList.json"):
    fs = open("./store/blackList.json", 'r')
    blackList = json.load(fs)
    fs.close()
else:
    blackList = list()

if not os.path.exists('./store'):
    os.makedirs('./store')

orderSwitch = 0  # 点歌开关
orderPeople = dict()  # 存放用户点歌数量
orderList = list()  # 歌曲信息列表
opertaionList = list()  # 存放传递给前端的操作信息
file_log = "default.log"  # 序列化存到本地的文件名
currentID = 0
maxList = 30


def unescape(str: str):
    return str.replace("&#44;", ",").replace("&#91;", "[").replace("&#93;", ']').replace("&amp;", "&")

def orderStatus():
    return orderSwitch

def currentPlay():
    id = 0
    tmpID = 0
    for v in orderList:
        if (v['played'] == 1):
            tmpID = v['id']
        else:
            id = tmpID
            break
    id = tmpID
    return id

def generateList():
    length = len(orderList)
    res = '🗒歌曲列表（🅿️正在播放）：'
    id = currentPlay()
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

def addOperation(type:str,para:str = '0'):
    temp = dict()
    temp['type'] = type
    temp['para'] = para
    opertaionList.append(temp)

def generatePlay():
    id = currentPlay()
    if (id == 0):
        return '👁‍🗨当前没有在播放歌曲'
    return f"🅿️当前歌曲【{orderList[id-1]['name']} - {orderList[id-1]['author']}】"


async def addToList(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot, name: str, author: str, urls: list):
    # global orderList
    if name in blackList:
        await bot.send(e, f"歌曲《{name}》在黑名单中，无法进行点歌🐵", at_sender=True, reply_message=True)
        return
    if ((0 if orderPeople.get(e.user_id) == None else orderPeople[e.user_id]) >= 2):
        await bot.send(e, f"每时段每人限点2首，你无法继续点歌🫣", at_sender=True, reply_message=True)
        return
    if len(orderList) > maxList:
        await bot.send(e, f"此时段点歌数量已达{maxList}首，无法继续点歌了💦",
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

    orderList.append(tempInfo)

    # if tempInfo['id'] == 1:
    #     operation = dict()
    #     operation['type'] = 'play'
    #     operation['info'] = tempInfo
    #     opertaionList.append(operation)

    path = f"./store/{file_log}"

    logger.debug(path)
    fp = open(path, "w")
    fp.write(json.dumps(orderList))
    fp.close()

    await bot.send(e, f"🥳点歌成功，点歌序号：{len(orderList)}/{maxList}", at_sender=True, reply_message=True)


@scheduler.scheduled_job("cron", id="start", hour="11,17", minute=30)
async def run_start_order():
    global file_log
    global orderSwitch
    if (orderSwitch == 1):
        return
    file_log = time.strftime("%Y_%m_%d_%H", time.localtime()) + ".log"
    orderSwitch = 1
    logger.debug(orderSwitch)
    bot: Bot = get_bot(plugin_config.bot_id)
    await bot.send_group_msg(group_id=plugin_config.notice_id,
                             message="🥰开始点歌啦，大家分享链接到群里就可以咯\r目前支持来自【QQ音乐、网易云音乐】的歌曲哦")


@scheduler.scheduled_job("cron", id="stop", hour="12,18", minute=30)
async def run_stop_order():
    global orderPeople, orderList, opertaionList, file_log, currentID
    global orderSwitch

    orderSwitch = 0
    orderPeople = dict()
    orderList = list()  # 歌曲信息列表
    opertaionList = list()  # 存放传递给前端的操作信息
    file_log = ""  # 序列化存到本地的文件名
    currentID = 0
    bot: Bot = get_bot(plugin_config.bot_id)
    bot.send_group_msg(group_id=plugin_config.notice_id,
                       message="🦭点歌已经结束了哦，大家下次再来吧～")


@app.get("/getLatestID")
def read_id():
    for v in orderList:
        if (v['played'] == 0):
            return {"res": v['id']}
    return {"res": '-1'}


@app.get("/getPlayInfo")
async def play_id(id: int = 1):
    global orderList
    for v in orderList:
        print(v['id'], str(id))
        if (v['id'] == id):
            print("equal")
            v['played'] = 1
            bot = get_bot(plugin_config.bot_id)
            await bot.send_group_msg(group_id=plugin_config.notice_id,
                                     message=f"🅿️正在播放第{id}首歌：{v['name']} - {v['author']}")
            return v
    return {"res": '-1'}


@app.get("/getOperations")
def get_operations():
    res = opertaionList[:]
    opertaionList.clear()
    return res