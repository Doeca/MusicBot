import base64
import re
import requests
import yaml
from typing import Union
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot,  GroupMessageEvent, PrivateMessageEvent

matcher = on_command("custom")

@matcher.handle()
async def handle(m: Matcher, bot: Bot, event: GroupMessageEvent, cmd: Message = CommandArg()):
    bot.delete_msg(event.message_id)
    await m.finish("🤬不要在群里发订阅链接")
    return

@matcher.handle()
async def handle(m: Matcher, bot: Bot, event: PrivateMessageEvent, cmd: Message = CommandArg()):
    ptxt = cmd.extract_plain_text()
    args = ptxt.split(" ")
    moon_url = ""
    custom_url = ""
    for arg in args:
        if "cquluna.top" in arg:
            moon_url = arg
        else:
            custom_url = arg
    if moon_url == "" or custom_url == "":
        await m.finish("🤐参数错误，正确格式：/custom 往月门订阅链接 自购机场订阅链接（clash）")
        return
    try:
        rawinfo = requests.get(custom_url,headers={"user-agent": "Stash/2.4.6 Clash/1.9.0"})
        data: dict = yaml.safe_load(rawinfo.text)
        if len(data['proxies']) == 0:
            await m.finish("😤自购机场订阅链接有误，请检查是否为Clash订阅链接")
            return
    except Exception as e:
        await m.finish("🫤获取自建机场订阅信息失败，可能为服务器网络原因，请稍后再试")
        return
    
    res = re.search(r'cquluna\.top:30000\/api\/v1\/client\/subscribe\?token=(.*)', moon_url)
    if res is None:
        await m.finish("😤往月门订阅链接有误，请检查是否为往月门订阅链接")
        return
    else:
        token = res.group(1)
    
    
    resp = f"https://tun6.cquluna.top:30000/api/v2/client/subscribe?token={token}&custom={base64.b64encode(custom_url.encode('utf-8')).decode()}"

    await m.finish(f"🥳订阅链接已生成，请参阅教程在clash中使用此订阅链接：\n{resp}")