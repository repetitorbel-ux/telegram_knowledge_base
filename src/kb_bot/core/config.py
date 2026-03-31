from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_user_id: int = Field(alias="TELEGRAM_ALLOWED_USER_ID")
    database_url: str = Field(alias="DATABASE_URL")
    backup_dir: str = Field(default="backups", alias="BACKUP_DIR")
    pg_dump_bin: str = Field(default="pg_dump", alias="PG_DUMP_BIN")
    pg_restore_bin: str = Field(default="pg_restore", alias="PG_RESTORE_BIN")
    restore_timeout_sec: int = Field(default=1800, alias="RESTORE_TIMEOUT_SEC")


@lru_cache
def get_settings() -> Settings:
    return Settings()
