from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class ReactionManager(RecordBase):
    user_id: str
    username: Optional[str] = MISSING
    reaction_from_bot: Optional[str] = MISSING
