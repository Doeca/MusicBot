from nonebot import get_bot
from nonebot import require
require("nonebot_plugin_apscheduler")
from nonebot_plugin_apscheduler import scheduler
import requests
import json

# @scheduler.scheduled_job("cron", id="fetch", second="*/10")
# async def run_every_10_seconds():
#     #print("trrigered")
#     resp = requests.get("http://api.doeca.cc/custom/readMsg.php")
#     if resp.status_code == 200:
#         #print(resp.text)
#         tab = json.loads(resp.text)
#         bot = get_bot("3155506801")
#         for msg in tab['body']:
#             await bot.send_private_msg(user_id=1124468334,message=msg)
