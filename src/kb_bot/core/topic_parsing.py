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


@dataclass(slots=True)
class TopicDeleteCommand:
    topic_id: uuid.UUID | None
    topic_selector: str | None


@dataclass(slots=True)
class TopicMoveCommand:
    topic_id: uuid.UUID | None
    topic_selector: str | None
    target_parent_id: uuid.UUID | None
    target_parent_selector: str | None
    move_to_root: bool


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


def parse_topic_delete_command(text: str | None) -> TopicDeleteCommand:
    if not text:
        return TopicDeleteCommand(topic_id=None, topic_selector=None)

    quoted_match = re.match(r'^/topic_delete\s+(?:"([^"]+)"|\'([^\']+)\')\s*$', text.strip())
    if quoted_match:
        selector = quoted_match.group(1) or quoted_match.group(2)
        return TopicDeleteCommand(topic_id=None, topic_selector=(selector or "").strip() or None)

    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        return TopicDeleteCommand(topic_id=None, topic_selector=None)

    raw_value = parts[1].strip()
    if not raw_value:
        return TopicDeleteCommand(topic_id=None, topic_selector=None)

    try:
        topic_id = uuid.UUID(raw_value)
    except ValueError:
        return TopicDeleteCommand(topic_id=None, topic_selector=raw_value)
    return TopicDeleteCommand(topic_id=topic_id, topic_selector=None)


def parse_topic_move_command(text: str | None) -> TopicMoveCommand:
    if not text:
        return TopicMoveCommand(
            topic_id=None,
            topic_selector=None,
            target_parent_id=None,
            target_parent_selector=None,
            move_to_root=False,
        )

    arrow_match = re.match(
        r'^/topic_move\s+(?:"([^"]+)"|\'([^\']+)\'|(\S+))\s*->\s*(?:"([^"]+)"|\'([^\']+)\'|(\S+))\s*$',
        text.strip(),
    )
    if arrow_match:
        source_raw = arrow_match.group(1) or arrow_match.group(2) or arrow_match.group(3)
        target_raw = arrow_match.group(4) or arrow_match.group(5) or arrow_match.group(6)
        return _build_topic_move_command(source_raw, target_raw)

    parts = text.split(maxsplit=2)
    if len(parts) < 3:
        return TopicMoveCommand(
            topic_id=None,
            topic_selector=None,
            target_parent_id=None,
            target_parent_selector=None,
            move_to_root=False,
        )
    return _build_topic_move_command(parts[1], parts[2])


def _build_topic_move_command(source_raw: str | None, target_raw: str | None) -> TopicMoveCommand:
    source = (source_raw or "").strip()
    target = (target_raw or "").strip()
    if not source or not target:
        return TopicMoveCommand(
            topic_id=None,
            topic_selector=None,
            target_parent_id=None,
            target_parent_selector=None,
            move_to_root=False,
        )

    topic_id: uuid.UUID | None = None
    topic_selector: str | None = None
    try:
        topic_id = uuid.UUID(source)
    except ValueError:
        topic_selector = source

    if target.lower() == "root":
        return TopicMoveCommand(
            topic_id=topic_id,
            topic_selector=topic_selector,
            target_parent_id=None,
            target_parent_selector=None,
            move_to_root=True,
        )

    target_parent_id: uuid.UUID | None = None
    target_parent_selector: str | None = None
    try:
        target_parent_id = uuid.UUID(target)
    except ValueError:
        target_parent_selector = target

    return TopicMoveCommand(
        topic_id=topic_id,
        topic_selector=topic_selector,
        target_parent_id=target_parent_id,
        target_parent_selector=target_parent_selector,
        move_to_root=False,
    )
