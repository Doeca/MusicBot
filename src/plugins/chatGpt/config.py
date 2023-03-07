import os
import json
import random
from nonebot import logger
from revChatGPT.V1 import Chatbot
from nonebot import get_driver
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    bot_id: str


bot = Config.parse_obj(get_driver().config)

cbList = list()

if os.path.exists("./store/gptAct.json"):
    fs = open("./store/gptAct.json", 'r')
    acts = json.load(fs)
    fs.close()
    for v in acts:
        cbList.append(Chatbot(config=v))
        logger.debug(f"[chatGPT] load:{v['email']}")


valTable = dict()  # 存放一些其他数据
if os.path.exists("./store/conversations.json"):
    fs = open("./store/conversations.json", 'r')
    valTable = json.load(fs)
    fs.close()

def getRandomChatBot():
    if (len(cbList) == 0):
        return -1
    min = 0
    max = len(cbList)-1
    return random.randint(min, max)

def getSpecificChatBot(index: int):
    if (index > len(cbList)-1):
        raise '1'
    return cbList[index]

def getValue(key: str):
    return valTable.get(key)

def setValue(key: str, val):
    valTable[key] = val
    fs = open("./store/conversations.json", 'w')
    fs.write(json.dumps(valTable))
    fs.close()
    return True

def delValue(key: str):
    try:
        valTable.pop(key)
        fs = open("./store/conversations.json", 'w')
        fs.write(json.dumps(valTable))
        fs.close()
    except KeyError:
        return False
    else:
        return True
