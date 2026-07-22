from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_SECRET_KEY = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "sqlite+aiosqlite:///./data/fintrack.db"
    secret_key: str = DEFAULT_SECRET_KEY
    single_user_password_hash: str = ""
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    @model_validator(mode="after")
    def check_secret_key_in_production(self) -> Self:
        if not self.debug and self.secret_key == DEFAULT_SECRET_KEY:
            raise RuntimeError("SECRET_KEY must be set in production")
        return self


settings = Settings()
