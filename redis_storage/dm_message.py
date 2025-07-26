from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class DMLogEntry(RecordBase):
    user_id: str
    username: Optional[str] = MISSING
    content: Optional[str] = MISSING
    timestamp: Optional[str] = MISSING
