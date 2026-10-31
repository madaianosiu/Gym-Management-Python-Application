from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

SubscriptionStatus = Literal["ACTIVE", "INACTIVE", "CANCELED", "PENDING"]

@dataclass(frozen=True)
class Subscription:
    id: str
    user_id: str
    plan_id: str
    status: SubscriptionStatus
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None