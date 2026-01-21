from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class DispatcherMessage(RecordBase):
    id: str #Первих 8 символов
    file_id: Optional[str] = MISSING # ID исходного сообщения
    source_id: Optional[str] = MISSING # ID канал оригинального сообщения
    message_id: Optional[str] = MISSING  # ID сообщения в канале
    channel_id: Optional[str] = MISSING # ID канал куда отправили ботом
    user_id: Optional[str] = MISSING
    username: Optional[str] = MISSING
    timestamp: Optional[str] = MISSING