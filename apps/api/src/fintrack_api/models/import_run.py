from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import JSON, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from fintrack_api.core.database import Base


class ImportRunStatus(enum.Enum):
    success = "success"
    partial = "partial"
    failed = "failed"


class ImportRun(Base):
    __tablename__ = "import_run"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("account.id"))
    filename: Mapped[str] = mapped_column(String)
    file_hash: Mapped[str] = mapped_column(String)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    inserted_count: Mapped[int] = mapped_column(Integer, default=0)
    skipped_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(default=None)
    status: Mapped[ImportRunStatus] = mapped_column(
        Enum(ImportRunStatus, native_enum=False)
    )
    error_log_json: Mapped[dict | None] = mapped_column(JSON, default=None)
