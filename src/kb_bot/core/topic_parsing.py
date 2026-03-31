import uuid
from dataclasses import dataclass
import re


@dataclass(slots=True)
class TopicAddCommand:
    parent_topic_id: uuid.UUID | None
    parent_selector: str | None
    name: str | None


@dataclass(slots=True)
class TopicRenameCommand:
    topic_id: uuid.UUID | None
    new_name: str | None


def parse_topic_add_command(text: str | None) -> TopicAddCommand:
    if not text:
        return TopicAddCommand(parent_topic_id=None, parent_selector=None, name=None)

    arrow_parent_match = re.match(
        r'^/topic_add\s+(?:"([^"]+)"|\'([^\']+)\'|(\S+))\s*->\s*(.+)$',
        text.strip(),
    )
    if arrow_parent_match:
        selector = (
            arrow_parent_match.group(1)
            or arrow_parent_match.group(2)
            or arrow_parent_match.group(3)
        )
        name = (arrow_parent_match.group(4) or "").strip()
        if not selector or not name:
            return TopicAddCommand(parent_topic_id=None, parent_selector=None, name=None)
        return TopicAddCommand(parent_topic_id=None, parent_selector=selector.strip(), name=name)

    parent_selector_match = re.match(
        r'^/topic_add\s+parent=(?:"([^"]+)"|\'([^\']+)\'|(\S+))\s+(.+)$',
        text.strip(),
    )
    if parent_selector_match:
        selector = (
            parent_selector_match.group(1)
            or parent_selector_match.group(2)
            or parent_selector_match.group(3)
        )
        name = (parent_selector_match.group(4) or "").strip()
        if not selector or not name:
            return TopicAddCommand(parent_topic_id=None, parent_selector=None, name=None)
        return TopicAddCommand(parent_topic_id=None, parent_selector=selector.strip(), name=name)

    parts = text.split(maxsplit=2)
    if len(parts) == 2:
        return TopicAddCommand(parent_topic_id=None, parent_selector=None, name=parts[1].strip())
    if len(parts) < 3:
        return TopicAddCommand(parent_topic_id=None, parent_selector=None, name=None)

    parent_raw = parts[1].strip().lower()
    if parent_raw == "root":
        return TopicAddCommand(parent_topic_id=None, parent_selector=None, name=parts[2].strip())
    try:
        parent_id = uuid.UUID(parent_raw)
    except ValueError:
        return TopicAddCommand(parent_topic_id=None, parent_selector=None, name=None)
    return TopicAddCommand(parent_topic_id=parent_id, parent_selector=None, name=parts[2].strip())


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
