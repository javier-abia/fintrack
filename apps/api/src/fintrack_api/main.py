from fastapi import FastAPI

from fintrack_api.routers import accounts

app = FastAPI(title="Fintrack API", version="0.1.0")

app.include_router(accounts.router, prefix="/api/v1")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
