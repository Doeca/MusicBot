import time
import random
import os
import json
from . import config
from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger
from nonebot import get_bot
from nonebot import require
require("nonebot_plugin_apscheduler")

cronList = list()


async def run_start_order(school_id, tzinfo: dict):
    info: dict = config.schoolInfo.get(school_id)
    setting: dict = config.schoolSettings[school_id]

    if (info.get("switch_status", 0) == 1):
        return

    set_time = tzinfo['settime']
    date_r = time.strftime(f"%m_%d", time.localtime())
    log_file = f"{date_r}_{set_time[0]}_{set_time[1]}.log"
    config.schoolInfo[school_id]['switch_status'] = 1
    config.schoolInfo[school_id]['log_file'] = log_file
    config.schoolInfo[school_id]['tzinfo'] = tzinfo
    config.schoolInfo[school_id]['setting'] = setting
    """此处判断，如果当前时段的fileLog已经存在，那么从这里读取文件恢复点歌歌单，再进行当前用户的点歌操作"""
    if os.path.exists(f"./store/{log_file}"):
        fs = open(f"./store/{log_file}")
        song_list = json.loads(fs.read())
        config.schoolInfo[school_id]['song_list'] = song_list
        fs.close()
    try:
        botid = config.system.bot_id
        bot: Bot = get_bot(str(botid))
        for gid in setting['groups']:
            await bot.set_group_card(group_id=gid, user_id=botid, card='激情点歌ing 分享链接到群内 即可点歌')
            await bot.send_group_msg(group_id=gid,
                                     message="🥰开始点歌啦，大家分享链接到群里就可以咯\r目前支持来自【QQ音乐、网易云音乐】的歌曲哦")
    except:
        pass

    logger.info(f"{school_id} 点歌开启，日志文件：./store/{log_file}")


async def run_stop_order(school_id):
    info: dict = config.schoolInfo.get(school_id)
    setting: dict = config.schoolSettings[school_id]
    if (info.get("switch_status", 0) == 0):
        return
    config.schoolInfo.pop(school_id)
    try:
        botid = config.system.bot_id
        bot: Bot = get_bot(str(botid))
        for gid in setting['groups']:
            await bot.set_group_card(group_id=gid, user_id=botid, card=setting['cardname'])
            await bot.send_group_msg(group_id=gid, message="🦭点歌已经结束了哦，大家下次再来吧～")
    except:
        pass

"""
当设置被更改后，应该重新进行初始化流程

重新进行初始化流程并不会影响当前正在进行的点歌操作
"""


async def init_cron():

    # 清空正在维护的定时任务
    for id in cronList:
        scheduler.remove_job(id)
    cronList.clear()

    # 为每个学校创建定时任务
    for id in config.schoolList.keys():
        school_config = config.get_config(id)
        for tzinfo in school_config['timezone']:
            set_time = tzinfo['settime']

            # 传递当前时段的设置信息给启动任务
            jobs_id = id + "_" + str(random.randint(10000, 99999))
            scheduler.add_job(run_start_order, "cron",
                              hour=set_time[0], minute=set_time[1], id=f"{jobs_id}",  args=[id, tzinfo])
            cronList.append(jobs_id)

            jobs_id = id + "_" + str(random.randint(10000, 99999))
            scheduler.add_job(run_stop_order, "cron",
                              hour=set_time[2], minute=set_time[3], id=f"{jobs_id}",  args=[id])
            cronList.append(jobs_id)

        logger.info(f"学校：{id} 启动完毕")
