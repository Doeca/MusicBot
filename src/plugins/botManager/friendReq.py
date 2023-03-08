from nonebot import on_request
from nonebot.adapters.onebot.v11 import Bot, FriendRequestEvent,FriendAddNoticeEvent

frq = on_request()
fan = on_request()

@frq.handle()
async def approve(bot: Bot, e: FriendRequestEvent):
    await e.approve(bot)


@fan.handle()
async def approve(bot: Bot, e: FriendAddNoticeEvent):
    pass
