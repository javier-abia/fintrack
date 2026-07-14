from __future__ import annotations

from httpx import AsyncClient

from tests.conftest import TEST_PASSWORD


async def test_login_success(unauthenticated_client: AsyncClient) -> None:
    res = await unauthenticated_client.post(
        "/api/v1/auth/login", json={"password": TEST_PASSWORD}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]


async def test_login_wrong_password(unauthenticated_client: AsyncClient) -> None:
    res = await unauthenticated_client.post(
        "/api/v1/auth/login", json={"password": "wrong"}
    )
    assert res.status_code == 401


async def test_protected_route_requires_token(
    unauthenticated_client: AsyncClient,
) -> None:
    res = await unauthenticated_client.get("/api/v1/accounts/")
    assert res.status_code == 401


async def test_protected_route_rejects_invalid_token(
    unauthenticated_client: AsyncClient,
) -> None:
    unauthenticated_client.headers["Authorization"] = "Bearer not-a-real-token"
    res = await unauthenticated_client.get("/api/v1/accounts/")
    assert res.status_code == 401


async def test_health_does_not_require_auth(
    unauthenticated_client: AsyncClient,
) -> None:
    res = await unauthenticated_client.get("/health")
    assert res.status_code == 200
