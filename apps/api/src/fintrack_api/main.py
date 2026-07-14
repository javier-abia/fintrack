from fastapi import Depends, FastAPI

from fintrack_api.core.deps import require_auth
from fintrack_api.routers import accounts, auth

app = FastAPI(title="Fintrack API", version="0.1.0")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(
    accounts.router, prefix="/api/v1", dependencies=[Depends(require_auth)]
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
