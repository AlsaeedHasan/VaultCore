from uuid import UUID

from pydantic import BaseModel, ConfigDict

import utils


class Wallet(BaseModel):
    id: UUID
    user_id: UUID
    currency: utils.CurrencyEnum
    is_active: bool


class WalletCreate(BaseModel):
    user_id: UUID
    currency: utils.CurrencyEnum


class WalletResponse(Wallet):
    model_config = ConfigDict(from_attributes=True)
