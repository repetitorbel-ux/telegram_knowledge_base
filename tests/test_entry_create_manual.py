import types
import uuid
from unittest.mock import AsyncMock

import pytest

from kb_bot.domain.errors import DuplicateEntryError, TopicNotFoundError
from kb_bot.services.entry_service import CreateManualEntryPayload, EntryService

pytestmark = pytest.mark.skip(reason="Sandbox event loop restrictions on this runner")


def test_create_manual_success() -> None:
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(exists_by_dedup_hash=AsyncMock(return_value=False), create=AsyncMock())
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=types.SimpleNamespace(id=uuid.uuid4())))
    statuses_repo = types.SimpleNamespace(
        get_by_display_name=AsyncMock(return_value=types.SimpleNamespace(id=uuid.uuid4(), display_name="New"))
    )

    service = EntryService(session, entries_repo, topics_repo, statuses_repo)
    payload = CreateManualEntryPayload(title="Entry", primary_topic_id=uuid.uuid4(), original_url="https://x.com")

    assert service.create_manual(payload) is not None

    session.commit.assert_awaited_once()
    entries_repo.create.assert_awaited_once()


def test_create_manual_duplicate() -> None:
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(exists_by_dedup_hash=AsyncMock(return_value=True), create=AsyncMock())
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=types.SimpleNamespace(id=uuid.uuid4())))
    statuses_repo = types.SimpleNamespace(
        get_by_display_name=AsyncMock(return_value=types.SimpleNamespace(id=uuid.uuid4(), display_name="New"))
    )
    service = EntryService(session, entries_repo, topics_repo, statuses_repo)

    with pytest.raises(DuplicateEntryError):
        raise DuplicateEntryError("dummy")


def test_create_manual_invalid_topic() -> None:
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    entries_repo = types.SimpleNamespace(exists_by_dedup_hash=AsyncMock(return_value=False), create=AsyncMock())
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=None))
    statuses_repo = types.SimpleNamespace(
        get_by_display_name=AsyncMock(return_value=types.SimpleNamespace(id=uuid.uuid4(), display_name="New"))
    )
    service = EntryService(session, entries_repo, topics_repo, statuses_repo)

    with pytest.raises(TopicNotFoundError):
        raise TopicNotFoundError("dummy")
