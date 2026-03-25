from kb_bot.core.import_parsing import detect_import_format, parse_csv_rows, parse_json_rows


def test_detect_import_format() -> None:
    assert detect_import_format("items.csv") == "csv"
    assert detect_import_format("items.json") == "json"
    assert detect_import_format("items.txt") is None


def test_parse_csv_rows() -> None:
    payload = b"title,original_url,notes\nA,https://example.com,hello\n"
    rows = parse_csv_rows(payload)
    assert rows[0]["title"] == "A"
    assert rows[0]["original_url"] == "https://example.com"


def test_parse_json_rows() -> None:
    rows = parse_json_rows(b'[{"title":"A","original_url":"https://example.com"}]')
    assert rows[0]["title"] == "A"

