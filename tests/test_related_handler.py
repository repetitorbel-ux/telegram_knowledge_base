import uuid
import os
from datetime import UTC, datetime

os.environ.pop("SSLKEYLOGFILE", None)

from kb_bot.bot.handlers.search import (
    _build_related_results_keyboard,
    _parse_related_page_callback,
    _render_related_results_screen,
)
from kb_bot.bot.ui.callbacks import ENTRY_VIEW_PREFIX, RELATED_PAGE_PREFIX
from kb_bot.domain.dto import RelatedEntryDTO


def test_parse_related_page_callback_ok() -> None:
    parsed = _parse_related_page_callback(
        f"{RELATED_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:3"
    )
    assert parsed is not None
    entry_id, page = parsed
    assert str(entry_id) == "11111111-1111-1111-1111-111111111111"
    assert page == 3


def test_parse_related_page_callback_invalid() -> None:
    assert _parse_related_page_callback(f"{RELATED_PAGE_PREFIX}bad-uuid:1") is None
    assert _parse_related_page_callback(f"{RELATED_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:bad") is None


def test_parse_related_page_callback_defaults_to_page_zero() -> None:
    parsed = _parse_related_page_callback(f"{RELATED_PAGE_PREFIX}11111111-1111-1111-1111-111111111111")
    assert parsed is not None
    entry_id, page = parsed
    assert str(entry_id) == "11111111-1111-1111-1111-111111111111"
    assert page == 0


def test_render_related_results_screen_shows_header_only() -> None:
    items = [
        RelatedEntryDTO(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            title="PostgreSQL restore strategy",
            status_name="New",
            topic_name="Infrastructure",
            score=12,
            same_topic=True,
            shared_tags_count=2,
            title_similarity_points=2,
            text_overlap_points=1,
            saved_date=datetime.now(UTC),
        )
    ]

    text = _render_related_results_screen("PostgreSQL backup strategy", items, page=0)
    assert text == "Похожие материалы для: PostgreSQL backup strategy"


def test_render_related_results_screen_truncates_long_source_title() -> None:
    items = [
        RelatedEntryDTO(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            title="PostgreSQL restore strategy",
            status_name="New",
            topic_name="Infrastructure",
            score=12,
            same_topic=True,
            shared_tags_count=2,
            title_similarity_points=2,
            text_overlap_points=1,
            saved_date=datetime.now(UTC),
        )
    ]
    long_title = "A" * 140
    text = _render_related_results_screen(long_title, items, page=0)
    assert text.startswith("Похожие материалы для: ")
    assert text.endswith("…")
    assert len(text) < len("Похожие материалы для: " + long_title)


def test_build_related_results_keyboard_contains_refresh_and_back_callbacks() -> None:
    items = [
        RelatedEntryDTO(
            id=uuid.UUID("11111111-1111-1111-1111-111111111111"),
            title="PostgreSQL restore strategy",
            status_name="New",
            topic_name="Infrastructure",
            score=12,
            same_topic=True,
            shared_tags_count=2,
            title_similarity_points=2,
            text_overlap_points=1,
            saved_date=datetime.now(UTC),
        )
    ]

    keyboard = _build_related_results_keyboard(
        items,
        entry_id=uuid.UUID("22222222-2222-2222-2222-222222222222"),
        page=1,
        has_next_page=True,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{RELATED_PAGE_PREFIX}22222222-2222-2222-2222-222222222222:1" in callbacks
    assert f"{RELATED_PAGE_PREFIX}22222222-2222-2222-2222-222222222222:0" in callbacks
    assert f"{RELATED_PAGE_PREFIX}22222222-2222-2222-2222-222222222222:2" in callbacks
    assert f"{ENTRY_VIEW_PREFIX}22222222-2222-2222-2222-222222222222" in callbacks
    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert "Назад к записи" in labels
