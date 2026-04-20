import types
import uuid
from collections.abc import Coroutine
from datetime import datetime, UTC
from unittest.mock import AsyncMock

from kb_bot.domain.errors import EntryNotFoundError
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


def test_related_returns_scored_items() -> None:
    source_entry_id = uuid.uuid4()
    source_topic_id = uuid.uuid4()
    tag_shared = uuid.uuid4()

    source_entry = types.SimpleNamespace(
        id=source_entry_id,
        title="PostgreSQL backup strategy",
        description="backup retention and restore drills",
        notes="weekly backup checks",
        primary_topic_id=source_topic_id,
    )
    candidate_entry = types.SimpleNamespace(
        id=uuid.uuid4(),
        title="PostgreSQL restore strategy",
        description="restore drills and backup plans",
        notes="daily checks",
        primary_topic_id=source_topic_id,
        saved_date=datetime.now(UTC),
    )
    repo = types.SimpleNamespace(
        get=AsyncMock(return_value=source_entry),
        get_entry_tag_ids=AsyncMock(return_value={tag_shared}),
        get_related_candidates=AsyncMock(return_value=[(candidate_entry, "New", "Infrastructure")]),
        get_tags_for_entries=AsyncMock(return_value={candidate_entry.id: {tag_shared}}),
    )
    service = SearchService(repo)

    result = run_coroutine(service.related(source_entry_id, limit=10, offset=0))

    assert len(result) == 1
    assert result[0].id == candidate_entry.id
    assert result[0].same_topic is True
    assert result[0].shared_tags_count == 1
    assert result[0].score >= 8
    repo.get_related_candidates.assert_awaited_once()


def test_related_raises_when_source_entry_missing() -> None:
    source_entry_id = uuid.uuid4()
    repo = types.SimpleNamespace(get=AsyncMock(return_value=None))
    service = SearchService(repo)

    coroutine = service.related(source_entry_id, limit=10, offset=0)
    try:
        run_coroutine(coroutine)
        raised = False
    except EntryNotFoundError:
        raised = True

    assert raised is True
