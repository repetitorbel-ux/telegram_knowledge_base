import os
import subprocess

os.environ.pop("SSLKEYLOGFILE", None)

from kb_bot.bot.handlers.menu import (
    _allowed_target_statuses,
    _parse_entry_view_callback,
    _parse_entry_id_from_callback,
    _parse_list_page_callback,
    _parse_topic_entries_page_callback,
    _parse_page_callback,
    _parse_status_update_callback,
    _resolve_entry_action_back_context,
    _resolve_entry_back_action,
    _resolve_entry_back_callback_from_state,
    _resolve_status_back_action,
    _format_restore_failure_message,
    _format_restore_progress_checkpoint,
    _render_backups_list_screen,
    _render_collection_result_screen,
    _render_entry_detail_screen,
    _render_entry_preview_screen,
    _render_entry_list_screen,
    _render_search_results_screen,
    _render_stats_screen,
    _render_topic_detail_screen,
    _render_topics_screen,
    _resolve_topic_entries_back_action,
)
from kb_bot.bot.handlers.start import render_boot_text, render_restart_text, render_welcome_text
from kb_bot.bot.ui.callbacks import (
    ADD_TOPIC_PREFIX,
    BACKUP_RESTORE_ACK_PREFIX,
    BACKUP_RESTORE_EXEC_PREFIX,
    BACKUP_RESTORE_PICK_PREFIX,
    COLLECTIONS_PAGE_PREFIX,
    COLLECTION_VIEW_PREFIX,
    ENTRY_DELETE_CONFIRM_PREFIX,
    ENTRY_DELETE_PREFIX,
    ENTRY_MOVE_CREATE_L0,
    ENTRY_MOVE_CREATE_L1,
    ENTRY_MOVE_MENU_PREFIX,
    ENTRY_MOVE_PAGE_PREFIX,
    ENTRY_MOVE_PARENT_PICK_PREFIX,
    ENTRY_MOVE_PICK_PREFIX,
    ENTRY_STATUS_MENU_PREFIX,
    ENTRY_STATUS_PREFIX,
    ENTRY_VIEW_PREFIX,
    LIST_NEW,
    LIST_PAGE_PREFIX,
    MENU_ADD,
    MENU_BACKUPS,
    MENU_BACKUP_CREATE,
    MENU_BACKUP_LIST,
    MENU_BACKUP_RESTORE,
    MENU_CANCEL_FLOW,
    MENU_COLLECTIONS,
    MENU_HELP,
    MENU_IMPORT_EXPORT,
    MENU_EXPORT_CSV,
    MENU_EXPORT_JSON,
    MENU_IMPORT_START,
    MENU_LIST,
    MENU_MAIN,
    MENU_STATS,
    MENU_TOPIC_CREATE,
    MENU_TOPICS,
    SEARCH_PAGE_PREFIX,
    TOPIC_ENTRIES_PAGE_PREFIX,
    TOPICS_PAGE_PREFIX,
    TOPIC_CREATE_CHILD_PREFIX,
    TOPIC_DELETE_CONFIRM_PREFIX,
    TOPIC_DELETE_PREFIX,
    TOPIC_ENTRY_PREVIEW_PREFIX,
    TOPIC_TOGGLE_PREFIX,
    TOPIC_RENAME_PREFIX,
    TOPIC_VIEW_PREFIX,
)
from kb_bot.bot.ui.keyboards import (
    build_backup_restore_picker_keyboard,
    build_backup_restore_warning_keyboard,
    build_add_topic_picker_keyboard,
    build_backups_keyboard,
    build_collections_keyboard,
    build_entry_delete_confirm_keyboard,
    build_entry_detail_keyboard,
    build_entry_move_topic_keyboard,
    build_post_entry_delete_keyboard,
    build_entry_preview_keyboard,
    build_entry_results_keyboard,
    build_entry_status_picker_keyboard,
    build_flow_navigation_keyboard,
    build_import_export_keyboard,
    build_list_filters_keyboard,
    build_main_menu_keyboard,
    build_topic_delete_confirm_keyboard,
    build_topic_detail_keyboard,
    build_topic_entries_actions_rows,
    build_topics_keyboard,
    build_topics_tree_keyboard,
)
from kb_bot.domain.dto import TopicDTO
from kb_bot.services.collection_service import SavedViewDTO
from kb_bot.services.query_service import EntryDetail


def test_render_welcome_text_is_short() -> None:
    text = render_welcome_text()
    assert text == "Telegram KB Bot готов к работе."


def test_render_boot_text_is_short() -> None:
    text = render_boot_text()
    assert text == "Бот запущен и готов к работе."


def test_render_restart_text_is_short() -> None:
    text = render_restart_text()
    assert text == "Бот перезапущен и снова готов к работе."


def test_main_menu_keyboard_contains_expected_actions() -> None:
    keyboard = build_main_menu_keyboard()
    callback_map = {
        button.text: button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    }
    assert callback_map["Добавить"] == MENU_ADD
    assert callback_map["Импорт/экспорт"] == MENU_IMPORT_EXPORT
    assert callback_map["Бэкапы"] == MENU_BACKUPS
    assert callback_map["Подсказка по командам"] == MENU_HELP
    assert callback_map["Статистика"] == MENU_STATS


def test_flow_navigation_keyboard_contains_cancel_and_home() -> None:
    keyboard = build_flow_navigation_keyboard()
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert MENU_MAIN in callbacks
    assert MENU_CANCEL_FLOW in callbacks


def test_list_filters_keyboard_contains_quick_filters() -> None:
    keyboard = build_list_filters_keyboard()
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert LIST_NEW in callbacks


def test_import_export_keyboard_contains_actions() -> None:
    keyboard = build_import_export_keyboard()
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert MENU_IMPORT_START in callbacks
    assert MENU_EXPORT_CSV in callbacks
    assert MENU_EXPORT_JSON in callbacks


def test_backups_keyboard_contains_actions() -> None:
    keyboard = build_backups_keyboard()
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert MENU_BACKUP_CREATE in callbacks
    assert MENU_BACKUP_LIST in callbacks
    assert MENU_BACKUP_RESTORE in callbacks


def test_backup_restore_picker_keyboard_contains_pick_callbacks() -> None:
    class BackupRow:
        def __init__(self, id: str, filename: str, restore_tested_at: str | None) -> None:
            self.id = id
            self.filename = filename
            self.restore_tested_at = restore_tested_at

    keyboard = build_backup_restore_picker_keyboard(
        [BackupRow("11111111-1111-1111-1111-111111111111", "tg_kb_test.dump", None)]
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{BACKUP_RESTORE_PICK_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert MENU_BACKUPS in callbacks


def test_backup_restore_warning_keyboard_contains_ack_and_exec_callbacks() -> None:
    backup_id = "11111111-1111-1111-1111-111111111111"
    ack_keyboard = build_backup_restore_warning_keyboard(backup_id, final=False)
    exec_keyboard = build_backup_restore_warning_keyboard(backup_id, final=True)

    ack_callbacks = [button.callback_data for row in ack_keyboard.inline_keyboard for button in row]
    exec_callbacks = [button.callback_data for row in exec_keyboard.inline_keyboard for button in row]

    assert f"{BACKUP_RESTORE_ACK_PREFIX}{backup_id}" in ack_callbacks
    assert f"{BACKUP_RESTORE_EXEC_PREFIX}{backup_id}" in exec_callbacks


def test_render_topics_screen_uses_hierarchy() -> None:
    topics = [
        TopicDTO(id="ignored", name="Root", full_path="Root", level=0),
        TopicDTO(id="ignored", name="Child", full_path="Root.Child", level=1),
    ]
    text = _render_topics_screen(topics)
    assert "Темы:" in text
    assert "- Root" in text
    assert "  - Child" in text


def test_render_stats_screen_contains_summary() -> None:
    text = _render_stats_screen(
        {
            "total_entries": 5,
            "inbox_size": 2,
            "backlog": 1,
            "verified_coverage": 0.2,
            "duplicates_prevented": 3,
            "by_status": {"New": 2, "Verified": 1},
            "by_topic": {"Python": 4},
        }
    )
    assert "Всего записей: 5" in text
    assert "По статусам:" in text
    assert "Python: 4" in text


def test_render_entry_list_screen_contains_titles() -> None:
    items = [
        EntryDetail(
            entry_id="ignored",
            title="Example title",
            status_name="New",
            topic_name="Python",
            original_url=None,
            normalized_url=None,
            notes=None,
        )
    ]
    text = _render_entry_list_screen(items, "Последние записи")
    assert "Последние записи:" in text
    assert "Example title [New] (Python)" in text


def test_render_topic_entries_list_screen_uses_compact_header() -> None:
    items = [
        EntryDetail(
            entry_id="ignored",
            title="Example title",
            status_name="New",
            topic_name="To Read",
            original_url=None,
            normalized_url=None,
            notes=None,
        )
    ]
    text = _render_entry_list_screen(items, "Записи темы: To Read")
    assert "Записи темы: To Read:" in text
    assert "Выберите запись кнопкой ниже." in text
    assert "Example title [New]" not in text


def test_render_topic_entries_list_screen_empty_uses_short_message() -> None:
    text = _render_entry_list_screen([], "Записи темы: Codex")
    assert text == "Записи темы: Codex:\nЗаписей не найдено."


def test_render_entry_list_screen_empty_contains_next_steps() -> None:
    text = _render_entry_list_screen([], "Статус Verified", page=0)
    assert "Записей не найдено." in text
    assert "Что можно сделать дальше:" in text
    assert "выбрать другой статус" in text


def test_add_topic_picker_keyboard_contains_topic_callbacks() -> None:
    topics = [
        TopicDTO(id="11111111-1111-1111-1111-111111111111", name="Root", full_path="Root", level=0),
        TopicDTO(id="22222222-2222-2222-2222-222222222222", name="Child", full_path="Root.Child", level=1),
    ]
    keyboard = build_add_topic_picker_keyboard(topics)
    topic_callbacks = [
        button.callback_data
        for row in keyboard.inline_keyboard[:-2]
        for button in row
    ]
    assert f"{ADD_TOPIC_PREFIX}11111111-1111-1111-1111-111111111111" in topic_callbacks
    assert f"{ADD_TOPIC_PREFIX}22222222-2222-2222-2222-222222222222" in topic_callbacks


def test_entry_results_keyboard_contains_entry_buttons() -> None:
    items = [
        EntryDetail(
            entry_id="11111111-1111-1111-1111-111111111111",
            title="Example title",
            status_name="New",
            topic_name="Python",
            original_url=None,
            normalized_url=None,
            notes=None,
        )
    ]
    keyboard = build_entry_results_keyboard(items, include_back_to_list=True)
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{ENTRY_VIEW_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert MENU_MAIN in callbacks


def test_entry_results_keyboard_supports_extra_rows() -> None:
    items = []
    extra_rows = build_topic_entries_actions_rows("11111111-1111-1111-1111-111111111111")
    keyboard = build_entry_results_keyboard(
        items,
        extra_rows=extra_rows,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{TOPIC_RENAME_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks


def test_entry_results_keyboard_can_merge_back_and_main_into_one_row() -> None:
    keyboard = build_entry_results_keyboard(
        [],
        back_callback=MENU_TOPICS,
        back_text="Назад к списку тем",
        merge_back_and_main=True,
    )
    callbacks_by_row = [[button.callback_data for button in row] for row in keyboard.inline_keyboard]
    assert [MENU_TOPICS, MENU_MAIN] in callbacks_by_row


def test_topic_entries_actions_rows_contains_manage_actions() -> None:
    rows = build_topic_entries_actions_rows("11111111-1111-1111-1111-111111111111")
    callbacks = [button.callback_data for row in rows for button in row]
    assert f"{TOPIC_RENAME_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{TOPIC_CREATE_CHILD_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{TOPIC_DELETE_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert len(rows) == 1
    assert len(rows[0]) == 3


def test_entry_results_keyboard_contains_pagination_callbacks() -> None:
    items = [
        EntryDetail(
            entry_id="11111111-1111-1111-1111-111111111111",
            title="Example title",
            status_name="New",
            topic_name="Python",
            original_url=None,
            normalized_url=None,
            notes=None,
        )
    ]
    keyboard = build_entry_results_keyboard(
        items,
        page=1,
        has_prev_page=True,
        has_next_page=True,
        page_callback_prefix=f"{LIST_PAGE_PREFIX}all:",
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{LIST_PAGE_PREFIX}all:0" in callbacks
    assert f"{LIST_PAGE_PREFIX}all:2" in callbacks


def test_entry_results_keyboard_contains_entry_back_context() -> None:
    items = [
        EntryDetail(
            entry_id="11111111-1111-1111-1111-111111111111",
            title="Example title",
            status_name="New",
            topic_name="Python",
            original_url=None,
            normalized_url=None,
            notes=None,
        )
    ]
    keyboard = build_entry_results_keyboard(
        items,
        entry_back_callback=f"{LIST_PAGE_PREFIX}new:1",
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{ENTRY_VIEW_PREFIX}11111111-1111-1111-1111-111111111111:{LIST_PAGE_PREFIX}new:1" in callbacks


def test_entry_results_keyboard_contains_topic_preview_callback() -> None:
    items = [
        EntryDetail(
            entry_id="11111111-1111-1111-1111-111111111111",
            title="Example title",
            status_name="New",
            topic_name="Python",
            original_url=None,
            normalized_url=None,
            notes=None,
        )
    ]
    keyboard = build_entry_results_keyboard(
        items,
        preview_callback_prefix=TOPIC_ENTRY_PREVIEW_PREFIX,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{TOPIC_ENTRY_PREVIEW_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert len(keyboard.inline_keyboard[0]) == 1


def test_entry_results_keyboard_does_not_contain_inline_delete_callback() -> None:
    items = [
        EntryDetail(
            entry_id="11111111-1111-1111-1111-111111111111",
            title="Example title",
            status_name="New",
            topic_name="Python",
            original_url=None,
            normalized_url=None,
            notes=None,
        )
    ]
    keyboard = build_entry_results_keyboard(items, preview_callback_prefix=TOPIC_ENTRY_PREVIEW_PREFIX)
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{TOPIC_ENTRY_PREVIEW_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{ENTRY_DELETE_PREFIX}11111111-1111-1111-1111-111111111111" not in callbacks
    assert len(keyboard.inline_keyboard[0]) == 1


def test_build_entry_preview_keyboard_contains_open_and_back() -> None:
    keyboard = build_entry_preview_keyboard(
        "11111111-1111-1111-1111-111111111111",
        entry_back_callback=f"{LIST_PAGE_PREFIX}new:1",
        back_callback=f"{LIST_PAGE_PREFIX}new:1",
        back_text="Назад к списку",
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{ENTRY_VIEW_PREFIX}11111111-1111-1111-1111-111111111111:{LIST_PAGE_PREFIX}new:1" in callbacks
    assert f"{ENTRY_DELETE_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{ENTRY_MOVE_MENU_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{LIST_PAGE_PREFIX}new:1" in callbacks
    assert len(keyboard.inline_keyboard[0]) == 3
    assert len(keyboard.inline_keyboard[1]) == 2


def test_entry_detail_keyboard_contains_change_status_action() -> None:
    keyboard = build_entry_detail_keyboard(
        "11111111-1111-1111-1111-111111111111",
        ["To Read", "Important"],
        include_back_to_list=True,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{ENTRY_STATUS_MENU_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{ENTRY_MOVE_MENU_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{ENTRY_DELETE_PREFIX}11111111-1111-1111-1111-111111111111" not in callbacks


def test_entry_move_topic_keyboard_for_existing_topics_contains_create_and_pick_actions() -> None:
    topics = [
        TopicDTO(id="11111111-1111-1111-1111-111111111111", name="Root", full_path="Root", level=0),
        TopicDTO(id="22222222-2222-2222-2222-222222222222", name="Child", full_path="Root.Child", level=1),
    ]
    keyboard = build_entry_move_topic_keyboard(
        topics=topics,
        mode="pick_existing",
        entry_id="33333333-3333-3333-3333-333333333333",
        entry_back_callback=f"{LIST_PAGE_PREFIX}new:1",
        page=1,
        has_prev_page=True,
        has_next_page=True,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert ENTRY_MOVE_CREATE_L0 in callbacks
    assert ENTRY_MOVE_CREATE_L1 in callbacks
    assert f"{ENTRY_MOVE_PICK_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{ENTRY_MOVE_PICK_PREFIX}22222222-2222-2222-2222-222222222222" in callbacks
    assert f"{ENTRY_MOVE_PAGE_PREFIX}0" in callbacks
    assert f"{ENTRY_MOVE_PAGE_PREFIX}2" in callbacks
    assert (
        f"{ENTRY_VIEW_PREFIX}33333333-3333-3333-3333-333333333333:{LIST_PAGE_PREFIX}new:1"
        in callbacks
    )


def test_entry_move_topic_keyboard_for_parent_pick_contains_parent_callbacks_only() -> None:
    topics = [
        TopicDTO(id="11111111-1111-1111-1111-111111111111", name="Root", full_path="Root", level=0),
    ]
    keyboard = build_entry_move_topic_keyboard(
        topics=topics,
        mode="pick_parent",
        entry_id="33333333-3333-3333-3333-333333333333",
        entry_back_callback=None,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert ENTRY_MOVE_CREATE_L0 not in callbacks
    assert ENTRY_MOVE_CREATE_L1 not in callbacks
    assert f"{ENTRY_MOVE_PICK_PREFIX}11111111-1111-1111-1111-111111111111" not in callbacks
    assert f"{ENTRY_MOVE_PARENT_PICK_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks


def test_entry_status_picker_keyboard_contains_status_actions() -> None:
    keyboard = build_entry_status_picker_keyboard(
        "11111111-1111-1111-1111-111111111111",
        ["To Read", "Important"],
        entry_back_callback=f"{LIST_PAGE_PREFIX}new:1",
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{ENTRY_STATUS_PREFIX}11111111-1111-1111-1111-111111111111:To Read" in callbacks
    assert f"{ENTRY_STATUS_PREFIX}11111111-1111-1111-1111-111111111111:Important" in callbacks
    assert f"{ENTRY_VIEW_PREFIX}11111111-1111-1111-1111-111111111111:{LIST_PAGE_PREFIX}new:1" in callbacks


def test_entry_delete_confirm_keyboard_contains_confirm_and_cancel_actions() -> None:
    keyboard = build_entry_delete_confirm_keyboard(
        "11111111-1111-1111-1111-111111111111",
        entry_back_callback=f"{LIST_PAGE_PREFIX}new:1",
        back_callback=f"{LIST_PAGE_PREFIX}new:1",
        back_text="Назад к списку",
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{ENTRY_DELETE_CONFIRM_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{ENTRY_VIEW_PREFIX}11111111-1111-1111-1111-111111111111:{LIST_PAGE_PREFIX}new:1" in callbacks
    assert f"{LIST_PAGE_PREFIX}new:1" in callbacks


def test_post_entry_delete_keyboard_contains_back_and_main() -> None:
    keyboard = build_post_entry_delete_keyboard(
        back_callback=MENU_TOPICS,
        back_text="Назад к списку тем",
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert MENU_TOPICS in callbacks
    assert MENU_MAIN in callbacks


def test_render_search_results_screen_prompts_selection() -> None:
    text = _render_search_results_screen([object()], "backup")
    assert "backup" in text
    assert "Выберите запись" in text


def test_render_search_results_screen_empty() -> None:
    text = _render_search_results_screen([], "unlikely_query")
    assert "ничего не найдено" in text.lower()
    assert "уточнить формулировку" in text.lower()


def test_render_entry_detail_screen_contains_fields() -> None:
    detail = EntryDetail(
        entry_id="11111111-1111-1111-1111-111111111111",
        title="Entry title",
        status_name="New",
        topic_name="Python",
        original_url="https://example.com",
        normalized_url="https://example.com",
        notes="some notes",
    )
    text = _render_entry_detail_screen(detail)
    assert "Карточка записи:" in text
    assert "Заголовок:" in text
    assert "Статус:" in text
    assert "Entry title" in text
    assert "Python" in text


def test_render_entry_detail_screen_compacts_long_notes() -> None:
    detail = EntryDetail(
        entry_id="11111111-1111-1111-1111-111111111111",
        title="Entry title",
        status_name="To Read",
        topic_name="To Read",
        original_url="https://example.com",
        normalized_url="https://example.com",
        notes="line one\nline two\n" + ("very long body " * 80),
    )
    text = _render_entry_detail_screen(detail)
    assert "Карточка записи:" in text
    assert "Заметки: line one line two" in text
    assert "… " not in text
    assert "…" in text
    assert len(text) < 700


def test_render_entry_preview_screen_returns_body_only() -> None:
    detail = EntryDetail(
        entry_id="11111111-1111-1111-1111-111111111111",
        title="Entry title",
        status_name="New",
        topic_name="Python",
        original_url="https://example.com",
        normalized_url="https://example.com",
        notes="notes body",
        description="description body",
    )
    text = _render_entry_preview_screen(detail)
    assert text == "description body"


def test_allowed_target_statuses_follow_status_machine() -> None:
    statuses = _allowed_target_statuses("New")
    assert "To Read" in statuses
    assert "Verified" not in statuses


def test_parse_entry_id_from_callback() -> None:
    parsed = _parse_entry_id_from_callback(
        f"{ENTRY_VIEW_PREFIX}11111111-1111-1111-1111-111111111111",
        ENTRY_VIEW_PREFIX,
    )
    assert str(parsed) == "11111111-1111-1111-1111-111111111111"


def test_parse_status_update_callback() -> None:
    parsed = _parse_status_update_callback(
        f"{ENTRY_STATUS_PREFIX}11111111-1111-1111-1111-111111111111:To Read"
    )
    assert parsed is not None
    entry_id, status_name = parsed
    assert str(entry_id) == "11111111-1111-1111-1111-111111111111"
    assert status_name == "To Read"


def test_parse_entry_view_callback_with_back_context() -> None:
    parsed = _parse_entry_view_callback(
        f"{ENTRY_VIEW_PREFIX}11111111-1111-1111-1111-111111111111:{SEARCH_PAGE_PREFIX}2"
    )
    assert parsed is not None
    entry_id, back_callback = parsed
    assert str(entry_id) == "11111111-1111-1111-1111-111111111111"
    assert back_callback == f"{SEARCH_PAGE_PREFIX}2"


def test_entry_view_chain_resolves_search_back_context_to_detail_keyboard() -> None:
    parsed = _parse_entry_view_callback(
        f"{ENTRY_VIEW_PREFIX}11111111-1111-1111-1111-111111111111:{SEARCH_PAGE_PREFIX}2"
    )
    assert parsed is not None
    _, entry_back_callback = parsed
    back_callback, back_text = _resolve_entry_back_action(entry_back_callback)

    keyboard = build_entry_detail_keyboard(
        "11111111-1111-1111-1111-111111111111",
        ["To Read"],
        back_callback=back_callback,
        back_text=back_text,
    )
    callback_map = {
        button.text: button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    }
    assert callback_map["Назад к поиску"] == f"{SEARCH_PAGE_PREFIX}2"


def test_entry_view_chain_resolves_collections_back_context_to_detail_keyboard() -> None:
    parsed = _parse_entry_view_callback(
        f"{ENTRY_VIEW_PREFIX}11111111-1111-1111-1111-111111111111:{MENU_COLLECTIONS}"
    )
    assert parsed is not None
    _, entry_back_callback = parsed
    back_callback, back_text = _resolve_entry_back_action(entry_back_callback)

    keyboard = build_entry_detail_keyboard(
        "11111111-1111-1111-1111-111111111111",
        ["To Read"],
        back_callback=back_callback,
        back_text=back_text,
    )
    callback_map = {
        button.text: button.callback_data
        for row in keyboard.inline_keyboard
        for button in row
    }
    assert callback_map["К коллекциям"] == MENU_COLLECTIONS


def test_resolve_entry_back_action_for_search_page() -> None:
    callback, text = _resolve_entry_back_action(f"{SEARCH_PAGE_PREFIX}2")
    assert callback == f"{SEARCH_PAGE_PREFIX}2"
    assert text == "Назад к поиску"


def test_resolve_entry_back_action_for_topic_entries_page() -> None:
    callback, text = _resolve_entry_back_action(
        f"{TOPIC_ENTRIES_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:2"
    )
    assert callback == f"{TOPIC_ENTRIES_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:2"
    assert text == "Назад к записям"


def test_resolve_entry_back_action_for_topic_view_page() -> None:
    callback, text = _resolve_entry_back_action(
        f"{TOPIC_VIEW_PREFIX}11111111-1111-1111-1111-111111111111"
    )
    assert callback == f"{TOPIC_VIEW_PREFIX}11111111-1111-1111-1111-111111111111"
    assert text == "Назад к теме"


def test_resolve_entry_back_action_for_topics_menu() -> None:
    callback, text = _resolve_entry_back_action(MENU_TOPICS)
    assert callback == MENU_TOPICS
    assert text == "Назад к списку тем"


def test_resolve_topic_entries_back_action_for_to_read_topic() -> None:
    topic = TopicDTO(
        id="11111111-1111-1111-1111-111111111111",
        name="To Read",
        full_path="to_read",
        level=0,
    )
    callback, text = _resolve_topic_entries_back_action(topic)
    assert callback == MENU_TOPICS
    assert text == "Назад к списку тем"


def test_resolve_topic_entries_back_action_for_regular_topic() -> None:
    topic = TopicDTO(
        id="11111111-1111-1111-1111-111111111111",
        name="Python",
        full_path="Programming.Python",
        level=1,
    )
    callback, text = _resolve_topic_entries_back_action(topic)
    assert callback == MENU_TOPICS
    assert text == "Назад к списку тем"


def test_resolve_entry_back_action_for_list_page() -> None:
    callback, text = _resolve_entry_back_action(f"{LIST_PAGE_PREFIX}verified:3")
    assert callback == f"{LIST_PAGE_PREFIX}verified:3"
    assert text == "Назад к списку"


def test_resolve_entry_back_action_for_collections() -> None:
    callback, text = _resolve_entry_back_action(MENU_COLLECTIONS)
    assert callback == MENU_COLLECTIONS
    assert text == "К коллекциям"


def test_resolve_entry_back_action_for_unknown_callback_fallbacks_to_filters() -> None:
    callback, text = _resolve_entry_back_action("unexpected:callback")
    assert callback == MENU_LIST
    assert text == "Назад к фильтрам"


def test_resolve_entry_back_callback_from_state_prefers_topic_entries_page() -> None:
    callback = _resolve_entry_back_callback_from_state(
        {"topic_entries_back_callback": f"{TOPIC_ENTRIES_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:2"}
    )
    assert callback == f"{TOPIC_ENTRIES_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:2"


def test_resolve_entry_back_callback_from_state_falls_back_to_topic_view() -> None:
    callback = _resolve_entry_back_callback_from_state(
        {"topic_view_id": "11111111-1111-1111-1111-111111111111"}
    )
    assert callback == f"{TOPIC_VIEW_PREFIX}11111111-1111-1111-1111-111111111111"


def test_resolve_entry_back_callback_from_state_uses_list_page_context() -> None:
    callback = _resolve_entry_back_callback_from_state(
        {"list_entries_back_callback": f"{LIST_PAGE_PREFIX}new:3"}
    )
    assert callback == f"{LIST_PAGE_PREFIX}new:3"


def test_resolve_entry_action_back_context_uses_entry_back_text_override() -> None:
    raw_callback, callback, text = _resolve_entry_action_back_context(
        {
            "entry_back_callback": f"{SEARCH_PAGE_PREFIX}1",
            "entry_back_text": "Назад в результаты",
        }
    )
    assert raw_callback == f"{SEARCH_PAGE_PREFIX}1"
    assert callback == f"{SEARCH_PAGE_PREFIX}1"
    assert text == "Назад в результаты"


def test_resolve_entry_action_back_context_falls_back_to_state_inference() -> None:
    raw_callback, callback, text = _resolve_entry_action_back_context(
        {"topic_entries_back_callback": f"{TOPIC_ENTRIES_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:0"}
    )
    assert raw_callback == f"{TOPIC_ENTRIES_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:0"
    assert callback == raw_callback
    assert text == "Назад к записям"


def test_resolve_status_back_action_uses_state_stored_text_override() -> None:
    callback, text = _resolve_status_back_action(
        {
            "entry_back_callback": f"{SEARCH_PAGE_PREFIX}1",
            "entry_back_text": "Назад в результаты",
        }
    )
    assert callback == f"{SEARCH_PAGE_PREFIX}1"
    assert text == "Назад в результаты"


def test_resolve_status_back_action_fallbacks_to_default_when_state_is_incomplete() -> None:
    callback, text = _resolve_status_back_action({})
    assert callback == MENU_LIST
    assert text == "Назад к фильтрам"


def test_parse_list_page_callback() -> None:
    parsed = _parse_list_page_callback(f"{LIST_PAGE_PREFIX}new:2")
    assert parsed == ("new", 2)


def test_parse_list_page_callback_rejects_unknown_kind() -> None:
    parsed = _parse_list_page_callback(f"{LIST_PAGE_PREFIX}archived:2")
    assert parsed is None


def test_parse_page_callback() -> None:
    page = _parse_page_callback(f"{SEARCH_PAGE_PREFIX}3", SEARCH_PAGE_PREFIX)
    assert page == 3


def test_parse_page_callback_for_topics() -> None:
    page = _parse_page_callback(f"{TOPICS_PAGE_PREFIX}4", TOPICS_PAGE_PREFIX)
    assert page == 4


def test_parse_topic_entries_page_callback() -> None:
    parsed = _parse_topic_entries_page_callback(
        f"{TOPIC_ENTRIES_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:3"
    )
    assert parsed is not None
    topic_id, page = parsed
    assert str(topic_id) == "11111111-1111-1111-1111-111111111111"
    assert page == 3


def test_topics_keyboard_contains_create_and_topic_callbacks() -> None:
    topics = [
        TopicDTO(id="11111111-1111-1111-1111-111111111111", name="Root", full_path="Root", level=0),
        TopicDTO(id="22222222-2222-2222-2222-222222222222", name="Child", full_path="Root.Child", level=1),
    ]
    keyboard = build_topics_keyboard(topics)
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert MENU_TOPIC_CREATE in callbacks
    assert f"{TOPIC_VIEW_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert "● Child" in labels


def test_topics_keyboard_contains_pagination_callbacks() -> None:
    topics = [
        TopicDTO(id="11111111-1111-1111-1111-111111111111", name="Root", full_path="Root", level=0),
    ]
    keyboard = build_topics_keyboard(
        topics,
        page=1,
        has_prev_page=True,
        has_next_page=True,
        page_callback_prefix=TOPICS_PAGE_PREFIX,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{TOPICS_PAGE_PREFIX}0" in callbacks
    assert f"{TOPICS_PAGE_PREFIX}2" in callbacks


def test_topics_tree_keyboard_contains_toggle_and_topic_callbacks() -> None:
    topic_rows = [
        (
            TopicDTO(
                id="11111111-1111-1111-1111-111111111111",
                name="Neural Networks / AI",
                full_path="neural_networks_ai",
                level=0,
            ),
            True,
            False,
        ),
        (
            TopicDTO(
                id="22222222-2222-2222-2222-222222222222",
                name="Codex",
                full_path="neural_networks_ai.codex",
                level=1,
            ),
            False,
            False,
        ),
    ]

    keyboard = build_topics_tree_keyboard(
        topic_rows,
        page=0,
        has_prev_page=False,
        has_next_page=False,
        page_callback_prefix=TOPICS_PAGE_PREFIX,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{TOPIC_TOGGLE_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{TOPIC_VIEW_PREFIX}22222222-2222-2222-2222-222222222222" in callbacks
    labels = [button.text for row in keyboard.inline_keyboard for button in row]
    assert any("Neural Networks / AI" in label for label in labels)


def test_topics_tree_keyboard_groups_subtopics_by_three_buttons_per_row() -> None:
    topic_rows = [
        (
            TopicDTO(
                id="11111111-1111-1111-1111-111111111111",
                name="Neural Networks / AI",
                full_path="neural_networks_ai",
                level=0,
            ),
            True,
            True,
        ),
        (
            TopicDTO(id="22222222-2222-2222-2222-222222222222", name="A", full_path="p.a", level=1),
            False,
            False,
        ),
        (
            TopicDTO(id="33333333-3333-3333-3333-333333333333", name="B", full_path="p.b", level=1),
            False,
            False,
        ),
        (
            TopicDTO(id="44444444-4444-4444-4444-444444444444", name="C", full_path="p.c", level=1),
            False,
            False,
        ),
        (
            TopicDTO(id="55555555-5555-5555-5555-555555555555", name="D", full_path="p.d", level=1),
            False,
            False,
        ),
    ]

    keyboard = build_topics_tree_keyboard(
        topic_rows,
        page=0,
        has_prev_page=False,
        has_next_page=False,
    )
    topic_rows_only = [
        row
        for row in keyboard.inline_keyboard
        if any((button.callback_data or "").startswith((TOPIC_TOGGLE_PREFIX, TOPIC_VIEW_PREFIX)) for button in row)
    ]

    # 1 row for parent + 2 rows for 4 subtopics (3 + 1).
    assert len(topic_rows_only) == 3
    assert len(topic_rows_only[0]) == 1
    assert len(topic_rows_only[1]) == 3
    assert len(topic_rows_only[2]) == 1


def test_topics_tree_keyboard_keeps_l0_leaf_as_separate_button() -> None:
    topic_rows = [
        (
            TopicDTO(
                id="11111111-1111-1111-1111-111111111111",
                name="Neural Networks / AI",
                full_path="neural_networks_ai",
                level=0,
            ),
            True,
            True,
        ),
        (
            TopicDTO(id="22222222-2222-2222-2222-222222222222", name="Codex", full_path="p.codex", level=1),
            False,
            False,
        ),
        (
            TopicDTO(
                id="33333333-3333-3333-3333-333333333333",
                name="Soft_misc",
                full_path="soft_misc",
                level=0,
            ),
            False,
            False,
        ),
    ]
    keyboard = build_topics_tree_keyboard(topic_rows, page=0)
    labels_by_row = [[button.text for button in row] for row in keyboard.inline_keyboard]
    assert any("Soft_misc" in row[0] and len(row) == 1 for row in labels_by_row)


def test_topics_tree_keyboard_contains_pagination_callbacks() -> None:
    topic_rows = [
        (
            TopicDTO(id="11111111-1111-1111-1111-111111111111", name="Root", full_path="Root", level=0),
            False,
            False,
        )
    ]
    keyboard = build_topics_tree_keyboard(
        topic_rows,
        page=2,
        has_prev_page=True,
        has_next_page=True,
        page_callback_prefix=TOPICS_PAGE_PREFIX,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{TOPICS_PAGE_PREFIX}1" in callbacks
    assert f"{TOPICS_PAGE_PREFIX}3" in callbacks


def test_topic_detail_keyboard_contains_child_create_and_rename_actions() -> None:
    keyboard = build_topic_detail_keyboard("11111111-1111-1111-1111-111111111111")
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{TOPIC_ENTRIES_PAGE_PREFIX}11111111-1111-1111-1111-111111111111:0" in callbacks
    assert f"{TOPIC_CREATE_CHILD_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{TOPIC_RENAME_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{TOPIC_DELETE_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert MENU_TOPICS in callbacks


def test_topic_detail_keyboard_contains_quick_entry_buttons() -> None:
    entries = [
        EntryDetail(
            entry_id="22222222-2222-2222-2222-222222222222",
            title="Telegram Bot API Overview",
            status_name="New",
            topic_name="To Read",
            original_url="https://core.telegram.org/bots/api",
            normalized_url="https://core.telegram.org/bots/api",
            notes=None,
        )
    ]
    keyboard = build_topic_detail_keyboard(
        "11111111-1111-1111-1111-111111111111",
        quick_entries=entries,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{TOPIC_ENTRY_PREVIEW_PREFIX}22222222-2222-2222-2222-222222222222" in callbacks


def test_topic_delete_confirm_keyboard_contains_confirm_and_cancel() -> None:
    keyboard = build_topic_delete_confirm_keyboard("11111111-1111-1111-1111-111111111111")
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{TOPIC_DELETE_CONFIRM_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks
    assert f"{TOPIC_VIEW_PREFIX}11111111-1111-1111-1111-111111111111" in callbacks


def test_collections_keyboard_contains_collection_callbacks() -> None:
    collections = [
        SavedViewDTO(
            id="33333333-3333-3333-3333-333333333333",
            name="New items",
            filter_snapshot={"status_name": "New", "topic_id": None, "limit": 20},
        )
    ]
    keyboard = build_collections_keyboard(collections)
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{COLLECTION_VIEW_PREFIX}33333333-3333-3333-3333-333333333333" in callbacks
    assert MENU_COLLECTIONS in callbacks


def test_collections_keyboard_contains_pagination_callbacks() -> None:
    collections = [
        SavedViewDTO(
            id="33333333-3333-3333-3333-333333333333",
            name="New items",
            filter_snapshot={"status_name": "New", "topic_id": None, "limit": 20},
        )
    ]
    keyboard = build_collections_keyboard(
        collections,
        page=2,
        has_prev_page=True,
        has_next_page=True,
        page_callback_prefix=COLLECTIONS_PAGE_PREFIX,
    )
    callbacks = [button.callback_data for row in keyboard.inline_keyboard for button in row]
    assert f"{COLLECTIONS_PAGE_PREFIX}1" in callbacks
    assert f"{COLLECTIONS_PAGE_PREFIX}3" in callbacks


def test_render_topic_detail_screen_contains_fields() -> None:
    topic = TopicDTO(
        id="11111111-1111-1111-1111-111111111111",
        name="Python",
        full_path="Programming.Python",
        level=1,
    )
    text = _render_topic_detail_screen(topic)
    assert "Карточка темы:" in text
    assert "Python" in text
    assert "Programming.Python" in text


def test_render_topic_detail_screen_contains_topic_entries_preview() -> None:
    topic = TopicDTO(
        id="11111111-1111-1111-1111-111111111111",
        name="To Read",
        full_path="to_read",
        level=0,
    )
    entries = [
        EntryDetail(
            entry_id="22222222-2222-2222-2222-222222222222",
            title="Qwen3.6 Plus Preview появился на OpenRouter",
            status_name="To Read",
            topic_name="To Read",
            original_url="https://example.com/post",
            normalized_url="https://example.com/post",
            notes="note",
        )
    ]

    text = _render_topic_detail_screen(topic, entries=entries)
    assert "Последние записи в теме:" in text
    assert "Qwen3.6 Plus Preview появился на OpenRouter" in text
    assert "Ссылка: https://example.com/post" in text


def test_render_collection_result_screen_contains_summary() -> None:
    collection = SavedViewDTO(
        id="33333333-3333-3333-3333-333333333333",
        name="Verified items",
        filter_snapshot={"status_name": "Verified", "topic_id": None, "limit": 10},
    )
    items = [
        EntryDetail(
            entry_id="11111111-1111-1111-1111-111111111111",
            title="Entry title",
            status_name="Verified",
            topic_name="Python",
            original_url=None,
            normalized_url=None,
            notes=None,
        )
    ]
    text = _render_collection_result_screen(collection, items)
    assert "Коллекция: Verified items" in text
    assert "status: Verified" in text
    assert "Выберите запись" in text


def test_render_collection_result_screen_empty_contains_guidance() -> None:
    collection = SavedViewDTO(
        id="33333333-3333-3333-3333-333333333333",
        name="Verified items",
        filter_snapshot={"status_name": "Verified", "topic_id": None, "limit": 10},
    )
    text = _render_collection_result_screen(collection, [])
    assert "записей не найдено" in text.lower()
    assert "увеличьте лимит" in text.lower()


def test_render_backups_list_screen_contains_rows() -> None:
    class BackupRow:
        def __init__(self, id: str, filename: str, restore_tested_at: str | None) -> None:
            self.id = id
            self.filename = filename
            self.restore_tested_at = restore_tested_at

    text = _render_backups_list_screen([BackupRow("id-1", "file.dump", None)])
    assert "Backups:" in text
    assert "file.dump" in text


def test_format_restore_progress_checkpoint_contains_elapsed_and_timeout_percent() -> None:
    text = _format_restore_progress_checkpoint(elapsed_sec=120, timeout_sec=600)
    assert "Restore в процессе." in text
    assert "2 мин 0 сек" in text
    assert "20% от таймаута" in text


def test_format_restore_failure_message_for_timeout_with_compact_stderr() -> None:
    exc = subprocess.TimeoutExpired(
        cmd=["pg_restore", "--clean"],
        timeout=300,
        stderr="fatal: connection reset by peer\n" * 20,
    )
    text = _format_restore_failure_message(exc)
    assert "Restore failed." in text
    assert "timeout after 300 sec" in text
    assert "stderr=" in text
    assert len(text) < 500


def test_format_restore_failure_message_for_nonzero_exit() -> None:
    exc = subprocess.CalledProcessError(
        returncode=2,
        cmd=["pg_restore", "--clean", "-d", "postgresql://user@localhost/db"],
        output="processing item",
        stderr="ERROR: relation does not exist",
    )
    text = _format_restore_failure_message(exc)
    assert "pg_restore exited with code 2" in text
    assert "stderr=ERROR: relation does not exist" in text
    assert "cmd=pg_restore --clean -d postgresql://user@localhost/db" in text
