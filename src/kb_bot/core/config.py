from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_allowed_user_id: int = Field(alias="TELEGRAM_ALLOWED_USER_ID")
    telegram_mode: str = Field(default="polling", alias="TELEGRAM_MODE")
    telegram_webhook_base_url: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_BASE_URL")
    telegram_webhook_path: str = Field(default="/telegram/webhook", alias="TELEGRAM_WEBHOOK_PATH")
    telegram_webhook_secret_token: str | None = Field(default=None, alias="TELEGRAM_WEBHOOK_SECRET_TOKEN")
    telegram_webhook_host: str = Field(default="127.0.0.1", alias="TELEGRAM_WEBHOOK_HOST")
    telegram_webhook_port: int = Field(default=8081, alias="TELEGRAM_WEBHOOK_PORT")
    telegram_webhook_drop_pending_updates: bool = Field(
        default=False,
        alias="TELEGRAM_WEBHOOK_DROP_PENDING_UPDATES",
    )
    database_url: str = Field(alias="DATABASE_URL")
    backup_dir: str = Field(default="backups", alias="BACKUP_DIR")
    pg_dump_bin: str = Field(default="pg_dump", alias="PG_DUMP_BIN")
    pg_restore_bin: str = Field(default="pg_restore", alias="PG_RESTORE_BIN")
    restore_timeout_sec: int = Field(default=1800, alias="RESTORE_TIMEOUT_SEC")
    admin_api_enabled: bool = Field(default=False, alias="ADMIN_API_ENABLED")
    admin_api_host: str = Field(default="127.0.0.1", alias="ADMIN_API_HOST")
    admin_api_port: int = Field(default=8080, alias="ADMIN_API_PORT")
    admin_api_token: str | None = Field(default=None, alias="ADMIN_API_TOKEN")
    admin_export_dir: str = Field(default="exports", alias="ADMIN_EXPORT_DIR")
    semantic_search_enabled: bool = Field(default=False, alias="SEMANTIC_SEARCH_ENABLED")
    semantic_provider: str = Field(default="openai", alias="SEMANTIC_PROVIDER")
    semantic_model: str = Field(default="text-embedding-3-small", alias="SEMANTIC_MODEL")
    semantic_embedding_dim: int = Field(default=1536, alias="SEMANTIC_EMBEDDING_DIM")
    semantic_alpha: float = Field(default=0.35, alias="SEMANTIC_ALPHA")
    semantic_top_k_candidates: int = Field(default=100, alias="SEMANTIC_TOP_K_CANDIDATES")
    semantic_min_score: float = Field(default=0.0, alias="SEMANTIC_MIN_SCORE")
    semantic_timeout_ms: int = Field(default=3000, alias="SEMANTIC_TIMEOUT_MS")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: str | None = Field(default=None, alias="OPENAI_BASE_URL")
    local_embedding_url: str | None = Field(default=None, alias="LOCAL_EMBEDDING_URL")


@lru_cache
def get_settings() -> Settings:
    return Settings()
