from typing import Union
from nonebot import on_regex
from nonebot.internal.adapter import Bot
from nonebot.adapters.onebot.v11 import PrivateMessageEvent as v11PMsgEvent
from nonebot.adapters.onebot.v12 import PrivateMessageEvent as v12PMsgEvent
from nonebot.log import logger



test = on_regex(".*", priority=10)
@test.handle()
async def _(bot: Bot, e: Union[v11PMsgEvent, v12PMsgEvent]):
    msg = e.message.extract_plain_text()
    logger.info(f"可能需要的内容：\n{msg}\n")


logger.info("测试监听器创建完成")
