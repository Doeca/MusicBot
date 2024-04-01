# 负责根据本地订阅事件，定时更新订阅内容
import asyncio
import re
import yaml
import requests
import aiohttp
import xml.etree.ElementTree as ET
from nonebot_plugin_apscheduler import scheduler
from nonebot import require, logger
require("nonebot_plugin_apscheduler")


def getConfig():

    return yaml.safe_load(open("./config/anime.yml", "r", encoding="utf-8"))


def getID():
    import time
    import random
    import base64
    return base64.b64encode(f"AriaNg_{int(time.time())}_{random.uniform(0, 1)}".encode("utf-8")).decode("utf-8")


async def httpGet(url, head={}):
    i = 0
    while i<=3:
        try:
            config = getConfig()
            p = config.get("proxy", "http://127.0.0.1:7890")
            resp = requests.get(url, proxies={"https": p, "http": p})
            return resp.text
        except:
            i += 1
            await asyncio.sleep(1000)
            pass
    return None


async def httpPost(url, data, head={}):
    head['Content-Type'] = 'application/json;charset=UTF-8'
    async with aiohttp.ClientSession(headers=head) as session:
        async with session.post(url, json=data) as resp:
            if resp.status == 200:  # Check if the response status is OK
                data = await resp.json()  # Parse JSON from the response
                return data
            else:
                return ""


@scheduler.scheduled_job('cron', minute='*/10')
async def check():
    logger.info("正在检查番剧更新")
    config = getConfig()
    aria2Link = config.get("aria2", "https://aria.doeca.cc:16800/jsonrpc")
    downloaded = config.get("downloaded", [])
    logger.debug(config.get("sub", []))
    for anime in config.get("sub", []):
        logger.debug(anime['link'])
        resp = await httpGet(anime['link'])
        logger.debug(resp)
        root = ET.fromstring(resp)
        for item in root.findall('.//item'):
            title = item.find('title').text
            link = item.find('link').text
            if (title in downloaded):
                # 已经提交过下载
                continue
            logger.info(f"检测到新番：{title}")
            # 获取下载链接 Start
            resp = await httpGet(link)
            match = re.search(
                r'<a class="btn episode-btn" href="(.*?)">磁力链接<\/a>', resp)
            if match is None:
                logger.error(f"获取下载链接失败：{link}")
                continue
            else:
                downloadLink = match.group(1)
                downloadLink = downloadLink.replace("&amp;", "&")
                logger.info(f"获取到下载链接：{downloadLink}")
            # 获取下载链接 End
            # 提交Aria2 Start
            res = await httpPost(aria2Link, {
                "jsonrpc": "2.0",
                "method": "aria2.addUri",
                "id": getID(),
                "params": [
                    "token:H3S7kbxl6wfR",
                    [
                        downloadLink
                    ],
                    {
                        "dir": f"/downloads/doeca/Anime/{anime['title']}"
                    }
                ]
            })
            if res is None:
                logger.error(f"提交下载链接失败：{link}")
                continue
            else:
                logger.success(f"提交下载链接成功：{res}")
            downloaded.append(title)  # 加入已下载标记
            # 提交Aria2 End
    config['downloaded'] = downloaded
    yaml.dump(config, open("./config/anime.yml", "w",
              encoding="utf-8"), allow_unicode=True)


