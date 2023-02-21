import time
from . import config
from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger
from nonebot import get_bot
from nonebot import require
require("nonebot_plugin_apscheduler")


@scheduler.scheduled_job("cron", id="start", hour="2,17", minute=14)
async def run_start_order():
    if (config.getValue('orderSwitch') == 1):
        return
    fileLog = time.strftime("%Y_%m_%d_%H", time.localtime()) + ".log"
    config.setValue('fileLog', fileLog)
    config.setValue('orderSwitch', 1)

    logger.info(f"点歌开启，日志文件：./store/{fileLog}")

    bot: Bot = get_bot(config.bot.bot_id)
    await bot.send_group_msg(group_id=config.bot.notice_id,
                             message="🥰开始点歌啦，大家分享链接到群里就可以咯\r目前支持来自【QQ音乐、网易云音乐】的歌曲哦")


@scheduler.scheduled_job("cron", id="stop", hour="12,18", minute=30)
async def run_stop_order():
    global orderPeople, orderList, opertaionList, file_log, currentID
    global orderSwitch

    config.setValue('orderSwitch', 0)
    config.setValue('fileLog', '')
    config.setValue('currentID', 0)
    config.getValue('orderPeople').clear()
    config.getValue('orderList').clear()
    config.getValue('opertaionList').clear()

    bot: Bot = get_bot(config.bot.bot_id)
    bot.send_group_msg(group_id=config.bot.notice_id,
                       message="🦭点歌已经结束了哦，大家下次再来吧～")
