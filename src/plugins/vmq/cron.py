import time
import requests
import datetime
import random
import os
import json
import asyncio
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import Bot
from nonebot_plugin_apscheduler import scheduler
from nonebot.log import logger
from nonebot import require
import hashlib
require("nonebot_plugin_apscheduler")

host = "https://vm.cquluna.top/"
secretkey = "88feaef9e14a466a95ce6a72881bd323"


@scheduler.scheduled_job('cron', minute='*/3')
async def heartbeat():
    # get timestamp
    timestamp = int(time.time())
    # python get md5
    # generate md5 hash
    md5_hash = hashlib.md5()
    md5_hash.update((str(timestamp)+secretkey).encode('utf-8'))
    sign = md5_hash.hexdigest()
    # send request
    url = host + f"appHeart?t={timestamp}&sign={sign}"
    logger.info(f"heartbeat res: {requests.get(url).text}")
