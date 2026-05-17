from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from fintrack_api.adapters.csv_generic import CSVAdapter, CSVParseError

VALID_CSV = """\
date,amount,description,currency
2024-01-15,-42.50,Supermarket,EUR
2024-02-01,1000.00,Salary,EUR
"""

BOM_CSV = "﻿" + VALID_CSV


def test_parse_valid_csv() -> None:
    rows = CSVAdapter().parse(VALID_CSV)
    assert len(rows) == 2
    assert rows[0].posted_at == date(2024, 1, 15)
    assert rows[0].amount == Decimal("-42.50")
    assert rows[0].currency == "EUR"
    assert rows[0].description == "Supermarket"


def test_parse_bom_csv() -> None:
    rows = CSVAdapter().parse(BOM_CSV)
    assert len(rows) == 2


def test_parse_bom_bytes() -> None:
    rows = CSVAdapter().parse(VALID_CSV.encode("utf-8-sig"))
    assert len(rows) == 2


def test_date_formats() -> None:
    for date_str, expected in [
        ("15/01/2024", date(2024, 1, 15)),
        ("01/15/2024", date(2024, 1, 15)),
        ("15-01-2024", date(2024, 1, 15)),
        ("15.01.2024", date(2024, 1, 15)),
        ("2024/01/15", date(2024, 1, 15)),
    ]:
        csv = f"date,amount,description\n{date_str},10.00,Test\n"
        rows = CSVAdapter().parse(csv)
        assert rows[0].posted_at == expected, date_str


def test_amount_with_currency_symbol() -> None:
    csv = "date,amount,description\n2024-01-01,€ 1.234,50,Test\n"
    rows = CSVAdapter().parse(csv)
    assert rows[0].amount == Decimal("1.234")


def test_amount_parentheses_negative() -> None:
    csv = "date,amount,description\n2024-01-01,(99.99),Test\n"
    rows = CSVAdapter().parse(csv)
    assert rows[0].amount == Decimal("-99.99")


def test_amount_comma_decimal() -> None:
    csv = "date,amount,description\n2024-01-01,1.234,56,Test\n"
    rows = CSVAdapter().parse(csv)
    assert rows[0].amount == Decimal("1.234")


def test_default_currency_used_when_no_column() -> None:
    csv = "date,amount,description\n2024-01-01,10.00,Test\n"
    rows = CSVAdapter(default_currency="USD").parse(csv)
    assert rows[0].currency == "USD"


def test_missing_required_column_raises() -> None:
    csv = "date,amount\n2024-01-01,10.00\n"
    with pytest.raises(CSVParseError) as exc_info:
        CSVAdapter().parse(csv)
    assert "description" in str(exc_info.value)
    assert exc_info.value.row == 0


def test_column_remapping() -> None:
    csv = "Booking Date,Debit/Credit,Memo\n2024-01-15,-42.50,Supermarket\n"
    adapter = CSVAdapter(
        column_map={
            "Booking Date": "posted_at",
            "Debit/Credit": "amount",
            "Memo": "description",
        }
    )
    rows = adapter.parse(csv)
    assert rows[0].posted_at == date(2024, 1, 15)
    assert rows[0].amount == Decimal("-42.50")
    assert rows[0].description == "Supermarket"


def test_invalid_date_raises() -> None:
    csv = "date,amount,description\nnot-a-date,10.00,Test\n"
    with pytest.raises(CSVParseError) as exc_info:
        CSVAdapter().parse(csv)
    assert "date" in str(exc_info.value).lower()
    assert exc_info.value.row == 2


def test_invalid_amount_raises() -> None:
    csv = "date,amount,description\n2024-01-01,not-a-number,Test\n"
    with pytest.raises(CSVParseError) as exc_info:
        CSVAdapter().parse(csv)
    assert "amount" in str(exc_info.value).lower()
    assert exc_info.value.row == 2


def test_empty_file_raises() -> None:
    with pytest.raises(CSVParseError):
        CSVAdapter().parse("")
