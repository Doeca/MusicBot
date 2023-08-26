from . import musicMatcher
from . import command
from . import cron
from . import server
from . import tutorial
from . import config
import asyncio

asyncio.run(config.init_config())

"""
初始化流程：
1. 读取各个学校的设置信息
2. 创建每个时段的定时任务
3. 自动运行
"""

"""
当收到点歌请求时，判断当前是否在这个学校的点歌时间段内，如果在的话就自动开启点歌
点歌时判断歌单文件是否存在，存在的话要读取到本地，这样歌单数据不会丢失
"""