import csv
import io
import json


def detect_import_format(filename: str | None) -> str | None:
    if not filename:
        return None
    lower = filename.lower()
    if lower.endswith(".csv"):
        return "csv"
    if lower.endswith(".json"):
        return "json"
    return None


def parse_csv_rows(data: bytes) -> list[dict]:
    text = data.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def parse_json_rows(data: bytes) -> list[dict]:
    payload = json.loads(data.decode("utf-8"))
    if isinstance(payload, list):
        return [dict(item) for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("entries"), list):
        return [dict(item) for item in payload["entries"] if isinstance(item, dict)]
    return []

