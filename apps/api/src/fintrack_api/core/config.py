from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "sqlite+aiosqlite:///./data/fintrack.db"
    secret_key: str = "change-me-in-production"
    single_user_password_hash: str = ""
    debug: bool = False


settings = Settings()
