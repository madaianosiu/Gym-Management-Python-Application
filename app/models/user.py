from dataclasses import dataclass
from typing import Literal, Optional

Role = Literal["USER", "ADMIN"]

@dataclass(frozen=True)
class User:
    id: str
    email: str
    full_name: str
    role: Role = "USER"
    photo_url: Optional[str] = None