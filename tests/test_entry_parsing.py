from kb_bot.core.entry_parsing import (
    parse_entry_command,
    parse_entry_edit_command,
    parse_entry_move_command,
    parse_entry_topic_command,
)


def test_parse_entry_command_ok() -> None:
    entry_id = parse_entry_command("/entry 123e4567-e89b-12d3-a456-426614174000")
    assert str(entry_id) == "123e4567-e89b-12d3-a456-426614174000"


def test_parse_entry_command_invalid() -> None:
    assert parse_entry_command("/entry") is None
    assert parse_entry_command("/entry bad-uuid") is None


def test_parse_entry_move_command_ok() -> None:
    parsed = parse_entry_move_command(
        "/entry_move 123e4567-e89b-12d3-a456-426614174000 123e4567-e89b-12d3-a456-426614174001"
    )
    assert parsed is not None
    entry_id, topic_id = parsed
    assert str(entry_id) == "123e4567-e89b-12d3-a456-426614174000"
    assert str(topic_id) == "123e4567-e89b-12d3-a456-426614174001"


def test_parse_entry_move_command_invalid() -> None:
    assert parse_entry_move_command("/entry_move") is None
    assert parse_entry_move_command("/entry_move bad-uuid 123e4567-e89b-12d3-a456-426614174001") is None
    assert parse_entry_move_command("/entry_move 123e4567-e89b-12d3-a456-426614174000 bad-uuid") is None


def test_parse_entry_topic_command_ok() -> None:
    parsed = parse_entry_topic_command(
        "/entry_topic_add 123e4567-e89b-12d3-a456-426614174000 123e4567-e89b-12d3-a456-426614174001"
    )
    assert parsed is not None
    entry_id, topic_id = parsed
    assert str(entry_id) == "123e4567-e89b-12d3-a456-426614174000"
    assert str(topic_id) == "123e4567-e89b-12d3-a456-426614174001"


def test_parse_entry_topic_command_invalid() -> None:
    assert parse_entry_topic_command("/entry_topic_add") is None
    assert parse_entry_topic_command("/entry_topic_add bad-uuid 123e4567-e89b-12d3-a456-426614174001") is None
    assert parse_entry_topic_command("/entry_topic_add 123e4567-e89b-12d3-a456-426614174000 bad-uuid") is None


def test_parse_entry_edit_command_ok() -> None:
    parsed = parse_entry_edit_command(
        "/entry_edit 123e4567-e89b-12d3-a456-426614174000 notes Keep this note"
    )
    assert parsed is not None
    entry_id, field_name, value = parsed
    assert str(entry_id) == "123e4567-e89b-12d3-a456-426614174000"
    assert field_name == "notes"
    assert value == "Keep this note"


def test_parse_entry_edit_command_invalid() -> None:
    assert parse_entry_edit_command("/entry_edit") is None
    assert parse_entry_edit_command("/entry_edit bad-uuid title New title") is None
    assert parse_entry_edit_command("/entry_edit 123e4567-e89b-12d3-a456-426614174000 title") is None
