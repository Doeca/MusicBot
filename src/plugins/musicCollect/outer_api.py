import random
import base64
import json
import nonebot
from . import config
from . import util
from nonebot import get_bot
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from nonebot.adapters.onebot.v11 import Bot
from fastapi.middleware.cors import CORSMiddleware


app: FastAPI = nonebot.get_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 获取最新播放的歌曲ID
@app.get("/getLatestID")
async def read_id(school_id: str):
    # 读取当前学校info，同时替代了开关功能，因为如果这里有数据那么当前肯定处于点歌开启状态
    info = config.schoolInfo.get(school_id, None)
    if (info == None):
        return {"res": '-1'}

    song_list = info['song_list']
    for v in song_list:
        if (v['played'] == 0):
            return {"res": v['id']}
    id = random.randint(0, len(config.random)-1)
    return {"res": id + 10000}

# 获取歌曲播放数据
@app.get("/getPlayInfo")
async def play_id(school_id: int, id: int = 1):
    info = config.schoolInfo.get(school_id, None)
    if (info == None):
        return {"res": '-1'}
    
    # 读取必要设置
    setting: dict = config.schoolSettings[school_id]
    botid = config.system.bot_id

    info['vote_num'] = 0
    info['vote_list'] = list()


    try:
        if id >= 10000:
            v = config.random[id-10000]
            info["current_song_title"] = f"{v['name']} - {v['author']}"
            
            bot: Bot = get_bot(botid)
            for gid in setting['groups']:
                await bot.send_group_msg(group_id=gid, message=f"🅿️正在播放随机歌曲：{v['name']} - {v['author']}")
            return v

        song_list = info['song_list']
        for v in song_list:
            if (v['id'] == id):
                async with config.lock:
                    v['played'] = 1
                    fs = open(f"./store/{info['log_file']}", "w")
                    fs.write(json.dumps(info))
                    fs.close()

                info["current_song_id"] = id
                info["current_song_title"] = f"{v['name']} - {v['author']}"

                bot: Bot = get_bot(str(botid))
                for gid in setting['groups']:
                    await bot.send_group_msg(group_id=gid, message=f"🅿️正在播放第{id}首歌：{v['name']} - {v['author']}")
                return v
    except:
        return {"res": '-1'}
    return {"res": '-1'}


@app.get("/notify")
async def get_operations(text: str):
    botid = config.system.bot_id
    bot: Bot = get_bot(botid)
    await bot.send_private_msg(user_id=1124468334,
                               message=base64.b64decode(text).decode("utf-8"))
    return {"res": 0}