import random
import base64
import json
import nonebot
from . import config
from . import util
from nonebot import get_bot
from nonebot.log import logger
from pydantic import BaseModel
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from nonebot.adapters.onebot.v11 import Bot
from fastapi.middleware.cors import CORSMiddleware


app: FastAPI = nonebot.get_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory="./src/plugins/musicCollect/template")
app.mount(
    "/static", StaticFiles(directory="./src/plugins/musicCollect/static"), name="static")
logger.info("Web接口创建完成")


@app.get("/")
async def ret_page(request: Request, school_id: str):
    if (config.schoolSettings.get(school_id, None) == None):
        return {"res": '-1'}
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "request": request,
            "school_id": school_id
        }
    )


@app.get("/landing.html")
async def ret_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="landing.html",
        context={
            "request": request
        }
    )


@app.get("/config.js")
async def ret_page(request: Request, school_id: str):
    return templates.TemplateResponse(
        request=request,
        name="config.js",
        context={
            "request": request,
            "apiUrl": config.system.backend_url,
            "school_id": school_id
        }
    )


# 获取最新播放的歌曲ID
@app.get("/getLatestID")
async def read_id(school_id: str):
    try:
        # 读取当前学校info，同时替代了开关功能，因为如果这里有数据那么当前肯定处于点歌开启状态
        status = await util.get_switch(school_id)
        info = config.schoolInfo.get(school_id, None)
        if (info == None):
            return {"res": '-1'}
        play_list = info['play_list']
        for v in play_list:
            if (v['played'] == 0):
                return {"res": v['id']}
        if status == False:
            # 说明歌单已经播完了，但是开启了允许继续播完，所以才会走到这个位置，那么不继续播放随机歌曲
            return {"res": '-1'}
        id = random.randint(0, len(config.random)-1)
        return {"res": id + 10000}
    except Exception as e:
        logger.opt(exception=True).error("get latest id wrong")
        return {"res": '-1'}

# 获取歌曲播放数据


@app.get("/getPlayInfo")
async def play_id(school_id: str, id: int = 1):
    try:
        if id < 1:
            return {"res": '-1'}
        await util.get_switch(school_id)
        info: dict = config.schoolInfo.get(school_id, None)
        if (info == None):
            return {"res": '-1'}
        play_list = info.get('play_list', [])
        # 首先找到song_info
        song_info = {}
        if id >= 50000:
            for v in play_list:
                if (v['id'] == id):
                    song_info = v['info']
        elif id >= 10000:
            song_info = config.random[id-10000]
        else:
            song_info = info.get('song_list', [])[id-1]
        if id == info.get('current_song_id', -1):
            # 加载出错，重新加载歌曲，不重新发送播放通知
            return song_info
        
        # logger.info(json.dumps(song_info))
        async with config.lock:
            info['current_song_id'] = id
            info['current_song_title'] = f"{song_info['name']} - {song_info['author']}"
            # logger.info(f"{song_info['name']} - {song_info['author']}")
            config.upsert_info(info['log_id'], json.dumps(info))

        # 如果id在列表里，则标记播放成功，下次获取id就会返回新的id了
        for v in play_list:
            if (v['played'] == 0) and (v['id'] == id):
                async with config.lock:
                    v['played'] = 1
                    config.upsert_info(info['log_id'], json.dumps(info))
        if id >= 50000:
            return song_info  # 预留的tts播报接口，不向群内发送消息

        resp = f"🅿️正在播放{'随机' if id >=10000 else f'第{id}首'}歌曲：{song_info['name']} - {song_info['author']}"
        card = f"当前：{song_info['name']} - {song_info['author']}"
        try:
            setting: dict = config.schoolSettings[school_id]
            for gid in setting['groups']:
                # 若开启静默模式则不发送消息，只修改群名片
                if info["tzinfo"].get("quietmode", 0) == 1:
                    bot: Bot = get_bot()
                    botid = (await bot.call_api("get_login_info"))['user_id']
                    await bot.set_group_card(group_id=gid, user_id=botid, card=card)
                    continue

                bot: Bot = get_bot()
                await bot.send_group_msg(group_id=gid, message=resp)
        except Exception as e:
            logger.error(f"发送消息失败，可能是bot离线了，错误信息：{e}")
            logger.opt(exception=True).error("get playinfo wrong[1]")
            pass
        return song_info
    except Exception as e:
        logger.opt(exception=True).error("get playinfo wrong[2]")
        return {"res": '-1'}


@app.get("/getOperations")
async def get_operations(school_id: str):
    try:
        status = await util.get_switch(school_id)
        info = config.schoolInfo.get(school_id, None)
        if (info == None):
            return {"res": '-1'}
        opertaionList = info['operation_list']
        res = opertaionList[:]
        async with config.lock:
            opertaionList.clear()
            config.upsert_info(info['log_id'], json.dumps(info))
        return res
    except Exception as e:
        logger.opt(exception=True).error("get operations wrong")
        return {"res": []}


# 通知接口，可通过此接口向我发送通知
@app.get("/notify")
async def get_operations(text: str):
    try:
        bot: Bot = get_bot()
        logger.debug(f"notify: {text}")
        await bot.send_private_msg(user_id=1124468334,
                                   message=base64.b64decode(text).decode("utf-8"))
    except Exception as e:
        logger.opt(exception=True).error("notify wrong")
        return {"res": -1}
    return {"res": 0}


@app.get("/heartbeat")
async def _():
    return {"res": 0}


@app.get("/config_reload")
async def _():
    from . import config
    from . import cron
    await config.init_config()
    await cron.init_cron()
    return {"res": 0}
