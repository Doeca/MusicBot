import json
import base64
import requests
import asyncio
from . import labctrl
from . import util
from . import config
from typing import Union
from nonebot import on_command
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg,  ArgStr
from nonebot.adapters.onebot.v11 import Bot,  GroupMessageEvent, PrivateMessageEvent

bindMatcher = on_command(
    "bind", aliases={"绑定学号"}, rule=util.group_checker)

lock = asyncio.Lock()
file_lock = asyncio.Lock()


@bindMatcher.handle()
async def bindHandle(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], matcher: Matcher, args: Message = CommandArg()):
    if args.extract_plain_text():
        matcher.set_arg("stuID", args)


@bindMatcher.got("stuID", prompt="请输入8位学号")
async def bindStuID(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent], arg: str = ArgStr('stuID')):
    stuID = arg.strip()
    if (config.userList.get(f'stu{stuID}', 0) == e.user_id):
        await bot.send(e, message=f"该学号已经被你绑定了，快看看说明书怎么用吧😅", reply_message=True)
        return
    if (config.userList.get(f'stu{stuID}', 0) != 0):
        await bot.send(e, message=f"该学号已被他人绑定，无法重复绑定😅", reply_message=True)
        return
    await bot.send(e, message=f"😼💦正在绑定，请稍候", reply_message=True)
    labct = labctrl.LabControl()
    if (labct.getID(stuID) == ''):
        await bot.send(e, message=f"查无此学号，请检查输入😇", reply_message=True)
        return
    change = False
    if (config.userList.get(f'qq{e.user_id}', '0') != '0'):
        change = True
    config.userList[f'stu{stuID}'] = e.user_id
    config.userList[f'qq{e.user_id}'] = stuID

    if change:
        await bot.send(e, message=f"换绑学号成功🥰", reply_message=True)
    else:
        await bot.send(e, message=f"绑定学号成功🥰", reply_message=True)

    async with file_lock:
        fs = open(f"./config/sxic/info.json", 'w')
        userlist_str = json.dumps(config.userList)
        fs.write(userlist_str)
        fs.close()

    carNumb = labct.getCarNumb(stuID)
    if (carNumb != ''):
        await applyHandle(bot, e)


applyMatcher = on_command("apply", aliases={"申请权限"}, rule=util.group_checker)


@applyMatcher.handle()
async def applyHandle(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent]):
    async with lock:
        stuID = config.userList.get(f'qq{e.user_id}', '0')
        if stuID == '0':
            await bot.send(e, message=f"请先绑定学号再使用此命令😤", reply_message=True)
            return
        await bot.send(e, message=f"😼💦正在申请权限，请稍候", reply_message=True)
        labct = labctrl.LabControl()
        carNumb = labct.getCarNumb(stuID)
        if carNumb == '':
            await bot.send(e, message=f"请先在门禁面板处进行卡片注册再使用此命令😤", reply_message=True)
            return
        if e.message_type == 'private':
            gcode = 0
        else:
            gcode = e.group_id
        userAuth: list = config.system["auths"][f'group{gcode}']
        roomNames = []
        for v in userAuth:
            roomNames.append(config.roomList[f'id{v}'])
        roomName = ",".join(roomNames)
        if labct.setAuth(stuID, userAuth):
            await bot.send(e, message=f"卡片({carNumb})已开通【{roomName}】的门禁权限，3～5分钟后即可刷卡开门😎", reply_message=True)
            config.userList[f'card{carNumb}'] = e.user_id
            async with file_lock:
                fs = open(f"./config/sxic/info.json", 'w')
                userlist_str = json.dumps(config.userList)
                fs.write(userlist_str)
                fs.close()
            return
        else:
            if ((bindUser := config.userList.get(f'card{carNumb}', 0)) != e.user_id):
                if bindUser == 0:
                    config.userList[f'card{carNumb}'] = e.user_id
                    async with file_lock:
                        fs = open(f"./config/sxic/info.json", 'w')
                        userlist_str = json.dumps(config.userList)
                        fs.write(userlist_str)
                        fs.close()
                else:
                    await bot.send(e, message=f"卡片({carNumb})已被qq({bindUser})绑定🥵\n如若有误请先重置卡片😶‍🌫️\n重新进行卡片注册再使用此命令🫣", reply_message=True)
                    return
            await bot.send(e, message=f"此账户已经开通过门禁权限🥵\n如若有误请先重置卡片😶‍🌫️\n重新进行卡片注册再使用此命令🫣", reply_message=True)
            return


resetMatcher = on_command("reset", aliases={"重置卡片"}, rule=util.group_checker)


@resetMatcher.handle()
async def resetHandle(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent]):
    stuID = config.userList.get(f'qq{e.user_id}', '0')
    if stuID == '0':
        await bot.send(e, message=f"请先绑定学号再使用此命令😤", reply_message=True)
        return
    await bot.send(e, message=f"😼💦正在重置，请稍候", reply_message=True)
    labct = labctrl.LabControl()

    if labct.rmCard(stuID):
        await bot.send(e, message=f"卡片重置成功🥱", reply_message=True)
        return
    else:
        await bot.send(e, message=f"此账户未进行卡片注册，无需重置😑", reply_message=True)
        return


viewMatcher = on_command("mycard", aliases={"我的卡片"}, rule=util.group_checker)


@viewMatcher.handle()
async def viewHandle(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent]):
    stuID = config.userList.get(f'qq{e.user_id}', '0')
    if stuID == '0':
        await bot.send(e, message=f"请先绑定学号再使用此命令😤", reply_message=True)
        return
    await bot.send(e, message=f"😼💦正在读取卡片信息，请稍候", reply_message=True)
    labct = labctrl.LabControl()
    carNumb = labct.getCarNumb(stuID)
    if carNumb == '':
        await bot.send(e, message=f"请先在门禁面板处进行卡片注册再使用此命令😤", reply_message=True)
        return
    userAuth = labct.getCardInfo(stuID)
    roomNames = []
    for v in userAuth:
        roomNames.append(config.roomList[f'id{v}'])
    roomName = ",".join(roomNames)
    await bot.send(e, message=f"账户绑定卡号：{carNumb}\n开通门禁权限：【{roomName}】", reply_message=True)


recordMatcher = on_command("readAllCard", rule=util.group_checker)


@recordMatcher.handle()
async def recordHandle(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent]):
    tmp = labctrl.LabControl()
    keys = list(config.userList.keys())[:]
    for key in keys:
        key: str = key
        if (key.find('qq') == -1):
            continue
        stuid = config.userList[key]
        cardNumb = tmp.getCarNumb(stuid)
        if (cardNumb != ""):
            config.userList[f'card{cardNumb}'] = int(key.replace('qq', ''))
    fs = open(f"./config/sxic/info.json", 'w')
    userlist_str = json.dumps(config.userList)
    fs.write(userlist_str)
    fs.close()
    await bot.send(e, message=f"已经更新所有卡号对应的qq", reply_message=True)


@on_command("removeTiger").handle()
async def _(bot: Bot, e: Union[GroupMessageEvent, PrivateMessageEvent]):
    tmp = labctrl.LabControl(
        "C0403", "aRLUmk0gaiwV1r0Ak7kNizTyFU%2BZor65hRjHRHTLxnOf%2Bo3Vb3N9uCPLGCzLkbM%2BcpHBAf%2B7sjiOSNQbhf7o4ZDftduOONnKZuVSHhA5i8sldxO%2FmH6RKS%2FgA0ZqlybM02b7%2F0IG3BK5rZLzPMHWm1aHGOtrNwEqnvJqWIJ9F0g%3D")
    await bot.send(e, message=f"done.{tmp.tigerRemove()}")
