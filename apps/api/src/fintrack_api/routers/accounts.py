from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fintrack_api.core.database import get_db
from fintrack_api.models.account import Account
from fintrack_api.schemas.account import AccountCreate, AccountRead, AccountUpdate

router = APIRouter(prefix="/accounts", tags=["accounts"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[AccountRead])
async def list_accounts(db: DbSession) -> list[Account]:
    result = await db.execute(select(Account).where(Account.is_active.is_(True)))
    return list(result.scalars().all())


@router.post("/", response_model=AccountRead, status_code=201)
async def create_account(payload: AccountCreate, db: DbSession) -> Account:
    account = Account(**payload.model_dump())
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(account_id: int, db: DbSession) -> Account:
    account = await db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/{account_id}", response_model=AccountRead)
async def update_account(
    account_id: int, payload: AccountUpdate, db: DbSession
) -> Account:
    account = await db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(account, field, value)
    await db.commit()
    await db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=204)
async def delete_account(account_id: int, db: DbSession) -> None:
    account = await db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    account.is_active = False
    await db.commit()
