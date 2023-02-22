from nonebot import on_request
from nonebot.adapters.onebot.v11 import Bot, FriendRequestEvent

frq = on_request()


@frq.handle()
async def approve(bot: Bot, e: FriendRequestEvent):
    await e.approve(bot)
