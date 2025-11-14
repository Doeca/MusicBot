import time
import json
import aiohttp
import hashlib
import sqlite3

from nonebot import logger, get_driver
from pydantic import BaseModel, Extra
from nonebot import get_plugin_config
import asyncio


"""
设置初始化流程：
1. 读取学校列表
2. 读取学校设置信息

设置信息如下

1、点歌群号 groups
2、bot在群内的群名片 cardname
3、黑名单歌曲列表 bankeywords
4、播放完歌单再结束播放 playfinishclose

时段信息 timezone【数组】
1、开启时间，关闭时间  settime[4]
2、开启日期 setdate [1,2,3,4,5,6,7]
2、点歌总数量上限  mainlimit
3、个人点歌数量上限 personlimit
4、投票切割所需票数 voteneed
5、静默模式 quietmode
6、语种比例设置 languageset


info字段（相当于cache字段，每次点歌都会刷新）


switch_status 点歌开启状态
song_list 歌曲列表
play_list 实际播放顺序
order_users 点歌用户列表
log_id 数据库中存放的ID
tzinfo 当前时段的相关数据
vote_num 投票切歌人数
vote_list list 参与投票切歌的qq号
operation_list 针对播放器的操作列表
current_song_id 当前播放的歌单中的歌曲id
current_song_title 当前播放的歌曲名
"""

class Config(BaseModel, extra=Extra.ignore):
    backend_url: str
    setting_domain: str
    music_api: str


load_status = 0  # 当前开启状态
schoolList = dict()  # id -> 学校名称列表
schoolSettings = dict()  # 后端获取的所有原始数据
schoolInfo = dict()  # 当前点歌开启状态、歌单等即时信息，不受初始化流程影响。
globalConfig = dict()  # 全局配置
lock = asyncio.Lock()

# 这里也要修改为从后台读取吧
fs = open(f"./config/music/random.store", 'r')
random = json.loads(s=fs.read())
fs.close()


system = get_plugin_config(Config)




"""
通过群号获取学校ID

此逻辑下禁止如下行为：
多个学校ID共用了一个群号，那么就会有问题，所以前端的模板设置里不应该设置真实的群号
"""


async def get_id(gid: str):
    if gid == "":
        return ''
    for key in schoolSettings.keys():
        if gid in schoolSettings[key]['groups']:
            return key
    return ''

def init_db():
    conn = sqlite3.connect('music_cache.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS song_history (
            hash TEXT PRIMARY KEY,
            info TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()


# 2. 判断某hash值是否存在
def hash_exists(hash_value: str) -> bool:
    conn = sqlite3.connect('music_cache.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM song_history WHERE hash = ? LIMIT 1", (hash_value,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists

# 3. 将info写到hash上（如果存在则更新，否则插入）


def upsert_info(hash_value: str, info_value: str):
    conn = sqlite3.connect('music_cache.db')
    cursor = conn.cursor()
    sql = """
        INSERT INTO song_history (hash, info)
        VALUES (?, ?)
        ON CONFLICT(hash) DO UPDATE SET info=excluded.info
    """
    cursor.execute(sql, (hash_value, info_value))
    conn.commit()
    cursor.close()
    conn.close()

# 4. 根据hash读取info


def get_info(hash_value: str):
    conn = sqlite3.connect('music_cache.db')
    cursor = conn.cursor()
    cursor.execute(
        "SELECT info FROM song_history WHERE hash = ? LIMIT 1", (hash_value,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result[0] if result else None



async def init_config():
    global system, schoolSettings, schoolList, schoolInfo, globalConfig
    system = get_plugin_config(Config)
    rawConfig = dict()
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{system.setting_domain}/config/get") as resp:
            if (resp.status != 200):
                return False
            rawConfig = await resp.json()
            rawConfig = rawConfig['data']
            global schoolList
            schoolList = rawConfig['list']
            schoolInfo.clear()  # 清空残留数据
    for val in schoolList.keys():
        schoolSettings[val] = rawConfig['settings'][val]
    globalConfig = rawConfig['global']
    logger.info("设置信息读取完毕")
    global load_status
    load_status = 1

    init_db()