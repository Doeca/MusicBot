import base64
import json
import random

from . import util
from . import config
from typing import Union
from nonebot.log import logger
from nonebot.matcher import Matcher
from nonebot.params import CommandArg,  ArgStr
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, PrivateMessageEvent, Message, MessageSegment
from nonebot.permission import SUPERUSER
from nonebot.adapters.onebot.v11 import GROUP_ADMIN, GROUP_OWNER

volume_matcher = on_command("volume", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER), aliases={"音量"}, rule=util.group_checker)


@volume_matcher.handle()
async def volume_handle(bot: Bot, matcher: Matcher, args: Message = CommandArg()):
    rarg = args.extract_plain_text().strip()
    volume = rarg
    if volume != '':
        if (volume.find("%") != -1):
            volume = volume.replace("%", "")
        volume = float(volume)
        if (volume > 1):
            volume = volume*0.01
        matcher.set_arg("arg", rarg)


@volume_matcher.got("arg", prompt="请输入音量百分比，例如：70%")
async def volume_got(e: GroupMessageEvent, arg: str = ArgStr('arg')):
    school_id = await config.get_id(str(e.group_id))
    status = await util.get_switch(school_id)
    if status == False:
        await volume_matcher.finish("当前不在点歌时间段内，不能点歌哦🥺")
        return
    rarg = arg.strip()
    volume = rarg
    if volume == '':
        await volume_matcher.finish(f"操作已取消")
    else:
        if (volume.find("%") != -1):
            volume = volume.replace("%", "")
        volume = float(volume)
        if (volume > 1):
            volume = volume*0.01
    await util.addOperation(school_id, "volume", volume)
    await volume_matcher.finish(f"已将音量调整为{rarg}")


notify_matcher = on_command("notify", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER), aliases={"通知"}, rule=util.group_checker)


@notify_matcher.handle()
async def notify_handle(bot: Bot, matcher: Matcher, args: Message = CommandArg()):
    rarg = args.extract_plain_text().strip()
    msg = rarg
    if msg != '':
        matcher.set_arg("arg", msg)


@notify_matcher.got("arg", prompt="请输入要广播通知的内容")
async def notify_got(e: GroupMessageEvent, arg: str = ArgStr('arg')):
    try:
        school_id = await config.get_id(str(e.group_id))
        status = await util.get_switch(school_id)
        if status == False:
            await notify_matcher.finish("当前不在点歌时间段内，不能使用该功能哦🥺")
            return
        rarg = arg.strip()
        msg = rarg
        if msg == '':
            await notify_matcher.finish(f"操作已取消")
        else:
            msg = f"现在进行广播通知：{msg}。；{msg}。；{msg}。通知完毕。"
            msg = str(base64.b64encode(msg.encode("utf-8")), "utf-8")
            apiUrl = config.system.music_api
            resp = await util.httpGet(f"{apiUrl}/ttsgenerate?msg={msg}&key=D8as1gv34")
            if resp == None:
               await notify_matcher.finish("生成通知时出现错误，请稍后再试😢")
            res: dict = json.loads(resp)
            info: dict = config.schoolInfo.get(school_id, {})
            play_list: list = info.get('play_list', [])
            
            async with config.lock:
                insert_index = 0  # 默认插到最前面
                for i in range(len(play_list) - 1, -1, -1):  # 从最后往前找
                    if play_list[i]['played'] == 1:
                        insert_index = i + 1
                        break
                play_list.insert(insert_index, {
                    "id": 50000 + random.randint(0, 9999),
                    "played": 0,
                    "info": res
                })
                config.upsert_info(info['log_id'], json.dumps(info))
            await notify_matcher.finish(f"通知将于当前歌曲播放完后播出👌")
    except Exception as e:
        return



sporder_matcher = on_command("sporder", permission=(
    SUPERUSER | GROUP_ADMIN | GROUP_OWNER), aliases={"特殊点歌"}, rule=util.group_checker)


@sporder_matcher.handle()
async def sporder_handle(bot: Bot, matcher: Matcher, args: Message = CommandArg()):
    rarg = args.extract_plain_text().strip()
    msg = rarg
    if msg != '':
        matcher.set_arg("arg", msg)


@sporder_matcher.got("arg", prompt="请输入歌曲名称及祝福词，例如\n绿光 孙燕姿，祝福词：a同学祝愿b同学生日快乐")
async def sporder_got(e: GroupMessageEvent, arg: str = ArgStr('arg')):
    try:
        school_id = await config.get_id(str(e.group_id))
        status = await util.get_switch(school_id)
        if status == False:
            await sporder_matcher.finish("当前不在点歌时间段内，不能使用该功能哦🥺")
            return
        rarg = arg.strip()
        msg = rarg
        if msg == '':
            await sporder_matcher.finish(f"本次操作已取消，请重新发送命令")
        else:
            apiUrl = config.system.music_api
            # 获取歌曲名及祝福词，调用接口获取歌曲信息，如果歌曲信息获取成功则进行歌单插入操作
            music_info = util.get_music_info(msg)
            logger.debug(f"special music_info is {music_info}")
            if music_info['keywords'] == '':
                await sporder_matcher.finish("未能从输入中识别出歌曲名称，请重新发送命令")
            
            resp = await util.httpGet(f"{apiUrl}/match?keywords={music_info['keywords']}&key=D8as1gv34")
            if resp == None:
                await sporder_matcher.finish('获取歌曲信息失败，请重新发送命令😢')
            song_res: dict = json.loads(resp)

            msg = music_info['msg']
            if msg != '':
                msg = str(base64.b64encode(msg.encode("utf-8")), "utf-8")
                resp = await util.httpGet(f"{apiUrl}/ttsgenerate?msg={msg}&key=D8as1gv34")
                if resp == None:
                    await sporder_matcher.finish("生成祝福词时出现错误，请稍后再试😢")
                word_res: dict = json.loads(resp)

            info: dict = config.schoolInfo.get(school_id, {})
            song_list: list = info.get('song_list', [])
            play_list: list = info.get('play_list', [])

            song_info = {
                "name": song_res['name'],
                "author": song_res['author'],
                "playUrl": song_res['playUrl'],
                "lrcUrl": song_res['lrcUrl'],
                "cover": song_res['cover'],
                "id": len(song_list) + 1,
                "uin": e.user_id,
                "lang": song_res['lang']
            }

            async with config.lock:
                song_list.append(song_info)
                insert_index = 0  # 默认插到最前面
                for i in range(len(play_list) - 1, -1, -1):  # 从最后往前找
                    if play_list[i]['played'] == 1:
                        insert_index = i + 1
                        break
                play_list.insert(insert_index, {
                    "id": song_info['id'],
                    "played": 0
                })
                if msg != '':
                    play_list.insert(insert_index, {
                        "id": 50000 + random.randint(0, 9999),
                        "played": 0,
                        "info": word_res
                    })
                config.upsert_info(info['log_id'], json.dumps(info))
            
            await sporder_matcher.finish(f"本歌曲将于当前歌曲播放完后播出👌")
    except Exception as e:
        return
    
logger.info("管理端命令加载完成")
