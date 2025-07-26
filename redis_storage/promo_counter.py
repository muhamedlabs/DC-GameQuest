from dataclasses import dataclass
from ashredis import RecordBase, MISSING
from typing import Optional

@dataclass
class PromoCounter(RecordBase):
    channel_id: str 
    sub_counter: Optional[int] = MISSING
    donate_counter: Optional[int] = MISSING
