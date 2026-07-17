from fastapi import APIRouter, Depends

from fintrack_api.core.deps import require_auth
from fintrack_api.routers import accounts, auth

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(accounts.router, dependencies=[Depends(require_auth)])
