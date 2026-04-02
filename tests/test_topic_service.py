import types
import uuid
from collections.abc import Coroutine
from unittest.mock import AsyncMock
import pytest

from kb_bot.services.topic_service import TopicService
from kb_bot.domain.errors import TopicConflictError


def run_coroutine(coroutine: Coroutine[object, object, object]) -> object:
    while True:
        try:
            coroutine.send(None)
        except StopIteration as done:
            return done.value


def test_rename_to_read_topic_keeps_stable_path_for_forward_routing() -> None:
    topic_id = uuid.uuid4()
    topic = types.SimpleNamespace(
        id=topic_id,
        name="To read",
        slug="to_read",
        full_path="to_read",
        level=0,
        parent_topic_id=None,
    )
    topics_repo = types.SimpleNamespace(get=AsyncMock(return_value=topic))
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    service = TopicService(topics_repo=topics_repo, session=session)

    result = run_coroutine(service.rename_topic(topic_id, "Read Later"))

    assert topic.name == "Read Later"
    assert topic.slug == "to_read"
    assert topic.full_path == "to_read"
    assert result.full_path == "to_read"
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(topic)


def test_move_topic_to_root_recalculates_branch_paths_and_levels() -> None:
    topic_id = uuid.uuid4()
    parent_id = uuid.uuid4()
    topic = types.SimpleNamespace(
        id=topic_id,
        name="Codex",
        slug="codex",
        full_path="neural_networks_ai.codex",
        full_path_ltree="neural_networks_ai.codex",
        level=1,
        parent_topic_id=parent_id,
    )
    child = types.SimpleNamespace(
        id=uuid.uuid4(),
        full_path="neural_networks_ai.codex.agentic",
        full_path_ltree="neural_networks_ai.codex.agentic",
        level=2,
    )
    topics_repo = types.SimpleNamespace(
        get=AsyncMock(return_value=topic),
        get_by_full_path=AsyncMock(return_value=None),
        list_descendants=AsyncMock(return_value=[child]),
    )
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    service = TopicService(topics_repo=topics_repo, session=session)

    result = run_coroutine(service.move_topic(topic_id=topic_id, new_parent_topic_id=None))

    assert result.full_path == "codex"
    assert result.level == 0
    assert topic.parent_topic_id is None
    assert topic.full_path == "codex"
    assert topic.level == 0
    assert child.full_path == "codex.agentic"
    assert child.level == 1
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(topic)


def test_move_topic_under_other_parent_recalculates_branch_paths_and_levels() -> None:
    topic_id = uuid.uuid4()
    old_parent_id = uuid.uuid4()
    new_parent_id = uuid.uuid4()
    topic = types.SimpleNamespace(
        id=topic_id,
        name="Codex",
        slug="codex",
        full_path="neural_networks_ai.codex",
        full_path_ltree="neural_networks_ai.codex",
        level=1,
        parent_topic_id=old_parent_id,
    )
    new_parent = types.SimpleNamespace(
        id=new_parent_id,
        full_path="infrastructure.tools",
        level=1,
    )
    child = types.SimpleNamespace(
        id=uuid.uuid4(),
        full_path="neural_networks_ai.codex.agentic",
        full_path_ltree="neural_networks_ai.codex.agentic",
        level=2,
    )

    async def _get_topic(value: uuid.UUID):
        if value == topic_id:
            return topic
        if value == new_parent_id:
            return new_parent
        return None

    topics_repo = types.SimpleNamespace(
        get=AsyncMock(side_effect=_get_topic),
        get_by_full_path=AsyncMock(return_value=None),
        list_descendants=AsyncMock(return_value=[child]),
    )
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    service = TopicService(topics_repo=topics_repo, session=session)

    result = run_coroutine(service.move_topic(topic_id=topic_id, new_parent_topic_id=new_parent_id))

    assert result.full_path == "infrastructure.tools.codex"
    assert result.level == 2
    assert topic.parent_topic_id == new_parent_id
    assert child.full_path == "infrastructure.tools.codex.agentic"
    assert child.level == 3


def test_move_topic_rejects_move_under_descendant() -> None:
    topic_id = uuid.uuid4()
    descendant_id = uuid.uuid4()
    topic = types.SimpleNamespace(
        id=topic_id,
        slug="codex",
        full_path="neural_networks_ai.codex",
        level=1,
        parent_topic_id=uuid.uuid4(),
    )
    descendant = types.SimpleNamespace(
        id=descendant_id,
        full_path="neural_networks_ai.codex.agentic",
        level=2,
    )

    async def _get_topic(value: uuid.UUID):
        if value == topic_id:
            return topic
        if value == descendant_id:
            return descendant
        return None

    topics_repo = types.SimpleNamespace(
        get=AsyncMock(side_effect=_get_topic),
        get_by_full_path=AsyncMock(),
        list_descendants=AsyncMock(),
    )
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    service = TopicService(topics_repo=topics_repo, session=session)

    with pytest.raises(ValueError) as exc_info:
        run_coroutine(service.move_topic(topic_id=topic_id, new_parent_topic_id=descendant_id))
    exc = exc_info.value
    assert "descendant" in str(exc)
    session.commit.assert_not_awaited()


def test_move_topic_rejects_path_conflict() -> None:
    topic_id = uuid.uuid4()
    new_parent_id = uuid.uuid4()
    topic = types.SimpleNamespace(
        id=topic_id,
        slug="codex",
        full_path="neural_networks_ai.codex",
        full_path_ltree="neural_networks_ai.codex",
        level=1,
        parent_topic_id=uuid.uuid4(),
    )
    parent = types.SimpleNamespace(id=new_parent_id, full_path="infrastructure.tools", level=1)
    conflict = types.SimpleNamespace(id=uuid.uuid4(), full_path="infrastructure.tools.codex")

    async def _get_topic(value: uuid.UUID):
        if value == topic_id:
            return topic
        if value == new_parent_id:
            return parent
        return None

    topics_repo = types.SimpleNamespace(
        get=AsyncMock(side_effect=_get_topic),
        get_by_full_path=AsyncMock(return_value=conflict),
        list_descendants=AsyncMock(),
    )
    session = types.SimpleNamespace(commit=AsyncMock(), refresh=AsyncMock())
    service = TopicService(topics_repo=topics_repo, session=session)

    with pytest.raises(TopicConflictError):
        run_coroutine(service.move_topic(topic_id=topic_id, new_parent_topic_id=new_parent_id))
    session.commit.assert_not_awaited()
