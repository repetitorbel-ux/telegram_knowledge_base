from kb_bot.core.backup_parsing import parse_restore_args, parse_single_uuid_arg


def test_parse_single_uuid_arg() -> None:
    value = parse_single_uuid_arg("/restore_token 123e4567-e89b-12d3-a456-426614174000")
    assert str(value) == "123e4567-e89b-12d3-a456-426614174000"
    assert parse_single_uuid_arg("/restore_token bad") is None


def test_parse_restore_args() -> None:
    backup_id, token = parse_restore_args("/restore 123e4567-e89b-12d3-a456-426614174000 abc123")
    assert str(backup_id) == "123e4567-e89b-12d3-a456-426614174000"
    assert token == "abc123"

