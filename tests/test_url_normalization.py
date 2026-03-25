from kb_bot.core.url_normalization import normalize_url


def test_normalize_url_removes_tracking_and_default_port() -> None:
    url = "HTTPS://Example.com:443/path/?utm_source=abc&a=1&fbclid=zzz&b=2"
    assert normalize_url(url) == "https://example.com/path?a=1&b=2"


def test_normalize_url_returns_none_for_non_http() -> None:
    assert normalize_url("ftp://example.com/file") is None
    assert normalize_url("not-a-url") is None

