import base64
from . import util
from . import config
import json
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







reload_matcher = on_command("reload", permission=SUPERUSER)


@reload_matcher.handle()
async def glist_handle(bot: Bot, e: PrivateMessageEvent):
    from . import config
    from . import cron
    await config.init_config()
    await cron.init_cron()
    resp = "已重载"
    await bot.send(e, message=resp)


@on_command("hook", permission=SUPERUSER).handle()
async def hook_handle(bot: Bot, e: PrivateMessageEvent):
    from . import wxlib
    res = await wxlib.hookSyncMsg()
    resp = f"hook结果:{res}"
    await bot.send(e, message=resp)

unhook_matcher = on_command("unhook", permission=SUPERUSER)


@unhook_matcher.handle()
async def unhook_handle(bot: Bot, e: PrivateMessageEvent):
    from . import wxlib
    res = await wxlib.unhookSyncMsg()
    resp = f"unhook结果:{res}"
    await bot.send(e, message=resp)


wxgroup_matcher = on_command("wxgroup", permission=SUPERUSER)


@wxgroup_matcher.handle()
async def wxgroup_handle(bot: Bot, e: PrivateMessageEvent):
    from . import wxlib
    res = await wxlib.getContacts()
    await bot.send(e, message=json.dumps(res, ensure_ascii=False))

cronlist_matcher = on_command("cronlist", permission=SUPERUSER)


@cronlist_matcher.handle()
async def cronlist_handle(bot: Bot, e: PrivateMessageEvent):
    from . import cron
    cron.get_cron_list()
    crons = []
    for job in cron.cronList:
        crons.append(
            f"id:{job['id']} type:{job['type']} {job['arg']}")
    res = "\n".join(crons)
    await bot.send(e, message=res)


logger.info("管理端命令加载完成")
