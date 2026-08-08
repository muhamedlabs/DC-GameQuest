from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING


@dataclass
class BotBlocking(RecordBase):
    user_id: str
    username: Optional[str] = MISSING
    descriptions_blocking: Optional[str] = MISSING
    banned_by: Optional[str] = MISSING
    time_blocking: Optional[str] = MISSING

    last_pm_at: Optional[str] = MISSING