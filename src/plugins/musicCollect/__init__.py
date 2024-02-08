from . import config
from . import cron
from . import matcher_netease
from . import matcher_qq
from . import matcher_kg
from . import outer_api
from . import command_user
from . import command_admin
from . import outer_wx
import asyncio

asyncio.run(config.init_config())
asyncio.run(cron.init_cron())
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