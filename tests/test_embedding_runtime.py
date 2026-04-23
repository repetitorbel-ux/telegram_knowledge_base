from kb_bot.core.config import Settings
from kb_bot.services.embedding_providers import LocalHTTPEmbeddingProvider, OpenAIEmbeddingProvider
from kb_bot.services.embedding_runtime import build_embedding_provider, build_embedding_service


def _make_settings(**overrides) -> Settings:
    defaults = dict(
        telegram_bot_token="test-token",
        telegram_allowed_user_id=1,
        telegram_mode="polling",
        telegram_webhook_base_url=None,
        telegram_webhook_path="/telegram/webhook",
        telegram_webhook_secret_token=None,
        telegram_webhook_host="127.0.0.1",
        telegram_webhook_port=8081,
        telegram_webhook_drop_pending_updates=False,
        database_url="postgresql+asyncpg://u:p@127.0.0.1:5432/db",
        backup_dir="backups",
        pg_dump_bin="pg_dump",
        pg_restore_bin="pg_restore",
        restore_timeout_sec=1800,
        admin_api_enabled=False,
        admin_api_host="127.0.0.1",
        admin_api_port=8080,
        admin_api_token=None,
        admin_export_dir="exports",
        semantic_search_enabled=False,
        semantic_provider="openai",
        semantic_model="text-embedding-3-small",
        semantic_embedding_dim=1536,
        semantic_alpha=0.35,
        semantic_top_k_candidates=100,
        semantic_min_score=0.0,
        semantic_timeout_ms=3000,
        openai_api_key=None,
        openai_base_url=None,
        local_embedding_url=None,
    )
    defaults.update(overrides)
    return Settings.model_construct(**defaults)


def test_build_embedding_provider_openai_requires_key() -> None:
    settings = _make_settings(semantic_provider="openai", openai_api_key=None)
    assert build_embedding_provider(settings) is None


def test_build_embedding_provider_openai_success() -> None:
    settings = _make_settings(semantic_provider="openai", openai_api_key="sk-test")
    provider = build_embedding_provider(settings)
    assert isinstance(provider, OpenAIEmbeddingProvider)


def test_build_embedding_provider_local_requires_url() -> None:
    settings = _make_settings(semantic_provider="local", local_embedding_url=None)
    assert build_embedding_provider(settings) is None


def test_build_embedding_provider_local_success() -> None:
    settings = _make_settings(semantic_provider="local", local_embedding_url="http://127.0.0.1:11434/embed")
    provider = build_embedding_provider(settings)
    assert isinstance(provider, LocalHTTPEmbeddingProvider)


def test_build_embedding_service_disabled_returns_none() -> None:
    settings = _make_settings(semantic_search_enabled=False, openai_api_key="sk-test")
    service = build_embedding_service(session=object(), settings=settings)  # type: ignore[arg-type]
    assert service is None


def test_build_embedding_service_enabled_with_provider_returns_service() -> None:
    settings = _make_settings(semantic_search_enabled=True, openai_api_key="sk-test")
    service = build_embedding_service(session=object(), settings=settings)  # type: ignore[arg-type]
    assert service is not None

