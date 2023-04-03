import os
import json
from nonebot import logger
botList = list()
botSettings = dict()


def read_setting(id):
    if not os.path.exists(f'./store/{id}'):
        os.makedirs(f'./store{id}')
    if not os.path.exists(f'./settings/{id}'):
        os.makedirs(f'./settings/{id}')

    valTable = dict()  # 存放一些其他数据
    valTable['prioritified'] = 0
    valTable['orderSwitch'] = 0
    valTable['fileLog'] = ''
    valTable['currentID'] = 0
    valTable['orderList'] = list()  # 歌曲信息列表
    valTable['orderPeople'] = dict()  # 存放用户点歌数量
    valTable['opertaionList'] = list()  # 存放传递给前端的操作信息
    valTable['debug'] = 0

    if os.path.exists(f"./settings/{id}/info.json"):
        fs = open(f"./settings/{id}/info.json", 'r')
        info = json.load(fs)
        # 读取平时的名片，最大点歌数量，点歌时间段
        valTable['normal_card'] = info['card']
        valTable['maxList'] = info['max_num']
        valTable['set_time'] = info['set_time']
        fs.close()
    else:
        logger.error("读取不存在的bot数据")
        return

    if os.path.exists(f"./settings/{id}/blackList.json"):
        fs = open(f"./settings/{id}/blackList.json", 'r')
        valTable['blackList'] = json.load(fs)
        fs.close()
    else:
        valTable['blackList'] = list()

    if os.path.exists(f"./settings/{id}/blackKeyList.json"):
        fs = open(f"./settings/{id}/blackKeyList.json", 'r')
        valTable['blackKeyList'] = json.load(fs)
        fs.close()
    else:
        valTable['blackKeyList'] = list()

    botSettings[id] = valTable


if os.path.exists("./settings/act.json"):
    fs = open("./settings/act.json", 'r')
    botList = json.load(fs)
    fs.close()

for id in botList:
    read_setting(id)


def create_bot(id, setting: dict):
    res = 0
    if id not in botList:
        botList.append(id)
        if not os.path.exists(f'./store/{id}'):
            os.makedirs(f'./store{id}')
        if not os.path.exists(f'./settings/{id}'):
            os.makedirs(f'./settings/{id}')
        res += 1
    fs = open(f"./settings/{id}/info.json", 'w')
    fs.write(json.dumps(setting))
    fs.close()
    res += 2
    if(res == 3):
        read_setting(id)
        # 创建定时任务
    return res
        

def getSetting(key: str):
    return botSettings.get(key)


def setSetting(id, val: dict):
    botSettings[id] = val
    return True
