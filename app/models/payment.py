from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

PaymentStatus = Literal["CREATED", "PENDING", "SUCCESS", "FAILED"]

@dataclass(frozen=True)
class Payment:
    id: str
    user_id: str
    amount: int
    currency: str = "USD"
    status: PaymentStatus = "CREATED"
    provider_ref: Optional[str] = None
    created_at: Optional[datetime] = None