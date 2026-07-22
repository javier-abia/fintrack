from fastapi import FastAPI

from fintrack_api.core.config import settings
from fintrack_api.routers import api_router

app = FastAPI(title="Fintrack API", version="0.1.0")

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
