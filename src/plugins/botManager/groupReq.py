from nonebot import on_request
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, GroupRequestEvent

girq = on_request()
@girq.handle()
async def superUserApprove(bot: Bot, e: GroupRequestEvent):
    if e.sub_type == 'invite':
        await e.approve(bot)
