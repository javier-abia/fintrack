from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me-in-production"

# apps/api/src/fintrack_api/core/config.py -> apps/api, and repo root.
API_DIR = Path(__file__).resolve().parents[3]
PROJECT_ROOT = Path(__file__).resolve().parents[5]

_RELATIVE_SQLITE_PREFIX = "sqlite+aiosqlite:///./"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=API_DIR / ".env")

    database_url: str = "sqlite+aiosqlite:///./data/fintrack.db"
    secret_key: str = DEFAULT_SECRET_KEY
    single_user_password_hash: str = ""
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    @model_validator(mode="after")
    def resolve_relative_sqlite_path(self) -> Self:
        # A relative sqlite URL is otherwise resolved against the process's
        # cwd, so it silently points at the wrong file if uvicorn/alembic
        # aren't launched from the repo root. Anchor it here instead.
        if self.database_url.startswith(_RELATIVE_SQLITE_PREFIX):
            relative_path = self.database_url.removeprefix(_RELATIVE_SQLITE_PREFIX)
            absolute_path = (PROJECT_ROOT / relative_path).resolve()
            self.database_url = f"sqlite+aiosqlite:///{absolute_path}"
        return self

    @model_validator(mode="after")
    def check_secret_key_in_production(self) -> Self:
        if not self.debug and self.secret_key == DEFAULT_SECRET_KEY:
            raise RuntimeError("SECRET_KEY must be set in production")
        return self


settings = Settings()
