import re
import urllib.parse
import requests
from .util import *
from typing import Union
from nonebot import on_command, on_message, on_regex
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import RegexGroup
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, PrivateMessageEvent, GroupMessageEvent


# neteaseMatcher = on_regex("http(s|):\/\/music\.163\.com.*id=([0-9]*)",)

# @neteaseMatcher.handle()
# def func(foo = RegexGroup(),e : PrivateMessageEvent):
#     musicID = foo[1]

#     print(musicID)
anyMatcher = on_message(permission=SUPERUSER)

"""
QQ音乐的匹配，如果没有songmid说明是iOS端来的会员歌曲，如果有就是安卓端发的
没有songmid，通过歌名搜索歌曲，后端判断是否为vip歌曲，返回确保能播放的url
"""


"""
歌曲黑名单设计：
通过歌名进行拉黑，title是歌名 + 作者，但是feat版如何，判断关键词是否存在于之中？这样容易误判，就一个一个拉黑吧
"""


# @anyMatcher.handle()
# def func(e: Event):
#     print("Received: "+e.get_plaintext())
#     a = str(e.get_message())

#     # logger.add(e.get_plaintext(),level="INFO")
#     # print(e.get_message())


qqMatcher = on_regex('\[CQ:json,data={"app":"com\.tencent\.structmsg',)


"""
点歌时间段，11点30分-12:30分，超时后将停止点歌
点歌时间段，17:30分-18:30分，超时后将停止点歌
"""


@qqMatcher.handle()
async def asyncfunc(e: Union[PrivateMessageEvent, GroupMessageEvent], bot: Bot):
    # if (orderSwitch == 0):
    #     await bot.send(e, "当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
    #     return
    msg = e.raw_message
    matchObj = re.search(r'"jumpUrl":"(.*?)"&#44;"p', msg, re.M | re.I)
    detailUrl = matchObj.group(1)
    detailUrl = unescape(detailUrl)
    resp = requests.get(detailUrl)
    matchObj = re.search(r'"mid":"(.*?)"', resp.text, re.M | re.I)
    mid = matchObj.group(1)
    logger.debug(f"MID: {mid}")

    # 访问musicAPI，获取songURL等信息，若获取失败则提示点歌失败
