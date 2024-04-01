# 负责处理订阅相关事务

import yaml
import requests
import asyncio
import xml.etree.ElementTree as ET
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot,  PrivateMessageEvent

"""
订阅流程：
发送mikan的rss订阅自动订阅
读取一次，获取番剧标题，如果被订阅过则不再订阅
如果没有就加入到订阅标题里

检查流程：
1. 读取rss链接，读取每一集的标题有没有被下载过，没有下载就提交下载链接

路径是  /downloads/番剧名/文件名

问题：
如果已经完结了该怎么办？手动退订？
"""


def getConfig():
    return yaml.load(open("./config/anime.yml", "r", encoding="utf-8"), Loader=yaml.FullLoader)


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
            await asyncio.sleep(2)
            pass
    return None


@on_command("sublist").handle()
async def _(bot: Bot, e: PrivateMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    config = getConfig()

    subs = []
    # 检查番剧有无此用户订阅记录
    subcribers:dict = config.get("subcriber", {})
    for key in subcribers.keys():
        if e.user_id in subcribers[key]:
            subs.append(f"{len(subs)+1}.{key}")

    subtext = "\n".join(subs)
    await matcher.finish(f"订阅列表:\n{subtext}")

   

@on_command("unsub").handle()
async def _(bot: Bot, e: PrivateMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    await bot.send(e, "取消订阅中，请稍后~")
    config = getConfig()

    # 获取当前的所有订阅番剧 及 相关的 订阅者
    animes = config.get("sub", [])
    anime_titles = [anime['title'] for anime in animes]
    

    aim_name = args.extract_plain_text().strip()
    if aim_name == "" or (aim_name not in anime_titles):
        await matcher.finish("请输入正确的番剧名！例：/unsub 葬送的芙莉莲")
        return

    # 从订阅者中删除数据
    subcribers:dict = config.get("subcriber", {})
    subcribers:list = subcribers.get(aim_name,[])
    subcribers.remove(e.user_id)

    ## 若该番剧订阅者为空，删除订阅相关信息
    if len(subcribers) == 0:
        subcribers:dict = config.get("subcriber", {})
        subcribers.pop(aim_name)
        config.get("sub").pop(anime_titles.index(aim_name))

    yaml.dump(config, open("./config/anime.yml", "w",
                           encoding="utf-8"), allow_unicode=True)
    from . import cron
    await matcher.finish("取消订阅成功~🤘")
    return

    


@on_command("sub").handle()
async def _(bot: Bot, e: PrivateMessageEvent, matcher: Matcher, args: Message = CommandArg()):
    await bot.send(e, "正在订阅中，请稍后~")
    link = args.extract_plain_text().strip()
    if link == "" or not link.startswith("https://mikanani.me/RSS/"):
        await matcher.finish("请输入蜜柑计划的Rss订阅链接🔗")
        return
    resp = await httpGet(link)
    if resp is None:
        await matcher.finish("获取数据失败，请稍后再试🤐")
        return
    config = getConfig()
    root = ET.fromstring(resp)
    title = root.find('./channel/title').text
    title = title.replace("Mikan Project - ", "")

    # 获取当前的所有订阅番剧 及 相关的 订阅者
    animes = config.get("sub", [])
    anime_titles = [anime['title'] for anime in animes]
    subcribers = config.get("subcriber", {})

    
    if title not in anime_titles:
        animes.append({"title": title, "link": link})
        config['sub'] = animes
        subcribers[title] = [e.user_id]
        config["subcriber"] = subcribers
    else:
        # 已经有过数据，说明已经有人订阅过
        if e.user_id in subcribers[title]:
            await matcher.finish("您已经订阅过了哦~👈")
            return
        config["subcriber"][title].append(e.user_id)

    yaml.dump(config, open("./config/anime.yml", "w",
                           encoding="utf-8"), allow_unicode=True)
    from . import cron
    await matcher.finish("订阅成功~🤘")
    return
