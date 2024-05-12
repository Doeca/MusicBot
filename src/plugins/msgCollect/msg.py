import base64
import json
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg,  ArgStr
from nonebot import on_message
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Message, MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER
from nonebot.rule import is_type

rule = is_type(GroupMessageEvent)

msg_matcher = on_message(rule=rule)
@msg_matcher.handle()
async def _ (bot: Bot,e:GroupMessageEvent):
    msg = e.get_plaintext()
