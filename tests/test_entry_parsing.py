from kb_bot.core.entry_parsing import parse_entry_command, parse_entry_move_command


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
