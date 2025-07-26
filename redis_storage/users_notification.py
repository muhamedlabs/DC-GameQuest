from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class UsersNotification(RecordBase):
    user_id: str
    username: Optional[str] = MISSING
    first_message_time: Optional[str] = MISSING
    first_message_content: Optional[str] = MISSING
