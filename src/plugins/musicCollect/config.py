import os
import json
from nonebot import get_driver
from pydantic import BaseModel, Extra

class Config(BaseModel, extra=Extra.ignore):
    bot_id: str
    notice_id: int

bot = Config.parse_obj(get_driver().config)
valTable = dict()  # 存放一些其他数据
valTable['orderSwitch'] = 0
valTable['maxList'] = 30
valTable['fileLog'] = ''
valTable['currentID'] = 0
valTable['orderList'] = list()  # 歌曲信息列表
valTable['orderPeople'] = dict()  # 存放用户点歌数量
valTable['opertaionList'] = list()  # 存放传递给前端的操作信息


if os.path.exists("./store/blackList.json"):
    fs = open("./store/blackList.json", 'r')
    valTable['blackList'] = json.load(fs)
    fs.close()
else:
    valTable['blackList'] = list()

if not os.path.exists('./store'):
    os.makedirs('./store')


def getValue(key: str):
    return valTable.get(key)


def setValue(key: str, val):
    valTable[key] = val
    return True
