from kb_bot.core.status_parsing import parse_status_command


def test_parse_status_command_ok() -> None:
    entry_id, status = parse_status_command("/status 123e4567-e89b-12d3-a456-426614174000 To Read")
    assert str(entry_id) == "123e4567-e89b-12d3-a456-426614174000"
    assert status == "To Read"


def test_parse_status_command_invalid() -> None:
    assert parse_status_command("/status") == (None, None)
    assert parse_status_command("/status bad-uuid New") == (None, None)

