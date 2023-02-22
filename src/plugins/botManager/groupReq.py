from . import config
from nonebot import on_request
from nonebot.adapters.onebot.v11 import Bot, GroupRequestEvent

frq = on_request()


@frq.handle()
async def approve(bot: Bot, e: GroupRequestEvent):
    if e.sub_type == 'add' and e.group_id == config.bot.notice_id:
        await e.approve(bot)
