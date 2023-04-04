import time
import json
from . import config
from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger
from nonebot import get_bot
from nonebot import require
require("nonebot_plugin_apscheduler")

cronList = dict()


async def run_start_order(id):
    if (config.getVal(id,'orderSwitch') == 1):
        return
    fileLog = time.strftime("%Y_%m_%d_%H", time.localtime()) + ".log"
    config.setVal(id, 'fileLog', fileLog)
    config.setVal(id, 'orderSwitch', 1)

    logger.info(f"点歌开启，日志文件：./store/{fileLog}")

    bot: Bot = get_bot(str(id))
    for gid in config.getVal(id,"groups"):
        await bot.set_group_card(group_id=gid, user_id=id, card='激情点歌ing 私发/群聊 分享链接 即可点歌')
        await bot.send_group_msg(group_id=gid,
                                 message="🥰开始点歌啦，大家分享链接到群里就可以咯\r目前支持来自【QQ音乐、网易云音乐】的歌曲哦")


async def run_stop_order(id):
    config.setVal(id, 'prioritified', 0)
    config.setVal(id, 'orderSwitch', 0)
    config.setVal(id, 'fileLog', '')
    config.setVal(id, 'currentID', 0)
    config.getVal(id, 'orderPeople').clear()
    config.getVal(id, 'orderList').clear()
    config.getVal(id, 'opertaionList').clear()

    bot: Bot = get_bot(str(id))

    for gid in config.getVal(id, "groups"):
        await bot.set_group_card(group_id=gid, user_id=id, card=config.getVal(id, "card"))
        await bot.send_group_msg(group_id=gid, message="🦭点歌已经结束了哦，大家下次再来吧～")


def initialize_cron():
    for id in config.botList:
        set_time = config.getVal(id, "set_time")
        if cronList.get(f"{id}AMSTART") != f"{set_time[0]}:{set_time[1]}":
            if cronList.get(f"{id}AMSTART") !=  None:
                scheduler.remove_job(f"{id}AMSTART")
            scheduler.add_job(run_start_order, "cron",
                              hour=set_time[0], minute=set_time[1], id=f"{id}AMSTART",  args=[id])
            cronList[f"{id}AMSTART"] = f"{set_time[0]}:{set_time[1]}"
            logger.info(f"启动：bot({id}) AMSTART")

        if cronList.get(f"{id}PMSTART") != f"{set_time[2]}:{set_time[3]}":
            if cronList.get(f"{id}PMSTART") !=  None:
                scheduler.remove_job(f"{id}PMSTART")
            scheduler.add_job(run_start_order, "cron",
                              hour=set_time[2], minute=set_time[3], id=f"{id}PMSTART", args=[id])
            cronList[f"{id}PMSTART"] = f"{set_time[2]}:{set_time[3]}"
            logger.info(f"启动：bot({id}) PMSTART")

        if cronList.get(f"{id}AMSTOP") != f"{set_time[4]}:{set_time[5]}":
            if cronList.get(f"{id}AMSTOP") !=  None:
                scheduler.remove_job(f"{id}AMSTOP")
            scheduler.add_job(run_stop_order, "cron",
                              hour=set_time[4], minute=set_time[5], id=f"{id}AMSTOP",  args=[id])
            cronList[f"{id}AMSTOP"] = f"{set_time[4]}:{set_time[5]}"
            logger.info(f"启动：bot({id}) AMSTOP")

        if cronList.get(f"{id}PMSTOP") != f"{set_time[6]}:{set_time[7]}":
            if cronList.get(f"{id}PMSTOP") !=  None:
                scheduler.remove_job(f"{id}PMSTOP")
            scheduler.add_job(run_stop_order, "cron",
                              hour=set_time[6], minute=set_time[7], id=f"{id}PMSTOP",  args=[id])
            cronList[f"{id}PMSTOP"] = f"{set_time[6]}:{set_time[7]}"
            logger.info(f"启动：bot({id}) PMSTOP")


initialize_cron()
