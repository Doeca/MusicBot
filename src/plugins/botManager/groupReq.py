from nonebot import on_request, logger
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, RequestEvent, GroupRequestEvent

girq = on_request()


@girq.handle()
async def superUserApprove(bot: Bot, e: RequestEvent):
    
    print("is group event:", isinstance(e, GroupRequestEvent))
    logger.info(f"e.request_name: {e.get_event_name()}")
    logger.info(f"e.event_description: {e.get_event_description()}")
    logger.info(f"e.event_description type: {type(e.get_event_description())}")
    try:
        if e.request_type == 'group' and e.sub_type == 'invite':
            logger.info("bot收到加群邀请")
            await bot.set_group_add_request(flag=e.flag, sub_type=e.sub_type, approve=True, reason="")
            return
    except:
        pass
