from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class MembershipPlan:
    id: str
    name: str
    price: int
    duration_days: int
    features: List[str]