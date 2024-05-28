import re
from . import util
from . import config
from typing import Union
from nonebot import on_regex, on_message
from nonebot.params import RegexGroup, RegexStr
from typing import Any, Annotated
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent,  Event
from nonebot.log import logger


"""
网易云匹配器
正则链接触发 -> 判断群是否为点歌群(通过rule实现) -> 判断点歌是否开启
-> 获取songid传递给添加到歌单
"""

"""
判断总数量是否达到上限
判断个人点歌数量是否达到上限
判断歌曲名中是否包含黑名单词语

发起api请求，获取点歌数据
->成功，加入歌单，修改上述信息（修改过程需要上锁）
->失败，提示，不进行任何操作
"""

link_1 = on_regex(
    'https:\/\/c6.y.qq.com\/base\/fcgi-bin\/u\?__=([a-zA-Z0-9]{10,15})', block=True, priority=1, rule=util.group_checker)
link_2 = on_regex(
    '"jumpUrl":"(https:\/\/i.y.qq.com\/v8\/playsong.html\?.*?)"&#44;"pre', block=True, priority=2, rule=util.group_checker)


@link_1.handle()
async def _(bot: Bot, e: GroupMessageEvent, link: Annotated[str, RegexStr()]):
    school_id = await config.get_id(str(e.group_id))
    status = await util.get_switch(school_id)
    if status == False:
        await bot.send(e, message="当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    resp = await util.httpGet(link)
    matchObj = re.search(r'"mid":"(.*?)"', resp, re.M | re.I)
    songmid = matchObj.group(1)
    res = await util.addTolist(bot, school_id, songmid, 'qq', str(e.user_id))
    await bot.send(e, message=res['msg'], at_sender=True, reply_message=True)


@link_2.handle()
async def _(bot: Bot, e: GroupMessageEvent, link: Annotated[tuple[Any, ...], RegexGroup()]):
    school_id = await config.get_id(str(e.group_id))
    status = await util.get_switch(school_id)
    if status == False:
        await bot.send(e, message="当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    rawlink = link[0]
    rawlink = util.unescape(rawlink)
    resp = await util.httpGet(rawlink)
    matchObj = re.search(r'"mid":"(.*?)"', resp, re.M | re.I)
    songmid = matchObj.group(1)
    res = await util.addTolist(bot, school_id, songmid, 'qq', str(e.user_id))
    await bot.send(e, message=res['msg'], at_sender=True, reply_message=True)

logger.info("QQ音乐监听器创建完成")
