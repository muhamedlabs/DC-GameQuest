from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class PostulateMessage(RecordBase):
    channel_id: str
    message_id: Optional[str] = MISSING
    time_message: Optional[str] = MISSING
