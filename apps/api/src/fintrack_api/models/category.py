from __future__ import annotations

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from fintrack_api.core.database import Base


class Category(Base):
    __tablename__ = "category"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    parent_id: Mapped[int | None] = mapped_column(default=None)
    color: Mapped[str] = mapped_column(String(7), default="#888888")
    is_income: Mapped[bool] = mapped_column(Boolean, default=False)
