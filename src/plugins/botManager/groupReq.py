from . import config
from nonebot import on_request
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, GroupRequestEvent

frq = on_request()
girq = on_request()


@frq.handle()
async def approve(bot: Bot, e: GroupRequestEvent):
    await e.approve(bot)

@girq.handle()
async def superUserApprove(bot: Bot, e: GroupRequestEvent):
    if e.sub_type == 'invite' and SUPERUSER(bot=bot, event=e):
        await e.approve(bot)
