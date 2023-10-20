import random
import base64
import json
import nonebot
import asyncio
from . import config
from . import util
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


async def init_wx():
    # 微信初始化hook
    res = await wxlib.hookSyncMsg()
    for i in range(0, 5):
        if res == True:
            logger.info("[Wxhelper] hook请求成功")
            return
        else:
            res = await wxlib.hookSyncMsg()
            await asyncio.sleep(1)
    logger.error("[Wxhelper] hook请求失败")


@app.on_event("shutdown")
async def wx_close():
    res = await wxlib.unhookSyncMsg()
    for i in range(0, 5):
        if res == True:
            logger.info("[Wxhelper] unhook请求成功")
            return
        else:
            res = await wxlib.unhookSyncMsg()
            await asyncio.sleep(1)
    logger.error("[Wxhelper] unhook请求失败")


@app.post("/wxpush")
async def create_item(req: Request):
    data = await req.body()
    content = data.decode('utf-8')
    logger.info(f"收到push请求:{content}")


    return {"code": 0, "msg": "success"}


logger.info("Wxhelp接口创建完成")
