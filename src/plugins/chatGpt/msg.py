
import re
import requests
import base64
from . import config
from typing import Union
from nonebot import on_message, on_command
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent


resetMatcher = on_command('reset', priority=1)
msgMatcher = on_message(rule=to_me(), priority=5)


@resetMatcher.handle()
async def reset(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher):
    matcher.stop_propagation()
    rtx_msg = ""
    try:
        v = config.getValue(f"{e.user_id}")
        index = v['index']
        converID = v['converID']
        config.getSpecificChatBot(index).delete_conversation(convo_id=converID)
        config.delValue(f"{e.user_id}")
    except:
        rtx_msg = "重置会话失败，可能数据已不存在"
    else:
        rtx_msg = "重置会话成功"

    await bot.send(event=e, message=rtx_msg, reply_message=True)


@msgMatcher.handle()
async def func(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent]):
    msg = str(e.get_message())
    print('raw msg:', msg)
    match = re.search(r'\[CQ.*file=([^,]*).*\]', msg, re.I | re.M)
    while (match != None):
        tt = await bot.get_image(file=match.group(1))
        msg = msg.replace(match.group(), "图片链接:"+tt['url'])
        match = re.search(r'\[CQ.*file=([^,]*).*\]', msg, re.I | re.M)

    index = -1
    pd = config.getValue(f"{e.user_id}")
    if (pd != None):
        index = pd['index']
    else:
        index = config.getRandomChatBot()

    if (config.getValue(f"{e.user_id}_flag") != None):
        await bot.send(event=e, message="【上一条消息还没有回复，不要急哦！】", reply_message=True)
        return
    else:
        config.setValue(f"{e.user_id}_flag", 1)
        
    if (index == -1):
        await bot.send(event=e, message="【当前无可用机器人源，请稍后再试】", reply_message=True)
        return

    rtx_msg = ""
    converID = ''
    parentID = ''
    try:
        if (pd == None):
            for data in config.getSpecificChatBot(index).ask(msg):
                rtx_msg = data["message"]
                converID = data['conversation_id']
                parentID = data['parent_id']
        else:
            for data in config.getSpecificChatBot(index).ask(msg, conversation_id=pd['converID'], parent_id=pd['parentID']):
                rtx_msg = data["message"]
                converID = data['conversation_id']
                parentID = data['parent_id']
        pd = dict({"index": index, "converID": converID, "parentID": parentID})
        config.setValue(f"{e.user_id}", pd)
    except:
        rtx_msg = '【调用时出现错误，请稍后重试或重置会话(发送/reset)】'
    else:
        pass
    config.delValue(f"{e.user_id}_flag")

    rtx_msg = rtx_msg.replace("ChatGPT", config.bot.bot_name)
    rtx_msg = f"[CQ:reply,id={e.message_id}]"+rtx_msg
    if (e.message_type == 'group'):
        
        await bot.send_msg(message_type='group', user_id=e.user_id, group_id=e.group_id, message=rtx_msg, auto_escape=False)
    else:
        await bot.send_msg(user_id=e.user_id, message=rtx_msg, auto_escape=False)
