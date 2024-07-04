import time
import datetime
import random
import os
import json
import asyncio
from . import config
from . import wxlib
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
        date_r = time.strftime(f"%m_%d", time.localtime())
        # 缓存文件名：日期 月_日_设置时_设置分.log
        # 即只要开启时间不变便可续读此时段的已点歌信息
        # 还要确保该学校文件夹存在
        os.makedirs(f"./store/{school_id}", exist_ok=True)
        log_file = f"{date_r}_{set_time[0]}_{set_time[1]}.log"

        """此处判断，如果当前时段的fileLog已经存在，那么从这里读取文件恢复info信息，再进行当前用户的点歌操作"""
        if os.path.exists(f"./store/{school_id}/{log_file}"):
            fs = open(f"./store/{school_id}/{log_file}", "r")
            config.schoolInfo[school_id] = json.loads(fs.read())
            fs.close()
            logger.info("从异常数据丢失中恢复，已加载数据")
            return
        else:
            config.schoolInfo[school_id] = {}
            config.schoolInfo[school_id]['switch_status'] = 1
            config.schoolInfo[school_id]['log_file'] = log_file
            config.schoolInfo[school_id]['tzinfo'] = tzinfo
            config.schoolInfo[school_id]['song_list'] = list()
            config.schoolInfo[school_id]['order_users'] = dict()
            config.schoolInfo[school_id]['vote_num'] = 0
            config.schoolInfo[school_id]['vote_list'] = list()
            config.schoolInfo[school_id]['operation_list'] = list()
            config.schoolInfo[school_id]['current_song_id'] = 0
            config.schoolInfo[school_id]['current_song_title'] = ""

        resp = "🥰开始点歌啦，大家分享链接到群里就可以咯\r目前支持来自【QQ音乐、网易云音乐、酷狗音乐】的歌曲哦"
        for gid in setting['groups']:
            if gid.find("@chatroom") != -1:
                await wxlib.changeCard(gid, "激情点歌ing")
                await wxlib.sendMsg(gid, resp)
            else:
                bot: Bot = get_bot()
                botid = (await bot.call_api("get_login_info"))['user_id']
                await bot.set_group_card(group_id=gid, user_id=botid, card='激情点歌ing 分享链接到群内 即可点歌')
                await bot.send_group_msg(group_id=gid,
                                         message=resp)

        logger.info(f"{school_id} 点歌开启，日志文件：./store/{school_id}/{log_file}")


async def run_stop_order(school_id):
    # print(f"{school_id} 执行停止任务 {time.strftime('%H:%M', time.localtime())}")
    async with cronLock:
        info: dict = config.schoolInfo.get(school_id, {})
        setting: dict = config.schoolSettings[school_id]
        if (info.get("switch_status", 0) == 0):
            # print("已经停止，提前返回")
            return
        config.schoolInfo.pop(school_id)
        try:
            resp = "🦭点歌已经结束了哦，大家下次再来吧～"
            for gid in setting['groups']:
                if gid.find("@chatroom") != -1:
                    await wxlib.changeCard(gid, "激情点歌ing")
                    await wxlib.sendMsg(gid, resp)
                else:
                    bot: Bot = get_bot()
                    botid = (await bot.call_api("get_login_info"))['user_id']
                    await bot.set_group_card(group_id=gid, user_id=botid, card=setting['cardname'])
                    await bot.send_group_msg(group_id=gid, message=resp)
        except Exception as e:
            print(e)
            pass

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


@scheduler.scheduled_job('cron', hour="10", minute='30')
async def status_report():
    # 向点歌测试群汇报本日点歌系统状态
    from . import util
    await bot.send_group_msg(group_id=762907200, message="Collecting Report...")
    bot: Bot = get_bot()
    hitokoto = await util.httpGet("https://v1.hitokoto.cn/?encode=text")
    music_status = {"qq": "Unknown", "wy": "Unknown", "kg": "Unknown"}
    wx_status = "Unknown"
    try:
        music_status = json.loads(s=(await util.httpGet(f"{config.system.music_api}/status")))
        wx_status = (await wxlib.userInfo())['data']['name']
    except:
        pass

    report_text = f"""📅 Date：{time.strftime('%m/%d/%Y', time.localtime())}

------System Info------
🐧 QQ Music：{music_status['qq']}
⛩️ Netease：{music_status['wy']}
🐩 Kugou Music：{music_status['kg']}
🌠 Wechat Status：{wx_status}

-------Hitokoto------
💮 {hitokoto}
"""
    
    await bot.send_group_msg(group_id=762907200, message=report_text)

