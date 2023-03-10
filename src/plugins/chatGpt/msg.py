
import re
from . import config
from typing import Union
from nonebot import on_message, on_command
from nonebot.log import logger
from nonebot.rule import to_me
from nonebot.matcher import Matcher
from nonebot.utils import run_sync
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent

switchMatcher = on_command('switch', priority=1, permission=SUPERUSER)
resetMatcher = on_command('reset', priority=1)
refreshMatcher = on_command("refresh", permission=SUPERUSER, priority=1)
msgMatcher = on_message(rule=to_me(), priority=5)


@run_sync
def get_Message(pd: str, index: str, msg: str, bot: Bot, e):
    rtx_msg = ""
    converID = ''
    parentID = ''
    i = 0
    if (pd == None):
        for data in config.getSpecificChatBot(index).ask(msg, timeout=3600):
            i = i + 1
            if i >= 500:
                bot.send(event=e, message="回复将很快生成，请再耐心等待一会⌛️")
                i = 0
            # print(data)
            rtx_msg = data["message"]
            converID = data['conversation_id']
            parentID = data['parent_id']
    else:
        for data in config.getSpecificChatBot(index).ask(msg, conversation_id=pd['converID'], parent_id=pd['parentID'], timeout=3600):
            i = i + 1
            if i >= 500:
                bot.send(event=e, message="回复将很快生成，请再耐心等待一会⌛️")
                i = 0
            # print(data)
            rtx_msg = data["message"]
            converID = data['conversation_id']
            parentID = data['parent_id']
    return [rtx_msg, converID, parentID]


@run_sync
def del_conver(index, converID):
    config.getSpecificChatBot(index).delete_conversation(convo_id=converID)


@refreshMatcher.handle()
async def change(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher):
    matcher.stop_propagation()
    config.refreshAct()
    len = config.getLen()
    await bot.send(message=f"✌️已经刷新GPT账号列表，当前个数：{len}", event=e)


@resetMatcher.handle()
async def reset(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher):
    matcher.stop_propagation()
    rtx_msg = ""
    try:
        if (config.getValue(f"{e.user_id}_flag") != None):
            config.delValue(f"{e.user_id}_flag")
        v = config.getValue(f"{e.user_id}")
        index = v['index']
        converID = v['converID']
        config.delValue(f"{e.user_id}")
        await del_conver(index, converID)
    except:
        rtx_msg = "❌重置会话失败，可能数据已不存在"
    else:
        rtx_msg = "✅重置会话成功"

    await bot.send(event=e, message=rtx_msg, reply_message=True)


@ msgMatcher.handle()
async def func(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent]):
    if (config.getSwitch() == 0):
        if (e.message_type == 'group'):
            await bot.send(event=e, message="🈲️此功能已被关闭", reply_message=True)
        return

    msg = str(e.get_message())
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
        await bot.send(event=e, message="上一条消息还没有回复，不要急哦😡！", reply_message=True)
        return
    else:
        config.setValue(f"{e.user_id}_flag", 1)

    if (index == -1):
        await bot.send(event=e, message="当前无可用机器人源，请稍后再试🤯", reply_message=True)
        return

    rtx_msg = ""
    converID = ''
    parentID = ''

    logger.info(f"ChatGPT账号index:{index}")
    # try:
    #     [rtx_msg, converID, parentID] = await get_Message(pd, index, msg, bot, e)
    #     pd = dict({"index": index, "converID": converID, "parentID": parentID})
    #     config.setValue(f"{e.user_id}", pd)
    # except:
    #     rtx_msg = '🥶调用时出现错误，请稍后重试或 重置会话(发送 /reset)'
    # else:
    #     pass

    [rtx_msg, converID, parentID] = await get_Message(pd, index, msg, bot, e)
    pd = dict({"index": index, "converID": converID, "parentID": parentID})
    config.setValue(f"{e.user_id}", pd)

    config.delValue(f"{e.user_id}_flag")

    rtx_msg = rtx_msg.replace("ChatGPT", config.bot.bot_name)
    rtx_msg = f"[CQ:reply,id={e.message_id}]"+rtx_msg
    if (e.message_type == 'group'):

        await bot.send_msg(message_type='group', user_id=e.user_id, group_id=e.group_id, message=rtx_msg, auto_escape=False)
    else:
        await bot.send_msg(user_id=e.user_id, message=rtx_msg, auto_escape=False)


@switchMatcher.handle()
async def func(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher):
    matcher.stop_propagation()
    if (config.getSwitch() == 1):
        config.setSwitch(0)
        await bot.send(message=f"🤐已关闭GPT功能", event=e)
    else:
        config.setSwitch(1)
        await bot.send(message=f"😆已开启GPT功能", event=e)
