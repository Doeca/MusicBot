from nonebot import on_request, logger
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, RequestEvent

girq = on_request()


@girq.handle()
async def superUserApprove(bot: Bot, e: RequestEvent):
    logger.info("接收加群邀请")
    try:
        if e.request_type == 'group' and e.sub_type == 'invite':
            await bot.set_group_add_request(flag=e.flag, sub_type=e.sub_type, approve=True, reason="")
            return
    except:
        pass
