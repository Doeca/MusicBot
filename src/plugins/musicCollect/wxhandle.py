import re
from .config import system
from . import wxlib
from . import util

# 群消息处理


async def wx_handle(gid: str, msg: str):
    pass


async def qq_matcher(content: str):
    reg_str = [
        "<dataurl>.*?songmid=(.*?)&.*?</dataurl>"
    ]
    for rs in reg_str:
        match = re.search(rs, content)
        if match != None:
            return match.group(1)
    return ""


async def wyy_matcher_1(content: str):
    reg_str = [
        "http.*?music\.163\.com.*?&amp;id=([0-9]{1,})",
    ]

# QQ处理器
# 网易云处理器
# 其它命令处理器
# 加好友事件处理 -> testanything ok.still can use
