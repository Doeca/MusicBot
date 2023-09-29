import time
import json
import aiohttp

from nonebot import logger, get_driver
from pydantic import BaseModel, Extra
import asyncio
"""
设置初始化流程：
1. 读取学校列表
2. 读取学校设置信息

设置信息如下

1、点歌群号 groups
2、bot在群内的群名片 cardname
3、黑名单歌曲列表 bankeywords

时段信息 timezone【数组】
1、开启时间，关闭时间  settime[4]
2、开启日期 setdate [1,2,3,4,5,6,7]
2、点歌总数量上限  mainlimit
3、个人点歌数量上限 personlimit


info字段

switch_status 点歌开启状态
song_list 歌曲列表
order_users 点歌用户列表
log_file 存放歌单的文件
tzinfo 当前时段的相关数据
vote_num 投票切歌人数
vote_list list 参与投票切歌的qq号
operation_list 针对播放器的操作列表
"""


class Config(BaseModel, extra=Extra.ignore):
    backend_url: str
    setting_domain: str
    music_api: str
    bot_id: str


load_status = 0 # 当前开启状态
schoolList = dict() # id -> 学校名称列表
schoolSettings = dict() # 后端获取的所有原始数据
schoolInfo = dict() #   当前点歌开启状态、歌单等即时信息，不受初始化流程影响。


system = Config.parse_obj(get_driver().config)
lock = asyncio.Lock()

fs = open(f"./random.store", 'r')
random = json.loads(s=fs.read())
fs.close()


async def get_schoolList():
    # async with aiohttp.ClientSession() as session:
    #     async with session.get(f"{system.setting_domain}/get?q=schoolList") as resp:
    #         if (resp.status != 200):
    #             return False
    #         global schoolList
    #         schoolList = await resp.json()
    #         return True
    fs = open("./config/list.json")
    global schoolList
    schoolList = json.loads(fs.read())
    fs.close()
    return True


async def get_schoolSettings():
    # async with aiohttp.ClientSession() as session:
    #     for val in schoolList.keys():
    #         async with session.get(f"{system.setting_domain}/get", params={'q': 'schoolSettings', 'id': val}) as resp:
    #             if (resp.status != 200):
    #                 return False
    #             tmp = await resp.json()
    #             schoolSettings[val] = tmp
    #             return True
    for val in schoolList.keys():
        fs = open(f"./config/{val}.json")
        schoolSettings[val] = json.loads(fs.read())
        fs.close()


async def init_config():
    while await get_schoolList() == False:
        time.sleep(1)
    logger.info("学校列表读取完毕")
    while await get_schoolSettings() == False:
        time.sleep(1)
    logger.info("设置信息读取完毕")
    global load_status
    load_status = 1


"""
通过群号获取学校ID

此逻辑下禁止如下行为：
多个学校ID共用了一个群号，那么就会有问题，所以前端的模板设置里不应该设置真实的群号
"""


async def get_id(gid: str):
    for key in schoolSettings.keys():
        if gid in schoolSettings[key]['groups']:
            return key
    return ''
