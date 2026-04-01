from kb_bot.core.forward_parsing import build_forward_notes, build_forward_title, extract_first_url
from types import SimpleNamespace


def test_extract_first_url() -> None:
    text = "See this https://example.com/a?x=1 and this https://example.org"
    assert extract_first_url(text) == "https://example.com/a?x=1"


def test_extract_first_url_from_text_link_entity() -> None:
    entities = [SimpleNamespace(type="text_link", url="https://openrouter.ai/news")]
    assert extract_first_url("Ссылка", entities=entities) == "https://openrouter.ai/news"


def test_build_forward_title() -> None:
    assert build_forward_title("   Hello    world   ") == "Hello world"
    assert build_forward_title("") == "Forwarded message"


def test_build_forward_notes() -> None:
    notes = build_forward_notes("message body", "chat:123")
    assert notes == "origin: chat:123\n\nmessage body"
