from pathlib import Path


def test_stats_service_contains_required_metrics() -> None:
    content = Path("src/kb_bot/services/stats_service.py").read_text(encoding="utf-8")
    assert "total_entries" in content
    assert "duplicates_prevented" in content
    assert "verified_coverage" in content

