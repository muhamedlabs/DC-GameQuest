from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class BotInformation(RecordBase):
    bot_id: str
    username: Optional[str] = MISSING
    uptime_time: Optional[str] = MISSING
    latency: Optional[str] = MISSING
    version: Optional[str] = MISSING