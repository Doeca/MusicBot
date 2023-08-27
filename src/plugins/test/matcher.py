import re
from . import util
from typing import Union
from nonebot import on_regex, on_message
from nonebot.params import RegexGroup, RegexStr
from typing import Any, Annotated

"""
网易云匹配器
正则链接触发 -> 判断群是否为点歌群 -> 判断点歌是否开启
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


link_1 = on_regex('http(s|):\/\/163cn\.tv\/[a-zA-Z0-9]{3,7}')
link_2 = on_regex('http(s|).*?music\.163\.com.*?&amp;id=([0-9]{1,})')


@link_1.handle()
async def _(link: Annotated[str, RegexStr()]):
    real_link = await util.get_realurl(link)
    matches = re.search('&id=([0-9]{1,})', real_link)
    if (matches == None):
        return
    songid = matches.group(1)

    info = util.schoolInfo.get('testid',{})
    print(info)
    info['b'] = songid



@link_2.handle()
async def _(link: Annotated[tuple[Any, ...], RegexGroup()]):
    songid = link[1]
    util.testprint()