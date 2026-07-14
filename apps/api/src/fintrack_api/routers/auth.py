from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from fintrack_api.core.config import settings
from fintrack_api.core.security import create_access_token, verify_password
from fintrack_api.schemas.auth import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    if not settings.single_user_password_hash or not verify_password(
        payload.password, settings.single_user_password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password",
        )
    token = create_access_token(subject="single-user")
    return TokenResponse(access_token=token)
