import types
import uuid
from collections.abc import Coroutine

from kb_bot.db.repositories.entries import EntriesRepository


def run_coroutine(coroutine: Coroutine[object, object, object]) -> object:
    while True:
        try:
            coroutine.send(None)
        except StopIteration as done:
            return done.value


class _FakeResult:
    def __init__(self, *, scalar=None, rows=None):
        self._scalar = scalar
        self._rows = rows or []

    def scalar_one_or_none(self):
        return self._scalar

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, selected_topic_path: str | None, rows: list[tuple[object, str, str]] | None = None) -> None:
        self.selected_topic_path = selected_topic_path
        self.rows = rows or []
        self.calls = []

    async def execute(self, stmt):
        self.calls.append(stmt)
        if len(self.calls) == 1:
            return _FakeResult(scalar=self.selected_topic_path)
        return _FakeResult(rows=self.rows)


def test_list_entries_topic_filter_includes_secondary_topics_exists_clause() -> None:
    entry = types.SimpleNamespace(id=uuid.uuid4())
    session = _FakeSession(
        selected_topic_path="to_read",
        rows=[(entry, "To Read", "To Read")],
    )
    repo = EntriesRepository(session)

    result = run_coroutine(repo.list_entries(topic_id=uuid.uuid4(), limit=20, offset=0))

    assert len(result) == 1
    assert len(session.calls) == 2
    compiled_sql = str(session.calls[1])
    assert "knowledge_entry_topics" in compiled_sql
    assert "EXISTS" in compiled_sql


def test_list_entries_topic_filter_returns_empty_when_topic_not_found() -> None:
    session = _FakeSession(selected_topic_path=None)
    repo = EntriesRepository(session)

    result = run_coroutine(repo.list_entries(topic_id=uuid.uuid4(), limit=20, offset=0))

    assert result == []
    assert len(session.calls) == 1

