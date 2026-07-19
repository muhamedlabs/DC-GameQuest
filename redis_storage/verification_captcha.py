from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class VerificationCaptcha(RecordBase):
    user_id: str
    username: Optional[str] = MISSING
    content: Optional[str] = MISSING
    time_captcha: Optional[str] = MISSING
    time_message: Optional[str] = MISSING