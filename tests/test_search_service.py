import types
import uuid
from collections.abc import Coroutine
from datetime import datetime, UTC
from unittest.mock import AsyncMock

from kb_bot.services.search_service import SearchService


def run_coroutine(coroutine: Coroutine[object, object, object]) -> object:
    while True:
        try:
            coroutine.send(None)
        except StopIteration as done:
            return done.value


def test_search_service_uses_offset_for_pagination() -> None:
    entry = types.SimpleNamespace(
        id=uuid.uuid4(),
        title="PostgreSQL backup guide",
        original_url="https://example.com/pg",
        normalized_url="https://example.com/pg",
        primary_topic_id=uuid.uuid4(),
        notes="backup strategy",
        saved_date=datetime.now(UTC),
    )
    repo = types.SimpleNamespace(search=AsyncMock(return_value=[(entry, "New")]))
    service = SearchService(repo)

    result = run_coroutine(service.search("PostgreSQL", limit=11, offset=10))

    assert len(result) == 1
    assert result[0].id == entry.id
    assert result[0].status_name == "New"
    repo.search.assert_awaited_once_with("PostgreSQL", limit=11, offset=10)


def test_search_service_blank_query_returns_empty() -> None:
    repo = types.SimpleNamespace(search=AsyncMock())
    service = SearchService(repo)

    result = run_coroutine(service.search("   ", limit=11, offset=10))

    assert result == []
    repo.search.assert_not_awaited()
