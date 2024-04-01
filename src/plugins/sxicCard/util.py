import requests
from . import config
from typing import Union
from nonebot.utils import run_sync
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Event

@run_sync
def httpGet(url):
    return requests.get(url)


def unescape(str: str):
    str = str.replace("\\/", "/")
    return str.replace("&#44;", ",").replace("&#91;", "[").replace("&#93;", ']').replace("&amp;", "&")



async def group_checker(e: Union[GroupMessageEvent, PrivateMessageEvent], bot: Bot) -> bool:
    if e.message_type == 'private':
        return True
    return e.group_id in config.system["groups"]
