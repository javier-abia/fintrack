from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fintrack_api.core.database import Base

if TYPE_CHECKING:
    from fintrack_api.models.transaction import Transaction


class AccountKind(enum.Enum):
    checking = "checking"
    savings = "savings"
    credit_card = "credit_card"
    crypto = "crypto"
    cash = "cash"
    investment = "investment"


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String)
    kind: Mapped[AccountKind] = mapped_column(Enum(AccountKind, native_enum=False))
    institution: Mapped[str] = mapped_column(String)
    currency: Mapped[str] = mapped_column(String(3))
    external_ref: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    transactions: Mapped[list[Transaction]] = relationship(back_populates="account")
