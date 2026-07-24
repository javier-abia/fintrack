from __future__ import annotations

from pydantic import BaseModel


class CsvUploadResult(BaseModel):
    imported: int
