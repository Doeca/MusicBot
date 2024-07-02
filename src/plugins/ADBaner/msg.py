from . import sql
from PIL import Image

import pytesseract
import hashlib
import requests


from nonebot import on_message, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message, MessageSegment
from nonebot.rule import is_type

rule = is_type(GroupMessageEvent)

msg_matcher = on_message(rule=rule, block=False, priority=100)


@msg_matcher.handle()
async def _ (bot: Bot, e: GroupMessageEvent):
    msg: Message = e.get_message()
    timestamp = e.time
    for msg_seg in msg:
        if msg_seg.type == 'text':
            sql.insert_data(
                'text', msg_seg.data['text'], e.group_id, e.user_id)
            # 统计相关信息到数据库中
        elif msg_seg.type == 'image':

            logger.info(f"图片消息: {msg_seg.data['url']}")
            # 获取图片原文件
            md5_hash = hashlib.md5()
            md5_hash.update(msg_seg.data['url'].encode('utf-8'))
            sign = md5_hash.hexdigest()[:5]
            filename = f"./config/adbaner/images/{e.group_id}_{e.user_id}_{timestamp}_{sign}.jpg"
            open(filename, 'wb').write(requests.get(msg_seg.data['url'], headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
            }).content)

            # 进行ocr识别，并保留原图，将ocr结果存入数据库
            image = Image.open(filename)
            ocrtext = pytesseract.image_to_string(image, lang='chi_sim')
            digest = f"""路径:{filename}\n摘要:{ocrtext}"""
            sql.insert_data('image', digest, e.group_id, e.user_id)
