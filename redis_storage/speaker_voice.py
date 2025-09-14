from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class SpeakerVoice(RecordBase):
    session_id: str
    bot_id: Optional[str] = MISSING
    channel_id: Optional[str] = MISSING
    random_channel_id: Optional[str] = MISSING
    enter_voice_channel: Optional[str] = MISSING
    end_voice_channel: Optional[str] = MISSING
    time: Optional[str] = MISSING
