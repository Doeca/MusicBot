import os
import json
from nonebot import get_driver
from pydantic import BaseModel, Extra

class Config(BaseModel, extra=Extra.ignore):
    bot_id: str
    notice_id: int

bot = Config.parse_obj(get_driver().config)