from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from utils import TransactionStatus, TransactionType


class TransactionBase(BaseModel):
    amount: Decimal = Field(..., gt=0, description="Amount must be positive")
    description: Optional[str] = None


class DepositRequest(TransactionBase):
    currency: str


class TransferRequest(TransactionBase):
    receiver_email: str
    currency: str


class WithdrawRequest(TransactionBase):
    currency: str


class TransactionResponse(BaseModel):
    id: UUID
    amount: Decimal
    balance_after: Decimal
    type: TransactionType
    status: TransactionStatus
    created_at: datetime
    reference_id: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
