from kb_bot.core.search_parsing import parse_search_query


def test_parse_search_query_with_value() -> None:
    assert parse_search_query("/search asyncpg") == "asyncpg"
    assert parse_search_query("/search    aiogram v3") == "aiogram v3"


def test_parse_search_query_without_value() -> None:
    assert parse_search_query("/search") == ""
    assert parse_search_query(None) == ""
