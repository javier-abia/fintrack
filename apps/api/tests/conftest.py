from __future__ import annotations

import os

os.environ.setdefault("DEBUG", "true")  # tests may leave SECRET_KEY at its default

from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import fintrack_api.models  # noqa: F401,E402 — registers all ORM models with Base.metadata
from fintrack_api.core.config import settings  # noqa: E402
from fintrack_api.core.database import Base, get_db
from fintrack_api.core.security import hash_password
from fintrack_api.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
TEST_PASSWORD = "correct-horse-battery-staple"

_engine = create_async_engine(TEST_DB_URL, echo=False)
_session_factory = async_sessionmaker(_engine, expire_on_commit=False)
settings.single_user_password_hash = hash_password(TEST_PASSWORD)


@pytest.fixture(autouse=True, scope="function")
async def reset_db() -> AsyncGenerator[None]:
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    async with _session_factory() as session:
        yield session


@pytest.fixture
async def unauthenticated_client(
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient]:
    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def client(
    unauthenticated_client: AsyncClient,
) -> AsyncGenerator[AsyncClient]:
    login_res = await unauthenticated_client.post(
        "/api/v1/auth/login", json={"password": TEST_PASSWORD}
    )
    token = login_res.json()["access_token"]
    unauthenticated_client.headers["Authorization"] = f"Bearer {token}"
    yield unauthenticated_client
