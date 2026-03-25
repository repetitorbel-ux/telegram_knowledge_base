from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_QUERY_KEYS = {"fbclid", "gclid", "yclid"}


def normalize_url(raw_url: str | None) -> str | None:
    if raw_url is None:
        return None

    candidate = raw_url.strip()
    if not candidate:
        return None

    parts = urlsplit(candidate)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        return None

    hostname = (parts.hostname or "").lower()
    if not hostname:
        return None

    port = parts.port
    if (parts.scheme == "http" and port == 80) or (parts.scheme == "https" and port == 443):
        port = None

    netloc = hostname if port is None else f"{hostname}:{port}"

    cleaned_query_pairs = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        key_lower = key.lower()
        if key_lower.startswith("utm_") or key_lower in TRACKING_QUERY_KEYS:
            continue
        cleaned_query_pairs.append((key, value))

    cleaned_query_pairs.sort(key=lambda item: (item[0], item[1]))
    normalized_query = urlencode(cleaned_query_pairs, doseq=True)

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path[:-1]

    return urlunsplit((parts.scheme.lower(), netloc, path, normalized_query, ""))

