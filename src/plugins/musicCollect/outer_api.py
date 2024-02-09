import random
import base64
import json
import nonebot
from . import config
from . import util
from . import wxlib
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
    allow_origins=['*'],
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
        "index.html",
        {
            "request": request,
            "school_id": school_id
        }
    )


@app.get("/landing.html")
async def ret_page(request: Request):
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request
        }
    )


@app.get("/config.js")
async def ret_page(request: Request, school_id: str):
    return templates.TemplateResponse(
        "config.js",
        {
            "request": request,
            "apiUrl": config.system.backend_url,
            "school_id": school_id
        }
    )


# 获取最新播放的歌曲ID
@app.get("/getLatestID")
async def read_id(school_id: str):
    # 读取当前学校info，同时替代了开关功能，因为如果这里有数据那么当前肯定处于点歌开启状态
    status = await util.get_switch(school_id)
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
async def play_id(school_id: str, id: int = 1):
    # 2024 1月5日记录：这个版本的设计下，如果bot端离线则不能正常播放歌曲，需要调整
    status = await util.get_switch(school_id)
    info = config.schoolInfo.get(school_id, None)
    if (info == None):
        return {"res": '-1'}

    # 读取必要设置
    setting: dict = config.schoolSettings[school_id]

    info['vote_num'] = 0
    info['vote_list'] = list()

    if id >= 10000:
        v = config.random[id-10000]
        info["current_song_id"] = id
        info["current_song_title"] = f"{v['name']} - {v['author']}"

        resp = f"🅿️正在播放随机歌曲：{v['name']} - {v['author']}"
        card = f"当前：{v['name']} - {v['author']}"
        try:
            for gid in setting['groups']:
                # 若开启静默模式则不发送消息，只修改群名片
                if info["tzinfo"].get("quietmode", 0) == 1:
                    if gid.find("@chatroom") != -1:
                        await wxlib.changeCard(gid, card)
                    else:
                        bot: Bot = get_bot()
                        botid = (await bot.call_api("get_login_info"))['user_id']
                        await bot.set_group_card(group_id=gid, user_id=botid, card=card)
                    continue
                if gid.find("@chatroom") != -1:
                    await wxlib.sendMsg(gid, resp)
                else:
                    bot: Bot = get_bot()
                    await bot.send_group_msg(group_id=gid, message=resp)
        except Exception as e:
            logger.error(f"发送消息失败，可能是bot离线了，错误信息：{e}")
            pass
        return v

    song_list = info['song_list']
    for v in song_list:
        if (v['id'] == id):
            async with config.lock:
                v['played'] = 1
                info["current_song_id"] = id
                info["current_song_title"] = f"{v['name']} - {v['author']}"
                fs = open(f"./store/{school_id}/{info['log_file']}", "w")
                fs.write(json.dumps(info))
                fs.close()

            resp = f"🅿️正在播放第{id}首歌：{v['name']} - {v['author']}"
            card = f"当前：{v['name']} - {v['author']}"
            try:
                for gid in setting['groups']:
                    # 若开启静默模式则不发送消息，只修改群名片
                    if info["tzinfo"].get("quietmode", 0) == 1:
                        if gid.find("@chatroom") != -1:
                            await wxlib.changeCard(gid, card)
                        else:
                            bot: Bot = get_bot()
                            await bot.set_group_card(group_id=gid, user_id=botid, card=card)
                        continue

                    if gid.find("@chatroom") != -1:
                        await wxlib.sendMsg(gid, resp)
                    else:
                        bot: Bot = get_bot()
                        await bot.send_group_msg(group_id=gid, message=resp)
            except Exception as e:
                logger.error(f"发送消息失败，可能是bot离线了，错误信息：{e}")
                pass
            return v
    return {"res": '-1'}


@app.get("/getOperations")
async def get_operations(school_id: str):
    async with config.lock:
        status = await util.get_switch(school_id)
        info = config.schoolInfo.get(school_id, None)
        if (info == None):
            return {"res": '-1'}

        opertaionList = info['operation_list']
        res = opertaionList[:]
        opertaionList.clear()
        fs = open(f"./store/{school_id}/{info['log_file']}", "w")
        fs.write(json.dumps(info))
        fs.close()
        return res


# 通知接口，可通过此接口向我发送通知
@app.get("/notify")
async def get_operations(text: str):
    bot: Bot = get_bot()
    await bot.send_private_msg(user_id=1124468334,
                               message=base64.b64decode(text).decode("utf-8"))
    return {"res": 0}


# 测试接口，通过此接口测试nonebot行为
@app.get("/action_test")
async def _():
    # botids: list = [1687708097, 1563790049, 2119302278]
    # for botid in botids:
    #     try:
    #         bot: Bot = get_bot(str(botid))
    #         if bot != None:
    #             return bot
    #     except:
    #         pass
    bot: Bot = nonebot.get_bot()
    res = await bot.call_api("get_stranger_info", user_id=1124468334)
    print(f"res:{res}")
    return {"res": 0}
