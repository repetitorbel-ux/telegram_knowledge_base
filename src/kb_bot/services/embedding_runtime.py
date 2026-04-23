from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from kb_bot.core.config import Settings
from kb_bot.db.repositories.embeddings import EmbeddingsRepository
from kb_bot.services.embedding_providers import LocalHTTPEmbeddingProvider, OpenAIEmbeddingProvider
from kb_bot.services.embedding_service import EmbeddingService, EmbeddingServiceConfig, EmbeddingProvider


def build_embedding_provider(settings: Settings) -> EmbeddingProvider | None:
    provider_name = settings.semantic_provider.strip().lower()

    if provider_name == "openai":
        if not settings.openai_api_key:
            return None
        return OpenAIEmbeddingProvider(
            api_key=settings.openai_api_key,
            model=settings.semantic_model,
            base_url=settings.openai_base_url,
            timeout_ms=settings.semantic_timeout_ms,
        )

    if provider_name == "local":
        if not settings.local_embedding_url:
            return None
        return LocalHTTPEmbeddingProvider(
            url=settings.local_embedding_url,
            model=settings.semantic_model,
            timeout_ms=settings.semantic_timeout_ms,
        )

    return None


def build_embedding_service(session: AsyncSession, settings: Settings) -> EmbeddingService | None:
    if not settings.semantic_search_enabled:
        return None

    provider = build_embedding_provider(settings)
    if provider is None:
        return None

    return EmbeddingService(
        session=session,
        embeddings_repo=EmbeddingsRepository(session),
        provider=provider,
        config=EmbeddingServiceConfig(
            provider_name=settings.semantic_provider,
            model_name=settings.semantic_model,
            embedding_dim=settings.semantic_embedding_dim,
        ),
    )

