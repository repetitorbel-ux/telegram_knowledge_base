from kb_bot.core.export_parsing import parse_export_format


def test_parse_export_format() -> None:
    assert parse_export_format("/export csv status=New") == "csv"
    assert parse_export_format("/export json") == "json"
    assert parse_export_format("/export unknown") == "json"

