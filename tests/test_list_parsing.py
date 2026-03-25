from kb_bot.core.list_parsing import parse_list_command


def test_parse_list_command_defaults() -> None:
    filters = parse_list_command("/list")
    assert filters.status_name is None
    assert filters.topic_id is None
    assert filters.limit == 20


def test_parse_list_command_with_filters() -> None:
    filters = parse_list_command(
        "/list status=To_Read topic=123e4567-e89b-12d3-a456-426614174000 limit=5"
    )
    assert filters.status_name == "To Read"
    assert str(filters.topic_id) == "123e4567-e89b-12d3-a456-426614174000"
    assert filters.limit == 5

