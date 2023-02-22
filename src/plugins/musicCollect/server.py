import nonebot
from . import config
from nonebot import get_bot
from fastapi import FastAPI
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


@app.get("/getLatestID")
def read_id():
    orderList = config.getValue('orderList')
    for v in orderList:
        if (v['played'] == 0):
            return {"res": v['id']}
    return {"res": '-1'}


@app.get("/getPlayInfo")
async def play_id(id: int = 1):
    orderList = config.getValue('orderList')
    for v in orderList:
        if (v['id'] == id):
            v['played'] = 1
            bot = get_bot(config.bot.bot_id)
            await bot.send_group_msg(group_id=config.bot.notice_id,
                                     message=f"🅿️正在播放第{id}首歌：{v['name']} - {v['author']}")
            return v
    return {"res": '-1'}


@app.get("/getOperations")
def get_operations():
    opertaionList = config.getValue('opertaionList')
    res = opertaionList[:]
    opertaionList.clear()
    return res


@app.get("/notifyLogout")
def get_operations():
    bot: Bot = get_bot(config.bot.bot_id)
    bot.send_private_msg(user_id=1124468334, message="网易云登陆已掉线，请重新扫码登陆")
    return {"res": 1}
