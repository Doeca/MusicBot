import json
from . import util
from . import config
from nonebot.log import logger
from nonebot.adapters import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg,  ArgStr
from nonebot import on_command,  on_regex
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
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
    util.addOperation(school_id, "volume", volume)
    await volume_matcher.finish(f"已将音量调整为{rarg}")

logger.info("管理端命令加载完成")