from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, InvalidOperation

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%d-%m-%Y",
    "%d.%m.%Y",
    "%Y/%m/%d",
)

_REQUIRED_CANONICAL = {"posted_at", "amount", "description"}


class CSVParseError(Exception):
    def __init__(self, row: int, message: str) -> None:
        self.row = row
        super().__init__(f"Row {row}: {message}")


@dataclass
class ParsedRow:
    posted_at: date
    amount: Decimal
    currency: str
    description: str
    merchant: str | None = None
    external_id: str | None = None


@dataclass
class CSVAdapter:
    """Parse bank CSV exports into ParsedRow objects.

    column_map: maps CSV header -> canonical field name.
    default_currency: used when CSV has no currency column.
    """

    column_map: dict[str, str] = field(default_factory=dict)
    default_currency: str = "EUR"

    def parse(self, data: bytes | str) -> list[ParsedRow]:
        text = _decode(data)
        reader = csv.DictReader(io.StringIO(text))
        if reader.fieldnames is None:
            raise CSVParseError(0, "empty file or missing header")

        col_map = _build_col_map(list(reader.fieldnames), self.column_map)
        missing = _REQUIRED_CANONICAL - set(col_map.values())
        if missing:
            raise CSVParseError(0, f"missing required columns: {sorted(missing)}")

        rows: list[ParsedRow] = []
        for i, raw in enumerate(reader, start=2):
            rows.append(self._parse_row(i, raw, col_map))
        return rows

    def _parse_row(
        self, row_num: int, raw: dict[str, str | None], col_map: dict[str, str]
    ) -> ParsedRow:
        def get(canonical: str) -> str:
            csv_col = next(k for k, v in col_map.items() if v == canonical)
            return (raw.get(csv_col) or "").strip()

        def maybe(canonical: str) -> str | None:
            try:
                csv_col = next(k for k, v in col_map.items() if v == canonical)
                val = (raw.get(csv_col) or "").strip()
                return val or None
            except StopIteration:
                return None

        posted_at = _parse_date(row_num, get("posted_at"))
        amount = _parse_amount(row_num, get("amount"))

        currency_val = maybe("currency") or self.default_currency
        description = get("description")
        if not description:
            raise CSVParseError(row_num, "description is empty")

        return ParsedRow(
            posted_at=posted_at,
            amount=amount,
            currency=currency_val,
            description=description,
            merchant=maybe("merchant"),
            external_id=maybe("external_id"),
        )


def _decode(data: bytes | str) -> str:
    if isinstance(data, str):
        return data.lstrip("﻿")
    for enc in ("utf-8-sig", "utf-16", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError, ValueError:
            continue
    raise CSVParseError(0, "cannot decode file — unknown encoding")


def _build_col_map(headers: list[str], user_map: dict[str, str]) -> dict[str, str]:
    """Return {csv_header: canonical_name} merging auto-detect with user overrides."""
    _auto = {
        "date": "posted_at",
        "posted_at": "posted_at",
        "transaction date": "posted_at",
        "value date": "posted_at",
        "amount": "amount",
        "debit/credit": "amount",
        "description": "description",
        "memo": "description",
        "narrative": "description",
        "currency": "currency",
        "merchant": "merchant",
        "external_id": "external_id",
        "transaction id": "external_id",
        "reference": "external_id",
    }
    result: dict[str, str] = {}
    for h in headers:
        lower = h.lower().strip()
        if h in user_map:
            result[h] = user_map[h]
        elif lower in _auto:
            result[h] = _auto[lower]
    for csv_col, canonical in user_map.items():
        if csv_col in headers and csv_col not in result:
            result[csv_col] = canonical
    return result


def _parse_date(row: int, value: str) -> date:
    if not value:
        raise CSVParseError(row, "date is empty")
    for fmt in _DATE_FORMATS:
        try:
            from datetime import datetime

            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise CSVParseError(row, f"unrecognised date format: {value!r}")


def _parse_amount(row: int, value: str) -> Decimal:
    if not value:
        raise CSVParseError(row, "amount is empty")
    cleaned = re.sub(r"[€$£¥\s]", "", value)
    cleaned = cleaned.replace(",", ".")
    negative = cleaned.startswith("(") and cleaned.endswith(")")
    if negative:
        cleaned = "-" + cleaned[1:-1]
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        raise CSVParseError(row, f"cannot parse amount: {value!r}") from None
