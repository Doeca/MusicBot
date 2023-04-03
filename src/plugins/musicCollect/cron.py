import time
import json
from . import config
from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger
from nonebot import get_bot
from nonebot import require
require("nonebot_plugin_apscheduler")


async def run_start_order():
    if (config.getValue('orderSwitch') == 1):
        return
    fileLog = time.strftime("%Y_%m_%d_%H", time.localtime()) + ".log"
    config.setValue('fileLog', fileLog)
    config.setValue('orderSwitch', 1)

    logger.info(f"点歌开启，日志文件：./store/{fileLog}")

    bot: Bot = get_bot(config.bot.bot_id)
    for gid in config.bot.notice_id:
        await bot.set_group_card(group_id=gid, user_id=config.bot.bot_id, card='激情点歌ing 私发/群聊 分享链接 即可点歌')
        await bot.send_group_msg(group_id=gid,
                                 message="🥰开始点歌啦，大家分享链接到群里就可以咯\r目前支持来自【QQ音乐、网易云音乐】的歌曲哦")


async def run_stop_order():
    config.setValue('prioritified', 0)
    config.setValue('orderSwitch', 0)
    config.setValue('fileLog', '')
    config.setValue('currentID', 0)
    config.getValue('orderPeople').clear()
    config.getValue('orderList').clear()
    config.getValue('opertaionList').clear()

    bot: Bot = get_bot(config.bot.bot_id)
    for gid in config.bot.notice_id:
        await bot.set_group_card(group_id=gid, user_id=config.bot.bot_id, card=config.bot.card_common)
        await bot.send_group_msg(group_id=gid, message="🦭点歌已经结束了哦，大家下次再来吧～")


# @scheduler.scheduled_job("cron", id="startAM", hour=config.bot.set_time[0], minute=config.bot.set_time[1])
# async def stMissionAm():
#     await run_start_order()


# @scheduler.scheduled_job("cron", id="startPM", hour=config.bot.set_time[2], minute=config.bot.set_time[3])
# async def stMissionPm():
#     await run_start_order()


# @scheduler.scheduled_job("cron", id="stopAM", hour=config.bot.set_time[4], minute=config.bot.set_time[5])
# async def stopMissionAm():
#     await run_stop_order()


# @scheduler.scheduled_job("cron", id="stopPM", hour=config.bot.set_time[6], minute=config.bot.set_time[7])
# async def stopMissionPm():
#     await run_stop_order()
