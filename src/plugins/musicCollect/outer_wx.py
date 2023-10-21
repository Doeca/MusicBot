import random
import base64
import json
import nonebot
import asyncio
from . import config
from . import util
from . import wxhandle
from . import wxlib
from nonebot.log import logger
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


app: FastAPI = nonebot.get_app()
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/wxpush")
async def create_item(req: Request):
    data = await req.body()
    data = data.decode('utf-8')
    content = json.loads(s=data)
    if content['fromUser'].find("@chatroom") != -1:
        msg: str = content['content']
        user_id = msg[0:msg.find(':')]
        msg = msg.replace(f"{user_id}:\n", "")
        await wxhandle.entrance(content['fromUser'], user_id, msg)
    return {"code": 0, "msg": "success"}


logger.info("Wxhelp接口创建完成")
