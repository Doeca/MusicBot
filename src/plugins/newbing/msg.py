
import re
import requests
import base64
from . import config
from typing import Union
from nonebot import on_message, on_command
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.matcher import Matcher 
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent



resetMatcher = on_command('reset', priority=1)
msgMatcher = on_message(rule=to_me(), priority=5)

@resetMatcher.handle()
async def reset(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher):
    matcher.stop_propagation()
    res = requests.get(f"{config.bot.bing_api}/reset/{e.user_id}")
    rtx_msg = ""
    if (res.status_code == 200):
        rtx_msg = res.json()['msg']
    else:
        rtx_msg = '【调用时出现错误，请稍后重试】'
    await bot.send(event=e, message=rtx_msg, reply_message=True)


@msgMatcher.handle()
async def func(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent]):
    msg = str(e.get_message())
    print('raw msg:', msg)
    match = re.search(r'\[CQ.*file=([^,]*).*\]', msg, re.I | re.M)
    while (match != None):
        tt = await bot.get_image(file=match.group(1))
        msg = msg.replace(match.group(), "图片链接:"+tt['url'])
        match = re.search(r'\[CQ.*file=([^,]*).*\]', msg, re.I | re.M)
    print('str msg:', msg)
    text = base64.b64encode(msg.encode())
    res = requests.post(f"{config.bot.bing_api}/chat/{e.user_id}",
                        data=text, headers={'content-type': 'text/plain'})
    rtx_msg = ""
    if (res.status_code == 200):
        rtx_msg = res.json()['msg']
    else:
        rtx_msg = '【调用时出现错误，请稍后重试】'
    await bot.send(event=e, message=rtx_msg, reply_message=True)
