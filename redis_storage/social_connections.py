from dataclasses import dataclass
from ashredis import RecordBase, MISSING
from typing import Optional

@dataclass
class SocialConnections(RecordBase):
    message_preview: Optional[str] = MISSING
    telegram_message_id: Optional[int] = MISSING
    discord_message_id: Optional[int] = MISSING
    timestamp: Optional[str] = MISSING
