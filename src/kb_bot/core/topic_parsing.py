import uuid
from dataclasses import dataclass


@dataclass(slots=True)
class TopicAddCommand:
    parent_topic_id: uuid.UUID | None
    name: str | None


@dataclass(slots=True)
class TopicRenameCommand:
    topic_id: uuid.UUID | None
    new_name: str | None


def parse_topic_add_command(text: str | None) -> TopicAddCommand:
    if not text:
        return TopicAddCommand(parent_topic_id=None, name=None)
    parts = text.split(maxsplit=2)
    if len(parts) == 2:
        return TopicAddCommand(parent_topic_id=None, name=parts[1].strip())
    if len(parts) < 3:
        return TopicAddCommand(parent_topic_id=None, name=None)

    parent_raw = parts[1].strip().lower()
    if parent_raw == "root":
        return TopicAddCommand(parent_topic_id=None, name=parts[2].strip())
    try:
        parent_id = uuid.UUID(parent_raw)
    except ValueError:
        return TopicAddCommand(parent_topic_id=None, name=None)
    return TopicAddCommand(parent_topic_id=parent_id, name=parts[2].strip())


def parse_topic_rename_command(text: str | None) -> TopicRenameCommand:
    if not text:
        return TopicRenameCommand(topic_id=None, new_name=None)
    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        return TopicRenameCommand(topic_id=None, new_name=None)
    try:
        topic_id = uuid.UUID(parts[1].strip())
    except ValueError:
        return TopicRenameCommand(topic_id=None, new_name=None)
    return TopicRenameCommand(topic_id=topic_id, new_name=parts[2].strip())

