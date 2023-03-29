import nonebot
from . import config
from nonebot import get_bot
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
app.mount("/static", StaticFiles(directory="./src/plugins/musicCollect/static"), name="static")


@app.get("/")
async def ret_page(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
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
async def ret_page(request: Request):
    return templates.TemplateResponse(
        "config.js",
        {
            "request": request,
            "apiUrl": config.bot.bot_api
        }
    )


@app.get("/getLatestID")
async def read_id():
    orderList = config.getValue('orderList')
    for v in orderList:
        if (v['played'] == 0):
            return {"res": v['id']}
    if len(orderList) == 0:
        return {"res": '-1'}
    id = config.getValue('currentID') + 1
    if id > len(orderList):
        id = 1
    return {"res": id}


@app.get("/getPlayInfo")
async def play_id(id: int = 1):
    orderList = config.getValue('orderList')
    for v in orderList:
        if (v['id'] == id):
            v['played'] = 1
            config.setValue('currentID',id)
            bot = get_bot(config.bot.bot_id)
            for gid in config.bot.notice_id:
                await bot.send_group_msg(group_id=gid,
                                         message=f"🅿️正在播放第{id}首歌：{v['name']} - {v['author']}")
            return v
    return {"res": '-1'}


@app.get("/getOperations")
def get_operations():
    opertaionList = config.getValue('opertaionList')
    res = opertaionList[:]
    opertaionList.clear()
    return res

