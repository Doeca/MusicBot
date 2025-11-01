import base64
import time
from . import util
from . import config
import json
from typing import Union
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg,  ArgStr
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Message, MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER

# 网易云登录管理

@on_command("wylogin", permission=SUPERUSER).handle()
async def login_handle(bot: Bot, e: PrivateMessageEvent):
    await bot.send(e, message="正在处理，请稍后")
    apiUrl = config.system.music_api
    resp = await util.httpGet(f"{apiUrl}/wylogin")
    resp = json.loads(s=resp)
    if resp['res'] == -1:
        await bot.send(e, message=resp['msg'])
    else:
        await bot.send(e, message="请及时登录,然后发送/wyok命令")
        await bot.send(e, message=Message(MessageSegment.image(f"base64://{resp['msg']}")))


@on_command("wyok", permission=SUPERUSER).handle()
async def login_handle(bot: Bot, e: PrivateMessageEvent):
    await bot.send(e, message="正在处理，请稍后")
    apiUrl = config.system.music_api
    resp = await util.httpGet(f"{apiUrl}/wygetCookie")
    resp = json.loads(s=resp)
    if resp['res'] == -1:
        await bot.send(e, message=f"获取失败，原因：{resp['msg']}")
    else:
        await bot.send(e, message='已经成功更新网易云 Cookie')


# QQ音乐登录管理
@on_command("qqlogin", permission=SUPERUSER).handle()
async def login_handle(bot: Bot, e: Union[PrivateMessageEvent, GroupMessageEvent]):
    await bot.send(e, message="正在处理，请稍后")
    apiUrl = config.system.music_api
    resp = await util.httpGet(f"{apiUrl}/qqlogin")
    resp = json.loads(s=resp)
    if resp['res'] == -1:
        await bot.send(e, message=resp['msg'])
    else:
        await bot.send(e, message="请及时登录,然后发送/qqok命令")
        await bot.send(e, message=Message(MessageSegment.image(f"base64://{resp['msg']}")))


@on_command("qqok", permission=SUPERUSER).handle()
async def login_handle(bot: Bot, e: Union[PrivateMessageEvent, GroupMessageEvent]):
    await bot.send(e, message="正在处理，请稍后")
    apiUrl = config.system.music_api
    resp = await util.httpGet(f"{apiUrl}/qqgetCookie")
    await bot.send(e, message='已经成功更新QQ Cookie')

