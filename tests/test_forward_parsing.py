from kb_bot.core.forward_parsing import build_forward_notes, build_forward_title, extract_first_url


def test_extract_first_url() -> None:
    text = "See this https://example.com/a?x=1 and this https://example.org"
    assert extract_first_url(text) == "https://example.com/a?x=1"


def test_build_forward_title() -> None:
    assert build_forward_title("   Hello    world   ") == "Hello world"
    assert build_forward_title("") == "Forwarded message"


def test_build_forward_notes() -> None:
    notes = build_forward_notes("message body", "chat:123")
    assert notes == "origin: chat:123\n\nmessage body"

