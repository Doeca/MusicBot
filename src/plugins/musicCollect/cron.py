import time
import datetime
import random
import os
import json
import asyncio
from . import config
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger
from nonebot import require
require("nonebot_plugin_apscheduler")

cronList = list()
cronLock = asyncio.Lock()


async def run_start_order(school_id, tzinfo: dict):
    # print(f"{school_id} 执行开始任务 {time.strftime('%H:%M', time.localtime())}")
    async with cronLock:
        info: dict = config.schoolInfo.get(school_id, {})
        setting: dict = config.schoolSettings[school_id]

        if (info.get("switch_status", 0) == 1):
            return

        # 判断当前星期数是否在设置日期中
        weekday_number = datetime.date.today().weekday() + 1
        if (weekday_number not in tzinfo['setdate']):
            return

        # 判断当前日期是否为假日或开关情况

        set_time = tzinfo['settime']
        date_r = time.strftime(f"%Y_%m_%d", time.localtime())
        # 缓存ID：日期 月_日_设置时_设置分
        # 即只要开启时间不变便可续读此时段的已点歌信息
        log_id = f"{school_id}_{date_r}_{set_time[0]}_{set_time[1]}"

        """此处判断，如果当前时段的fileLog已经存在，那么从这里读取文件恢复info信息，再进行当前用户的点歌操作"""
        if config.hash_exists(log_id):
            config.schoolInfo[school_id] = json.loads(config.get_info(log_id))
            logger.info("从异常数据丢失中恢复，已加载数据")
            return
        else:
            config.schoolInfo[school_id] = {}
            config.schoolInfo[school_id]['switch_status'] = 1
            config.schoolInfo[school_id]['log_id'] = log_id
            config.schoolInfo[school_id]['tzinfo'] = tzinfo
            config.schoolInfo[school_id]['song_list'] = list()
            config.schoolInfo[school_id]['play_list'] = list()
            config.schoolInfo[school_id]['order_users'] = dict()
            config.schoolInfo[school_id]['vote_num'] = 0
            config.schoolInfo[school_id]['vote_list'] = list()
            config.schoolInfo[school_id]['operation_list'] = list()
            config.schoolInfo[school_id]['current_song_id'] = 0
            config.schoolInfo[school_id]['current_song_title'] = ""
            config.schoolInfo[school_id]['languagerecords'] = {}

        resp = "🥰开始点歌啦，大家分享链接到群里就可以咯\r目前支持来自【QQ音乐、网易云音乐】的歌曲哦"
        for gid in setting['groups']:
            bot: Bot = get_bot()
            botid = (await bot.call_api("get_login_info"))['user_id']
            await bot.set_group_card(group_id=gid, user_id=botid, card='激情点歌ing 分享链接到群内 即可点歌')
            await bot.send_group_msg(group_id=gid,
                                        message=resp)

        logger.info(f"{school_id} 点歌开启，日志ID：{log_id}")


async def run_stop_order(school_id):
    # 这个任务好像没有意义了
    # pass
    # print(f"{school_id} 执行停止任务 {time.strftime('%H:%M', time.localtime())}")
    async with cronLock:
        info: dict = config.schoolInfo.get(school_id, {})
        setting: dict = config.schoolSettings[school_id]
        if (info.get("switch_status", 0) == 0):
            return
        # 如果设置了播放完歌单再结束播放，则不清除info，只是把switch_status改为0就行了
        if setting.get("playfinishclose", 0) == 1:
            info['switch_status'] = 0
            config.upsert_info(info['log_id'], json.dumps(info))
        else:
            config.schoolInfo.pop(school_id)
        try:
            for gid in setting['groups']:
                bot: Bot = get_bot()
                botid = (await bot.call_api("get_login_info"))['user_id']
                await bot.set_group_card(group_id=gid, user_id=botid, card=setting['cardname'])
        except Exception as e:
            logger.opt(exception=True).error("stop cron error")
            pass
        logger.info(f"{school_id} 点歌结束")

"""
当设置被更改后，应该重新进行初始化流程

重新进行初始化流程并不会影响当前正在进行的点歌操作
"""


async def init_cron():

    # 清空正在维护的定时任务
    for job in cronList:
        scheduler.remove_job(job['id'])
    cronList.clear()

    # 为每个学校创建定时任务
    for id in config.schoolList.keys():
        setting = config.schoolSettings[id]
        if setting['switch'] == 0:
            logger.info(f"学校：{id} 总开关未开启，跳过设置定时任务")
            continue
        for tzinfo in setting['timezone']:
            set_time = tzinfo['settime']
            # 传递当前时段的设置信息给启动任务
            # 此架构从设计上来说是可以在相同的时间段内开启多个点歌任务的
            # 但是这样会导致数据的混乱，所以不允许这样做
            # 可以通过设置不同的星期数来实现多个时段的点歌任务

            jobs_id = id + "_" + str(random.randint(10000, 99999))
            scheduler.add_job(run_start_order, "cron",
                              hour=set_time[0], minute=set_time[1], second="*/10", id=f"{jobs_id}",  args=[id, tzinfo])
            cronList.append({'type': 'start', 'id': jobs_id,
                            'arg': f"{set_time[0]}:{set_time[1]}"})
            jobs_id = id + "_" + str(random.randint(10000, 99999))
            scheduler.add_job(run_stop_order, "cron",
                              hour=set_time[2], minute=set_time[3], second="*/10", id=f"{jobs_id}",  args=[id])
            cronList.append({'type': 'stop', 'id': jobs_id,
                            'arg': f"{set_time[2]}:{set_time[3]}"})

        logger.info(f"学校：{id} 定时任务启动完毕")


def get_cron_list():
    for job in scheduler.get_jobs():
        print(job)



