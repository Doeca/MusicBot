# 负责处理行为相关，如无发言qq等级邀请低等级用户入群的行为

import json
import datetime
from . import warnsys
from nonebot import on_request, logger, on_notice
from nonebot.adapters.onebot.v11 import Bot, RequestEvent, NoticeEvent


@on_request().handle()
async def _(bot: Bot, e: RequestEvent):
    if e.request_type == 'group' and e.sub_type == 'add':
        if e.invitor_id != 0:
            logger.info("收到有人被邀请加群请求")
            invitor_info = await bot.get_group_member_info(group_id=e.group_id, user_id=e.invitor_id)
            if invitor_info['join_time'] == invitor_info['last_sent_time']:
                # 从未发言，但却邀请人进群
                # 记录警告，并拒绝此邀请，拒绝理由为从未发言，疑似广告行为
                warntimes = warnsys.set_warn(
                    e.invitor_id, f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}] 邀请人从未发言却邀请人进群")
                await bot.set_group_add_request(flag=e.flag, sub_type=e.sub_type, approve=False, reason="邀请者疑似广告行为")
                if warntimes >= 3:
                    await bot.set_group_kick(group_id=e.group_id, user_id=e.invitor_id)
                    # 从未发言，所以这个号码直接进黑名单
                    with open("./config/adbaner/black.json", 'rw') as f:
                        black_list = json.load(f)
                        black_list.append(
                            {"from_group_id": e.group_id, "user_id": e.user_id, "time": e.time, "reason": "多次未发言邀请行为"})
                        json.dump(black_list, f)
                return
        else:
            (isblack, reason) = warnsys.is_black(e.user_id)
            # 根据黑名单判断是否拒绝此人入群
            await bot.set_group_add_request(flag=e.flag, sub_type=e.sub_type, approve=(~isblack), reason=reason)
        return


@on_notice().handle()
async def _(bot: Bot, e: NoticeEvent):
    if e.NoticeEvent == 'group_decrease' and e.sub_type == 'kick':
        logger.info("有人被移出群聊")
        # 此人被踢则大概率是因为广告行为，则之后对应查询他的消息记录，这个名单后续可以被转换为黑名单
        with open("./config/adbaner/kick_list.json", 'rw') as f:
            kick_list = json.load(f)
            kick_list.append(
                {"group_id": e.group_id, "kicked_user_id": e.user_id, "time": e.time})
            json.dump(kick_list, f)
