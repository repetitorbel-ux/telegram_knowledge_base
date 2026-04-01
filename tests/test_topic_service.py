import types
import uuid
from collections.abc import Coroutine
from unittest.mock import AsyncMock

from kb_bot.services.topic_service import TopicService


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
