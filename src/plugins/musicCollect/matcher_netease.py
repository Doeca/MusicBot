import re
from . import util
from . import config
from typing import Union
from nonebot import on_regex, on_message
from nonebot.params import RegexGroup, RegexStr
from typing import Any, Annotated
from nonebot.internal.adapter import Bot
from nonebot.adapters.onebot.v11 import GroupMessageEvent as v11GMsgEvent
from nonebot.adapters.onebot.v12 import GroupMessageEvent as v12GMsgEvent
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
    'http(s|):\/\/163cn\.tv\/[a-zA-Z0-9]{3,7}', priority=1, block=True)
link_2 = on_regex(
    'http(s|).*?music\.163\.com.*?&amp;id=([0-9]{1,})', priority=2, block=True)
link_3 = on_regex(
    '"musicUrl":"https:.*?music.163.com.*?url\?id=([0-9]{2,14})"&#44', priority=3, block=True)
link_4 = on_regex(
    'http.*?music.163.com.*?\?id=([0-9]{3,14})&amp;userid=[0-9]*', priority=4, block=True)
link_5 = on_regex(
    'https:.*y\.music.*m\/song\?id=([0-9]{1,})&', priority=5, block=True)

@link_1.handle()
async def _(bot: Bot, e: Union[v11GMsgEvent, v12GMsgEvent], link: Annotated[str, RegexStr()]):
    school_id = await config.get_id(str(e.group_id))
    status = await util.get_switch(school_id)
    if status == False:
        await util.send(e, message="当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return

    real_link = await util.get_realurl(link)
    matches = re.search('&id=([0-9]{1,})', real_link)
    if (matches == None):
        return
    songid = matches.group(1)
    res = await util.addTolist(school_id, songid, 'wy', str(e.user_id))
    await util.send(e, message=res['msg'], at_sender=True, reply_message=True)


@link_2.handle()
async def _(bot: Bot, e: Union[v11GMsgEvent, v12GMsgEvent], link: Annotated[tuple[Any, ...], RegexGroup()]):
    school_id = await config.get_id(str(e.group_id))
    status = await util.get_switch(school_id)
    if status == False:
        await util.send(e, message="当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    songid = link[1]
    res = await util.addTolist(school_id, songid, 'wy', str(e.user_id))
    await util.send(e, message=res['msg'], at_sender=True, reply_message=True)


@link_3.handle()
async def _(bot: Bot, e: Union[v11GMsgEvent, v12GMsgEvent], link: Annotated[tuple[Any, ...], RegexGroup()]):
    school_id = await config.get_id(str(e.group_id))
    status = await util.get_switch(school_id)
    if status == False:
        await util.send(e, message="当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    songid = link[0]
    res = await util.addTolist(school_id, songid, 'wy', str(e.user_id))
    await util.send(e, message=res['msg'], at_sender=True, reply_message=True)


@link_4.handle()
async def _(bot: Bot, e: Union[v11GMsgEvent, v12GMsgEvent], link: Annotated[tuple[Any, ...], RegexGroup()]):
    school_id = await config.get_id(str(e.group_id))
    status = await util.get_switch(school_id)
    if status == False:
        await util.send(e, message="当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    songid = link[0]
    res = await util.addTolist(school_id, songid, 'wy', str(e.user_id))
    await util.send(e, message=res['msg'], at_sender=True, reply_message=True)

@link_5.handle()
async def _(bot: Bot, e: Union[v11GMsgEvent, v12GMsgEvent], link: Annotated[tuple[Any, ...], RegexGroup()]):
    school_id = await config.get_id(str(e.group_id))
    status = await util.get_switch(school_id)
    if status == False:
        await util.send(e, message="当前不在点歌时间段内，不能点歌哦🥺", at_sender=True, reply_message=True)
        return
    songid = link[0]
    res = await util.addTolist(school_id, songid, 'wy', str(e.user_id))
    await util.send(e, message=res['msg'], at_sender=True, reply_message=True)

logger.info("网易云音乐监听器创建完成")
