from __future__ import annotations

import enum
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fintrack_api.core.database import Base

if TYPE_CHECKING:
    from fintrack_api.models.account import Account


class CategorySource(enum.Enum):
    rule = "rule"
    manual = "manual"
    none = "none"


class Transaction(Base):
    __tablename__ = "transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    posted_at: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[str] = mapped_column(String(3))
    description: Mapped[str] = mapped_column(String)
    merchant: Mapped[str | None] = mapped_column(String)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("category.id", use_alter=True, name="fk_transaction_category_id")
    )
    category_source: Mapped[CategorySource] = mapped_column(
        Enum(CategorySource, native_enum=False)
    )
    external_id: Mapped[str | None] = mapped_column(String)
    import_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("import_run.id", use_alter=True, name="fk_transaction_import_run_id")
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    account: Mapped[Account] = relationship(back_populates="transactions")
