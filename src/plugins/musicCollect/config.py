from pydantic import BaseModel, Extra
class Config(BaseModel, extra=Extra.ignore):
    bot_id: str
    notice_id: int