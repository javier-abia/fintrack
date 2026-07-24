from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from fintrack_api.models.account import AccountKind


class AccountBase(BaseModel):
    name: str
    kind: AccountKind
    institution: str
    currency: str
    external_ref: str | None = None
    is_active: bool = True


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: str | None = None
    kind: AccountKind | None = None
    institution: str | None = None
    currency: str | None = None
    external_ref: str | None = None
    is_active: bool | None = None


class AccountRead(AccountBase):
    model_config = {"from_attributes": True}

    id: int
    created_at: datetime
    balance: Decimal = Decimal("0")
