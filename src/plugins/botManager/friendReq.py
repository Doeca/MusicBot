from nonebot import on_request
from nonebot.internal.adapter import Bot
from nonebot.adapters.onebot.v11 import FriendRequestEvent
from nonebot.adapters.onebot.v12 import Event as V12Event

frq = on_request()


@frq.handle()
async def approve(bot: Bot, e: FriendRequestEvent):
    await e.approve(bot)

frq_wx = on_request()
@frq_wx.handle()
async def approve(bot: Bot, e: V12Event):
    # 判断是否为拓展动作wx.friend_request
    if e.detail_type == "wx.friend_request":
        await bot.call_api("wx.accept_friend", v3=e.v3, v4=e.v4)
