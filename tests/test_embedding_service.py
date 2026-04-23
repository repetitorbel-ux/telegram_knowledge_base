import types
import uuid
from collections.abc import Coroutine
from unittest.mock import AsyncMock

from kb_bot.services.embedding_service import EmbeddingService, EmbeddingServiceConfig


def run_coroutine(coroutine: Coroutine[object, object, object]) -> object:
    while True:
        try:
            coroutine.send(None)
        except StopIteration as done:
            return done.value


def _make_entry(
    title: str = "PostgreSQL guide",
    description: str | None = "backup and restore",
    notes: str | None = "weekly checks",
    normalized_url: str | None = "https://example.com",
) -> types.SimpleNamespace:
    return types.SimpleNamespace(
        id=uuid.uuid4(),
        title=title,
        description=description,
        notes=notes,
        normalized_url=normalized_url,
    )


def test_upsert_for_entry_persists_embedding_and_commits() -> None:
    entry = _make_entry()
    session = types.SimpleNamespace(commit=AsyncMock())
    repo = types.SimpleNamespace(
        get_embedding_row=AsyncMock(return_value=None),
        upsert_embedding=AsyncMock(),
    )
    provider = types.SimpleNamespace(embed=AsyncMock(return_value=[0.1, 0.2, 0.3]))
    service = EmbeddingService(
        session=session,  # type: ignore[arg-type]
        embeddings_repo=repo,  # type: ignore[arg-type]
        provider=provider,  # type: ignore[arg-type]
        config=EmbeddingServiceConfig(
            provider_name="openai",
            model_name="test-model",
            embedding_dim=3,
        ),
    )

    result = run_coroutine(service.upsert_for_entry(entry))  # type: ignore[arg-type]

    assert result is True
    provider.embed.assert_awaited_once()
    repo.upsert_embedding.assert_awaited_once()
    session.commit.assert_awaited_once()


def test_upsert_for_entry_skips_empty_payload() -> None:
    entry = _make_entry(title="", description=None, notes=None, normalized_url=None)
    session = types.SimpleNamespace(commit=AsyncMock())
    repo = types.SimpleNamespace(
        get_embedding_row=AsyncMock(return_value=None),
        upsert_embedding=AsyncMock(),
    )
    provider = types.SimpleNamespace(embed=AsyncMock())
    service = EmbeddingService(
        session=session,  # type: ignore[arg-type]
        embeddings_repo=repo,  # type: ignore[arg-type]
        provider=provider,  # type: ignore[arg-type]
        config=EmbeddingServiceConfig(
            provider_name="openai",
            model_name="test-model",
            embedding_dim=3,
        ),
    )

    result = run_coroutine(service.upsert_for_entry(entry))  # type: ignore[arg-type]

    assert result is False
    provider.embed.assert_not_awaited()
    repo.upsert_embedding.assert_not_awaited()
    session.commit.assert_not_awaited()


def test_upsert_for_entry_validates_embedding_dimension() -> None:
    entry = _make_entry()
    session = types.SimpleNamespace(commit=AsyncMock())
    repo = types.SimpleNamespace(
        get_embedding_row=AsyncMock(return_value=None),
        upsert_embedding=AsyncMock(),
    )
    provider = types.SimpleNamespace(embed=AsyncMock(return_value=[0.1, 0.2]))
    service = EmbeddingService(
        session=session,  # type: ignore[arg-type]
        embeddings_repo=repo,  # type: ignore[arg-type]
        provider=provider,  # type: ignore[arg-type]
        config=EmbeddingServiceConfig(
            provider_name="openai",
            model_name="test-model",
            embedding_dim=3,
        ),
    )

    raised = False
    try:
        run_coroutine(service.upsert_for_entry(entry))  # type: ignore[arg-type]
    except ValueError:
        raised = True

    assert raised is True
    repo.upsert_embedding.assert_not_awaited()
    session.commit.assert_not_awaited()


def test_upsert_for_entry_skips_when_hash_and_provider_model_match() -> None:
    entry = _make_entry()
    session = types.SimpleNamespace(commit=AsyncMock())
    repo = types.SimpleNamespace(
        get_embedding_row=AsyncMock(
            return_value={
                "provider": "openai",
                "model": "test-model",
                "content_hash": EmbeddingService.compute_content_hash(entry),  # type: ignore[arg-type]
            }
        ),
        upsert_embedding=AsyncMock(),
    )
    provider = types.SimpleNamespace(embed=AsyncMock())
    service = EmbeddingService(
        session=session,  # type: ignore[arg-type]
        embeddings_repo=repo,  # type: ignore[arg-type]
        provider=provider,  # type: ignore[arg-type]
        config=EmbeddingServiceConfig(
            provider_name="openai",
            model_name="test-model",
            embedding_dim=3,
        ),
    )

    result = run_coroutine(service.upsert_for_entry(entry))  # type: ignore[arg-type]

    assert result is False
    provider.embed.assert_not_awaited()
    repo.upsert_embedding.assert_not_awaited()
    session.commit.assert_not_awaited()


def test_compute_content_hash_is_stable_for_same_content() -> None:
    entry_a = _make_entry()
    entry_b = types.SimpleNamespace(
        id=uuid.uuid4(),
        title=entry_a.title,
        description=entry_a.description,
        notes=entry_a.notes,
        normalized_url=entry_a.normalized_url,
    )

    hash_a = EmbeddingService.compute_content_hash(entry_a)  # type: ignore[arg-type]
    hash_b = EmbeddingService.compute_content_hash(entry_b)  # type: ignore[arg-type]

    assert hash_a == hash_b


def test_upsert_for_entry_retries_with_shorter_payload_on_context_error() -> None:
    entry = _make_entry(title="A" * 4000, description="B" * 4000, notes="C" * 4000, normalized_url=None)
    session = types.SimpleNamespace(commit=AsyncMock())
    repo = types.SimpleNamespace(
        get_embedding_row=AsyncMock(return_value=None),
        upsert_embedding=AsyncMock(),
    )
    provider = types.SimpleNamespace(
        embed=AsyncMock(side_effect=[RuntimeError("input length exceeds the context length"), [0.1, 0.2, 0.3]])
    )
    service = EmbeddingService(
        session=session,  # type: ignore[arg-type]
        embeddings_repo=repo,  # type: ignore[arg-type]
        provider=provider,  # type: ignore[arg-type]
        config=EmbeddingServiceConfig(
            provider_name="local",
            model_name="nomic-embed-text",
            embedding_dim=3,
        ),
    )

    result = run_coroutine(service.upsert_for_entry(entry))  # type: ignore[arg-type]

    assert result is True
    assert provider.embed.await_count == 2
    session.commit.assert_awaited_once()
