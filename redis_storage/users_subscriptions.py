from dataclasses import dataclass
from typing import Optional
from ashredis import RecordBase, MISSING

@dataclass
class UsersSubscriptions(RecordBase):
    user_id: str
    username: Optional[str] = MISSING
    subscription: Optional[str] = MISSING
    time_actions_commands: Optional[str] = MISSING
    number_canceled_subscriptions: Optional[str] = MISSING
