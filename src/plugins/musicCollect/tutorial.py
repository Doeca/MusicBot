import json
from . import cron
from . import util
from . import config
from typing import Union
from nonebot import on_command,  on_regex, on_fullmatch
from nonebot.log import logger
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg,  ArgStr
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, Event, GroupMessageEvent, PrivateMessageEvent
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER


async def group_checker(e: Union[GroupMessageEvent, PrivateMessageEvent], bot: Bot) -> bool:
    botid = await util.getID(bot)
    if e.message_type == 'private':
        for i in config.getVal(botid, 'groups'):
            info = await bot.get_group_member_info(group_id=i, user_id=e.user_id, no_cache=True)
            if info["role"] != 'member':
                return True
        return False
    else:
        info = await bot.get_group_member_info(group_id=e.group_id, user_id=e.user_id, no_cache=True)
        if info["role"] != 'member':
            return True
        return False


setMatcher = on_command(
    "setting", aliases={"设置", "初始化"},  rule=group_checker)
playlinkMatcher = on_command(
    "playlink", aliases={"播放地址"}, rule=group_checker)


@setMatcher.handle()
async def func(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher):
    botid = await util.getID(bot)
    await bot.send_private_msg(
        user_id=e.user_id, message=f'请访问以下网址进行bot设置\n{config.system.backend_url}/setting?botid={botid}\n设置完成后发送"/播放地址"获取播放链接')
    if e.message_type == "group":
        await util.sendMsg(bot, e, message="已将相关信息私聊发送给您，请勿将地址发送到群内等公开场合")


@playlinkMatcher.handle()
async def func(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher):
    botid = await util.getID(bot)
    if (config.getSetting(botid) == None):
        await util.sendMsg(bot, e, message=f'您还未进行初始化设置，请发送"/设置"获取链接进行设置，点击"保存"即可完成设置')
        return
    await bot.send_private_msg(
        user_id=e.user_id, message=f'请打开此网页进行歌曲播放\n{config.system.backend_url}/?botid={botid}')
    if e.message_type == "group":
        await util.sendMsg(bot, e, message="已将相关信息私聊发送给您，请勿将地址发送到群内等公开场合")
