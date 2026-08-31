from pydantic import BaseModel, Field
from typing import Literal

class TransactionIn(BaseModel):
    transaction_id: str | None = None
    amount: float = Field(gt=0, le=2_000_000)
    hour: int = Field(ge=0, le=23)
    customer_age_days: int = Field(ge=0)
    transactions_24h: int = Field(ge=0, le=1000)
    failed_attempts_24h: int = Field(ge=0, le=100)
    distance_km: float = Field(ge=0, le=50000)
    device_trust: float = Field(ge=0, le=1)
    is_international: bool = False
    is_new_device: bool = False
    payment_method: Literal['card', 'upi', 'wallet', 'netbanking'] = 'card'

class ActionIn(BaseModel):
    action: Literal['approve', 'step_up_verify', 'hold_review', 'block_refund']
    note: str = Field(default='', max_length=500)
