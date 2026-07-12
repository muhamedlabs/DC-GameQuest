from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class AutoMessages(RecordBase):
    id: str 
    message_id: Optional[str] = MISSING
    channel_id: Optional[str] = MISSING 
    timestamp: Optional[str] = MISSING