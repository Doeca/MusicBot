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


# 所有登录状态检查
@on_command("status", permission=SUPERUSER).handle()
async def status_handle(bot: Bot, e: Union[PrivateMessageEvent, GroupMessageEvent]):
    from . import wxlib
    await bot.send(e, message="Collecting Report...")
    hitokoto = await util.httpGet("https://v1.hitokoto.cn/?encode=text")
    music_status = {"qq": "Unknown", "wy": "Unknown", "kg": "Unknown"}
    wx_status = "Unknown"
    try:
        music_status = json.loads(s=(await util.httpGet(f"{config.system.music_api}/status")))
        wx_status = (await wxlib.userInfo())['data']['name']
    except:
        pass

    report_text = f"""📅 Date：{time.strftime('%m/%d/%Y', time.localtime())}

------System Info------
🐧 QQ Music：{music_status['qq']}
⛩️ Netease：{music_status['wy']}
🐩 Kugou Music：{music_status['kg']}
🌠 Wechat Status：{wx_status}

-------Hitokoto------
💮 {hitokoto}
"""

    await bot.send(e, message=report_text)

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
async def login_handle(bot: Bot, e: PrivateMessageEvent):
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
async def login_handle(bot: Bot, e: PrivateMessageEvent):
    await bot.send(e, message="正在处理，请稍后")
    apiUrl = config.system.music_api
    resp = await util.httpGet(f"{apiUrl}/qqgetCookie")
    await bot.send(e, message='已经成功更新QQ Cookie')


# 酷狗音乐登录管理
@on_command("kglogin", permission=SUPERUSER).handle()
async def login_handle(bot: Bot, e: PrivateMessageEvent):
    await bot.send(e, message="正在处理，请稍后")
    apiUrl = config.system.music_api
    resp = await util.httpGet(f"{apiUrl}/kglogin")
    resp = json.loads(s=resp)
    if resp['res'] == -1:
        await bot.send(e, message='发送验证码失败，请稍后再试')
    else:
        await bot.send(e, message="请发送/kgcode code命令")


kgcode_matcher = on_command("kgcode", permission=SUPERUSER)


@kgcode_matcher.handle()
async def cookieUploadPre(bot: Bot, matcher: Matcher, args: Message = CommandArg()):
    code = args.extract_plain_text().strip()
    if code != '':
        matcher.set_arg("arg", code)


@kgcode_matcher.got("arg", prompt="请输入酷狗验证码")
async def cookieUpload(bot: Bot, e: PrivateMessageEvent, arg: str = ArgStr('arg')):
    apiUrl = config.system.music_api
    await util.httpGet(f"{apiUrl}/kgsubmit?code={arg}")
    await kgcode_matcher.finish(f"验证码{arg}已经提交")
