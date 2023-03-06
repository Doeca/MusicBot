from nonebot import get_driver
from pydantic import BaseModel, Extra


class Config(BaseModel, extra=Extra.ignore):
    bot_id: str
    bing_api: str


bot = Config.parse_obj(get_driver().config)
