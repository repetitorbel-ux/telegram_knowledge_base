from kb_bot.core.collection_parsing import parse_collection_add_name, parse_collection_run_id


def test_parse_collection_add_name() -> None:
    assert parse_collection_add_name("/collection_add backlog status=New") == "backlog"
    assert parse_collection_add_name("/collection_add") is None


def test_parse_collection_run_id() -> None:
    value = parse_collection_run_id("/collection_run 123e4567-e89b-12d3-a456-426614174000")
    assert str(value) == "123e4567-e89b-12d3-a456-426614174000"
    assert parse_collection_run_id("/collection_run bad") is None

