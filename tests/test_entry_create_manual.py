import types
import uuid
from collections.abc import Coroutine
from unittest.mock import AsyncMock

import pytest

from kb_bot.domain.errors import DuplicateEntryError, EntryNotFoundError, TopicNotFoundError
from kb_bot.services.entry_service import CreateManualEntryPayload, EntryService


def run_coroutine(coroutine: Coroutine[object, object, object]) -> object:
    while True:
        try:
            coroutine.send(None)
        except StopIteration as done:
            return done.value


def test_create_manual_success() -> None:
    topic_id = uuid.uuid4()
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(exists_by_dedup_hash=AsyncMock(return_value=False), create=AsyncMock())
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=types.SimpleNamespace(id=topic_id)))
    statuses_repo = types.SimpleNamespace(
        get_by_code=AsyncMock(return_value=types.SimpleNamespace(id=uuid.uuid4(), display_name="New")),
        get_by_display_name=AsyncMock(return_value=types.SimpleNamespace(id=uuid.uuid4(), display_name="New"))
    )

    service = EntryService(session, entries_repo, topics_repo, statuses_repo)
    payload = CreateManualEntryPayload(title=" Entry ", primary_topic_id=topic_id, original_url="https://x.com")

    result = run_coroutine(service.create_manual(payload))

    assert result.title == "Entry"
    assert result.original_url == "https://x.com"
    assert result.normalized_url == "https://x.com/"
    assert result.primary_topic_id == topic_id
    assert result.status_name == "New"

    topics_repo.get.assert_awaited_once_with(topic_id)
    entries_repo.exists_by_dedup_hash.assert_awaited_once()
    statuses_repo.get_by_code.assert_awaited_once_with("NEW")
    statuses_repo.get_by_display_name.assert_not_awaited()
    entries_repo.create.assert_awaited_once()
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once()


def test_create_manual_duplicate() -> None:
    topic_id = uuid.uuid4()
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(exists_by_dedup_hash=AsyncMock(return_value=True), create=AsyncMock())
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=types.SimpleNamespace(id=topic_id)))
    statuses_repo = types.SimpleNamespace(get_by_code=AsyncMock(), get_by_display_name=AsyncMock())
    service = EntryService(session, entries_repo, topics_repo, statuses_repo)
    payload = CreateManualEntryPayload(title="Entry", primary_topic_id=topic_id, original_url="https://x.com")

    with pytest.raises(DuplicateEntryError):
        run_coroutine(service.create_manual(payload))

    entries_repo.create.assert_not_awaited()
    statuses_repo.get_by_code.assert_not_awaited()
    statuses_repo.get_by_display_name.assert_not_awaited()
    session.commit.assert_not_awaited()
    session.refresh.assert_not_awaited()


def test_create_manual_invalid_topic() -> None:
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(exists_by_dedup_hash=AsyncMock(return_value=False), create=AsyncMock())
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=None))
    statuses_repo = types.SimpleNamespace(get_by_code=AsyncMock(), get_by_display_name=AsyncMock())
    service = EntryService(session, entries_repo, topics_repo, statuses_repo)
    payload = CreateManualEntryPayload(title="Entry", primary_topic_id=uuid.uuid4(), original_url="https://x.com")

    with pytest.raises(TopicNotFoundError):
        run_coroutine(service.create_manual(payload))

    entries_repo.exists_by_dedup_hash.assert_not_awaited()
    entries_repo.create.assert_not_awaited()
    statuses_repo.get_by_code.assert_not_awaited()
    statuses_repo.get_by_display_name.assert_not_awaited()
    session.commit.assert_not_awaited()
    session.refresh.assert_not_awaited()


def test_create_manual_with_explicit_status_code() -> None:
    topic_id = uuid.uuid4()
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(exists_by_dedup_hash=AsyncMock(return_value=False), create=AsyncMock())
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=types.SimpleNamespace(id=topic_id)))
    statuses_repo = types.SimpleNamespace(
        get_by_code=AsyncMock(
            side_effect=[
                types.SimpleNamespace(id=uuid.uuid4(), display_name="To Read"),
            ]
        ),
        get_by_display_name=AsyncMock(),
    )

    service = EntryService(session, entries_repo, topics_repo, statuses_repo)
    payload = CreateManualEntryPayload(
        title="Forwarded item",
        primary_topic_id=topic_id,
        original_url="https://x.com",
        status_code="TO_READ",
    )

    result = run_coroutine(service.create_manual(payload))

    assert result.status_name == "To Read"
    statuses_repo.get_by_code.assert_awaited_once_with("TO_READ")
    statuses_repo.get_by_display_name.assert_not_awaited()


def test_delete_entry_success() -> None:
    entry_id = uuid.uuid4()
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(
        exists_by_dedup_hash=AsyncMock(return_value=False),
        create=AsyncMock(),
        get=AsyncMock(return_value=types.SimpleNamespace(id=entry_id)),
        delete=AsyncMock(),
    )
    topics_repo = types.SimpleNamespace(get=AsyncMock())
    statuses_repo = types.SimpleNamespace(get_by_code=AsyncMock(), get_by_display_name=AsyncMock())
    service = EntryService(session, entries_repo, topics_repo, statuses_repo)

    run_coroutine(service.delete(entry_id))

    entries_repo.get.assert_awaited_once_with(entry_id)
    entries_repo.delete.assert_awaited_once()
    session.commit.assert_awaited_once()


def test_delete_entry_not_found() -> None:
    entry_id = uuid.uuid4()
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(
        exists_by_dedup_hash=AsyncMock(return_value=False),
        create=AsyncMock(),
        get=AsyncMock(return_value=None),
        delete=AsyncMock(),
    )
    topics_repo = types.SimpleNamespace(get=AsyncMock())
    statuses_repo = types.SimpleNamespace(get_by_code=AsyncMock(), get_by_display_name=AsyncMock())
    service = EntryService(session, entries_repo, topics_repo, statuses_repo)

    with pytest.raises(EntryNotFoundError):
        run_coroutine(service.delete(entry_id))

    entries_repo.delete.assert_not_awaited()
    session.commit.assert_not_awaited()


def test_move_entry_to_topic_success() -> None:
    entry_id = uuid.uuid4()
    source_topic_id = uuid.uuid4()
    target_topic_id = uuid.uuid4()
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entry = types.SimpleNamespace(
        id=entry_id,
        title="Entry",
        original_url="https://x.com",
        normalized_url="https://x.com/",
        primary_topic_id=source_topic_id,
        notes="note",
        saved_date=None,
    )
    entries_repo = types.SimpleNamespace(
        get_with_status=AsyncMock(return_value=(entry, "To Read")),
    )
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=types.SimpleNamespace(id=target_topic_id)))
    statuses_repo = types.SimpleNamespace(get_by_code=AsyncMock(), get_by_display_name=AsyncMock())
    service = EntryService(session, entries_repo, topics_repo, statuses_repo)

    result = run_coroutine(service.move_to_topic(entry_id, target_topic_id))

    assert result.id == entry_id
    assert result.primary_topic_id == target_topic_id
    assert result.status_name == "To Read"
    assert entry.primary_topic_id == target_topic_id
    entries_repo.get_with_status.assert_awaited_once_with(entry_id)
    topics_repo.get.assert_awaited_once_with(target_topic_id)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(entry)


def test_move_entry_to_topic_fails_on_missing_topic() -> None:
    entry_id = uuid.uuid4()
    target_topic_id = uuid.uuid4()
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(
        get_with_status=AsyncMock(return_value=(types.SimpleNamespace(id=entry_id), "New")),
    )
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=None))
    statuses_repo = types.SimpleNamespace(get_by_code=AsyncMock(), get_by_display_name=AsyncMock())
    service = EntryService(session, entries_repo, topics_repo, statuses_repo)

    with pytest.raises(TopicNotFoundError):
        run_coroutine(service.move_to_topic(entry_id, target_topic_id))

    session.commit.assert_not_awaited()
    session.refresh.assert_not_awaited()


def test_move_entry_to_topic_fails_on_missing_entry() -> None:
    entry_id = uuid.uuid4()
    target_topic_id = uuid.uuid4()
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(get_with_status=AsyncMock(return_value=None))
    topics_repo = types.SimpleNamespace(get=AsyncMock())
    statuses_repo = types.SimpleNamespace(get_by_code=AsyncMock(), get_by_display_name=AsyncMock())
    service = EntryService(session, entries_repo, topics_repo, statuses_repo)

    with pytest.raises(EntryNotFoundError):
        run_coroutine(service.move_to_topic(entry_id, target_topic_id))

    topics_repo.get.assert_not_awaited()
    session.commit.assert_not_awaited()
    session.refresh.assert_not_awaited()
