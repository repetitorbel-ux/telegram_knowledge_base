from kb_bot.core.entry_parsing import parse_entry_command


def test_parse_entry_command_ok() -> None:
    entry_id = parse_entry_command("/entry 123e4567-e89b-12d3-a456-426614174000")
    assert str(entry_id) == "123e4567-e89b-12d3-a456-426614174000"


def test_parse_entry_command_invalid() -> None:
    assert parse_entry_command("/entry") is None
    assert parse_entry_command("/entry bad-uuid") is None

