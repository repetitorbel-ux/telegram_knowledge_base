from kb_bot.bot.handlers.add_parsing import parse_content_input
from kb_bot.core.auth import AuthGuard


def test_auth_guard() -> None:
    guard = AuthGuard(allowed_user_id=42)
    assert guard.is_allowed(42) is True
    assert guard.is_allowed(10) is False


def test_add_flow_parser_for_url_and_note() -> None:
    url, note = parse_content_input("https://example.com/a")
    assert url == "https://example.com/a"
    assert note is None

    url, note = parse_content_input("Some plain note")
    assert url is None
    assert note == "Some plain note"
