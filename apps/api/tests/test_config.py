from __future__ import annotations

import pytest

from fintrack_api.core.config import Settings


def test_refuses_default_secret_key_in_production() -> None:
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        Settings(debug=False, secret_key="change-me-in-production")


def test_allows_default_secret_key_in_debug() -> None:
    Settings(debug=True, secret_key="change-me-in-production")


def test_allows_custom_secret_key_in_production() -> None:
    Settings(debug=False, secret_key="a-real-secret")
