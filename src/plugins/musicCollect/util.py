import time
import json
import os
import nonebot
from .config import Config
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, GroupMessageEvent, Event
from nonebot_plugin_apscheduler import scheduler
from typing import Union
from nonebot.log import logger
from nonebot import get_bot, get_driver
from nonebot import require
from fastapi import FastAPI
app: FastAPI = nonebot.get_app()

require("nonebot_plugin_apscheduler")
plugin_config = Config.parse_obj(get_driver().config)
logger.debug(plugin_config.bot_id)
logger.debug(str(plugin_config.notice_id))

if os.path.exists("./blackList.json"):
    fs = open("./blackList.json", 'r')
    blackList = json.load(fs)
    fs.close()
else:
    blackList = dict()

orderSwitch = 0  # 点歌开关
orderPeople = dict()  # 存放用户点歌数量
orderList = list()  # 歌曲信息列表
opertaionList = list()  # 存放传递给前端的操作信息
file_log = ""  # 序列化存到本地的文件名
currentID = 0
maxList = 30


def unescape(str: str):
    return str.replace("&#44;", ",").replace("&#91;", "[").replace("&#93;", ']').replace("&amp;", "&")


def addToList(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot, name: str, author: str, urls: list):
    if blackList[name] == 1:
        bot.send(e, f"歌曲{name}在黑名单中，无法进行点歌🐵", True, True)
        return
    if orderPeople[e.user_id] > 2:
        bot.send(e, f"每时段每人限点2首，你无法继续点歌🫣", at_sender=True, reply_message=True)
        return
    if len(orderList) > maxList:
        bot.send(e, f"此时段点歌数量已达{maxList}首，无法继续点歌了💦",
                 at_sender=True, reply_message=True)
        return

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

    if tempInfo['id'] == 1:
        operation = dict()
        operation['type'] = 'play'
        operation['info'] = tempInfo
        opertaionList.append(operation)

    fp = open(f"./store/{file_log}", "w")
    fp.write(json.dumps(orderList))
    fp.close()

    bot.send(e, f"点歌成功，点歌序号：{len(orderList)}❤️", True, True)


@scheduler.scheduled_job("cron", id="start", hour="11,17", minute=30)
async def run_start_order():
    logger.debug(str())
    global file_log, orderSwitch
    file_log = time.strftime("%Y_%m_%d_%H", time.localtime()) + ".log"
    orderSwitch = 1
    bot: Bot = get_bot(plugin_config.bot_id)
    bot.send_group_msg(group_id=plugin_config.notice_id,
                       message="开始点歌啦，大家分享链接到群里就可以咯\r目前支持来自【QQ音乐、网易云音乐】的歌曲哦")


@scheduler.scheduled_job("cron", id="stop", hour="12,18", minute=30)
async def run_stop_order():
    global orderSwitch, orderPeople, orderList, opertaionList, file_log, currentID
    orderSwitch = 0
    orderPeople = dict()
    orderList = list()  # 歌曲信息列表
    opertaionList = list()  # 存放传递给前端的操作信息
    file_log = ""  # 序列化存到本地的文件名
    currentID = 0
    bot: Bot = get_bot(plugin_config.bot_id)
    bot.send_group_msg(group_id=plugin_config.notice_id,
                       message="点歌已经结束了哦，大家下次再来吧～")


@app.get("/getLatestID")
def read_operations():
    for v in orderList:
        if (v['played'] == 0):
            return {"res": v['id']}
    return {"res": '-1'}


@app.get("/getPlayInfo")
def play_id(id: int = 1):
    for v in orderList:
        if (v['id'] == str(id)):
            v['played'] = 1
            # 发送正在播放的消息
            return v
    return {"res": '-1'}
