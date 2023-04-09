import random
import base64
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


class Setting(BaseModel):
    id: int
    groups: list
    card: str
    maxList: int
    set_time: list
    vote_need: int = 6
    maxPer: int = 2


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


@app.get("/")
async def ret_page(request: Request, botid: int):
    if (config.getSetting(botid) == None):
        return {"res": '-1'}
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "botid": botid
        }
    )


@app.get("/setting")
async def ret_page(request: Request, botid: int):
    return templates.TemplateResponse(
        "set.html",
        {
            "request": request,
            "botid": botid,
            "apiUrl": config.system.backend_url
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
async def ret_page(request: Request, botid: int):
    return templates.TemplateResponse(
        "config.js",
        {
            "request": request,
            "apiUrl": config.system.backend_url,
            "botid": botid
        }
    )


@app.get("/getLatestID")
async def read_id(botid: int):
    if (config.getSetting(botid) == None):
        return {"res": '-1'}
    status = await util.isRunning(botid)
    if (status == False):
        return {"res": '-1'}
    orderList = config.getVal(botid, 'orderList')
    for v in orderList:
        if (v['played'] == 0):
            return {"res": v['id']}
    id = random.randint(0, len(config.random)-1)
    return {"res": id + 10000}


@app.get("/getPlayInfo")
async def play_id(botid: int, id: int = 1):
    if (config.getSetting(botid) == None):
        return {"res": '-1'}
    status = await util.isRunning(botid)
    if (status == False):
        return {"res": '-1'}
    config.setVal(botid, "voteNum", 0)
    config.setVal(botid, "votePeople", list())

    if id >= 10000:
        v = config.random[id-10000]
        config.setVal(botid, "currentTitle",
                      f"{v['name']} - {v['author']}")
        bot: Bot = get_bot(str(botid))
        for gid in config.getVal(botid, "groups"):
            await bot.send_group_msg(group_id=gid,
                                     message=f"🅿️正在播放随机歌曲：{v['name']} - {v['author']}")
        return v

    orderList = config.getVal(botid, 'orderList')
    for v in orderList:
        if (v['id'] == id):
            v['played'] = 1
            config.setVal(botid, 'currentID', id)
            config.setVal(botid, "currentTitle",
                          f"{v['name']} - {v['author']}")
            bot: Bot = get_bot(str(botid))
            for gid in config.getVal(botid, "groups"):
                await bot.send_group_msg(group_id=gid,
                                         message=f"🅿️正在播放第{id}首歌：{v['name']} - {v['author']}")
            return v
    return {"res": '-1'}


@app.get("/getOperations")
def get_operations(botid: int):
    if (config.getSetting(botid) == None):
        return {"res": '-1'}
    opertaionList = config.getVal(botid, 'opertaionList')
    res = opertaionList[:]
    opertaionList.clear()
    return res


@app.post("/changeSettings")
async def change_settings(setting: Setting):
    config.create_bot(setting.id, {'groups': setting.groups, 'card': setting.card,
                                   'maxList': setting.maxList, 'set_time': setting.set_time, 'vote_need': setting.vote_need, 'maxPer': setting.maxPer})
    return "保存设置成功"


@app.get("/getSettings")
async def play_id(botid: int):
    if botid == 0:
        return {"res": -1}
    return {'res': "0", 'id': botid, 'groups': config.getVal(botid, "groups", [123, 456]), 'card': config.getVal(botid, 'card', '快乐食间点歌bot'), 'maxList': config.getVal(botid, "maxList", 30), 'set_time': config.getVal(botid, "set_time", [11, 30, 17, 30, 13, 30, 19, 0]), 'vote_need': config.getVal(botid, "vote_need", 6), 'maxPer': config.getVal(botid, "maxPer", 2)}


@app.get("/notify")
async def get_operations(text: str):
    bot: Bot = get_bot(config.system.bot_id)
    await bot.send_private_msg(user_id=1124468334,
                               message=base64.b64decode(text).decode("utf-8"))
    return {"res": 0}
