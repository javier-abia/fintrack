from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.fixture
def account_payload() -> dict[str, object]:
    return {
        "name": "ING Checking",
        "kind": "checking",
        "institution": "ING",
        "currency": "EUR",
        "external_ref": None,
        "is_active": True,
    }


async def test_create_account(
    client: AsyncClient, account_payload: dict[str, object]
) -> None:
    res = await client.post("/api/v1/accounts/", json=account_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["id"] == 1
    assert data["name"] == "ING Checking"
    assert data["kind"] == "checking"
    assert data["currency"] == "EUR"


async def test_list_accounts(
    client: AsyncClient, account_payload: dict[str, object]
) -> None:
    await client.post("/api/v1/accounts/", json=account_payload)
    await client.post("/api/v1/accounts/", json={**account_payload, "name": "Revolut"})

    res = await client.get("/api/v1/accounts/")
    assert res.status_code == 200
    assert len(res.json()) == 2


async def test_list_accounts_excludes_inactive(
    client: AsyncClient, account_payload: dict[str, object]
) -> None:
    create_res = await client.post("/api/v1/accounts/", json=account_payload)
    account_id = create_res.json()["id"]

    await client.delete(f"/api/v1/accounts/{account_id}")

    res = await client.get("/api/v1/accounts/")
    assert res.status_code == 200
    assert res.json() == []


async def test_get_account(
    client: AsyncClient, account_payload: dict[str, object]
) -> None:
    create_res = await client.post("/api/v1/accounts/", json=account_payload)
    account_id = create_res.json()["id"]

    res = await client.get(f"/api/v1/accounts/{account_id}")
    assert res.status_code == 200
    assert res.json()["id"] == account_id


async def test_get_account_not_found(client: AsyncClient) -> None:
    res = await client.get("/api/v1/accounts/9999")
    assert res.status_code == 404


async def test_update_account(
    client: AsyncClient, account_payload: dict[str, object]
) -> None:
    create_res = await client.post("/api/v1/accounts/", json=account_payload)
    account_id = create_res.json()["id"]

    res = await client.patch(
        f"/api/v1/accounts/{account_id}", json={"name": "ING Savings"}
    )
    assert res.status_code == 200
    assert res.json()["name"] == "ING Savings"


async def test_update_account_not_found(client: AsyncClient) -> None:
    res = await client.patch("/api/v1/accounts/9999", json={"name": "Ghost"})
    assert res.status_code == 404


async def test_delete_account_soft(
    client: AsyncClient, account_payload: dict[str, object]
) -> None:
    create_res = await client.post("/api/v1/accounts/", json=account_payload)
    account_id = create_res.json()["id"]

    res = await client.delete(f"/api/v1/accounts/{account_id}")
    assert res.status_code == 204

    get_res = await client.get(f"/api/v1/accounts/{account_id}")
    assert get_res.json()["is_active"] is False


async def test_upload_csv_imports_transactions(
    client: AsyncClient, account_payload: dict[str, object]
) -> None:
    create_res = await client.post("/api/v1/accounts/", json=account_payload)
    account_id = create_res.json()["id"]

    csv_content = (
        "date,amount,description\n"
        "2024-01-15,-42.50,Supermarket\n"
        "2024-02-01,1000.00,Salary\n"
    )
    res = await client.post(
        f"/api/v1/accounts/{account_id}/transactions/upload-csv",
        files={"file": ("transactions.csv", csv_content, "text/csv")},
    )
    assert res.status_code == 200
    assert res.json() == {"imported": 2}


async def test_upload_csv_malformed_returns_400(
    client: AsyncClient, account_payload: dict[str, object]
) -> None:
    create_res = await client.post("/api/v1/accounts/", json=account_payload)
    account_id = create_res.json()["id"]

    csv_content = "date,amount\n2024-01-15,-42.50\n"
    res = await client.post(
        f"/api/v1/accounts/{account_id}/transactions/upload-csv",
        files={"file": ("transactions.csv", csv_content, "text/csv")},
    )
    assert res.status_code == 400


async def test_list_accounts_includes_balance(
    client: AsyncClient, account_payload: dict[str, object]
) -> None:
    create_res = await client.post("/api/v1/accounts/", json=account_payload)
    account_id = create_res.json()["id"]

    csv_content = (
        "date,amount,description\n2024-01-15,-42.50,Rent\n2024-02-01,1000.00,Salary\n"
    )
    await client.post(
        f"/api/v1/accounts/{account_id}/transactions/upload-csv",
        files={"file": ("transactions.csv", csv_content, "text/csv")},
    )

    res = await client.get("/api/v1/accounts/")
    assert res.status_code == 200
    assert res.json()[0]["balance"] == "957.50"


async def test_upload_csv_account_not_found(client: AsyncClient) -> None:
    csv_content = "date,amount,description\n2024-01-15,-42.50,Supermarket\n"
    res = await client.post(
        "/api/v1/accounts/9999/transactions/upload-csv",
        files={"file": ("transactions.csv", csv_content, "text/csv")},
    )
    assert res.status_code == 404
