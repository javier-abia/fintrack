from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fintrack_api.adapters.csv_generic import CSVAdapter, CSVParseError
from fintrack_api.core.database import get_db
from fintrack_api.models.account import Account
from fintrack_api.models.transaction import CategorySource, Transaction
from fintrack_api.schemas.account import AccountCreate, AccountRead, AccountUpdate
from fintrack_api.schemas.transaction import CsvUploadResult

router = APIRouter(prefix="/accounts", tags=["accounts"])

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/", response_model=list[AccountRead])
async def list_accounts(db: DbSession) -> list[AccountRead]:
    result = await db.execute(
        select(Account, func.coalesce(func.sum(Transaction.amount), 0))
        .outerjoin(Transaction, Transaction.account_id == Account.id)
        .where(Account.is_active.is_(True))
        .group_by(Account.id)
    )
    return [
        AccountRead.model_validate(account).model_copy(update={"balance": balance})
        for account, balance in result.all()
    ]


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


@router.post("/{account_id}/transactions/upload-csv", response_model=CsvUploadResult)
async def upload_transactions_csv(
    account_id: int, db: DbSession, file: Annotated[UploadFile, File()]
) -> CsvUploadResult:
    account = await db.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    contents = await file.read()
    try:
        rows = CSVAdapter(default_currency=account.currency).parse(contents)
    except CSVParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    db.add_all(
        Transaction(
            account_id=account.id,
            posted_at=row.posted_at,
            amount=row.amount,
            currency=row.currency,
            description=row.description,
            merchant=row.merchant,
            external_id=row.external_id,
            category_source=CategorySource.none,
        )
        for row in rows
    )
    await db.commit()
    return CsvUploadResult(imported=len(rows))
