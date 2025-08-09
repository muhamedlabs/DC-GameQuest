from dataclasses import dataclass, field
from typing import Optional, Dict
from ashredis import RecordBase, MISSING

@dataclass
class SatbatManager(RecordBase):
    user_id: str
    username: Optional[str] = MISSING
    transition_random_voice: Optional[int] = 0
    transitions_history: Optional[Dict[str, str]] = field(default_factory=dict)
    last_transition_time: Optional[str] = None
