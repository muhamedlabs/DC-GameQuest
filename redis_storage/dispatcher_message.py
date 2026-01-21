from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class DispatcherMessage(RecordBase):
    id: str #Первих 8 символов
    file_id: Optional[str] = MISSING
    message_id: Optional[str] = MISSING
    channel_id: Optional[str] = MISSING
    user_id: Optional[str] = MISSING
    username: Optional[str] = MISSING
    timestamp: Optional[str] = MISSING