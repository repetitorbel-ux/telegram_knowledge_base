from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from kb_bot.bot.ui.callbacks import (
    ADD_TOPIC_PREFIX,
    BACKUP_RESTORE_ACK_PREFIX,
    BACKUP_RESTORE_EXEC_PREFIX,
    BACKUP_RESTORE_PICK_PREFIX,
    COLLECTION_VIEW_PREFIX,
    ENTRY_DELETE_CONFIRM_PREFIX,
    ENTRY_DELETE_PREFIX,
    ENTRY_STATUS_MENU_PREFIX,
    ENTRY_STATUS_PREFIX,
    ENTRY_VIEW_PREFIX,
    LIST_ALL,
    LIST_NEW,
    LIST_TO_READ,
    LIST_VERIFIED,
    MENU_ADD,
    MENU_BACKUPS,
    MENU_BACKUP_CREATE,
    MENU_BACKUP_LIST,
    MENU_BACKUP_RESTORE,
    MENU_CANCEL_FLOW,
    MENU_COLLECTIONS,
    MENU_EXPORT_CSV,
    MENU_EXPORT_JSON,
    MENU_HELP,
    MENU_IMPORT_EXPORT,
    MENU_IMPORT_START,
    MENU_LIST,
    MENU_MAIN,
    MENU_SEARCH,
    MENU_STATS,
    MENU_TOPIC_CREATE,
    TOPIC_ENTRIES_PAGE_PREFIX,
    TOPIC_CREATE_CHILD_PREFIX,
    MENU_TOPICS,
    TOPIC_DELETE_CONFIRM_PREFIX,
    TOPIC_DELETE_PREFIX,
    TOPIC_ENTRY_PREVIEW_PREFIX,
    TOPIC_RENAME_PREFIX,
    TOPIC_VIEW_PREFIX,
)
from kb_bot.domain.dto import TopicDTO
from kb_bot.services.collection_service import SavedViewDTO
from kb_bot.services.query_service import EntryDetail


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Добавить", callback_data=MENU_ADD),
                InlineKeyboardButton(text="Поиск", callback_data=MENU_SEARCH),
            ],
            [
                InlineKeyboardButton(text="Список", callback_data=MENU_LIST),
                InlineKeyboardButton(text="Темы", callback_data=MENU_TOPICS),
            ],
            [
                InlineKeyboardButton(text="Коллекции", callback_data=MENU_COLLECTIONS),
                InlineKeyboardButton(text="Импорт/экспорт", callback_data=MENU_IMPORT_EXPORT),
            ],
            [
                InlineKeyboardButton(text="Бэкапы", callback_data=MENU_BACKUPS),
                InlineKeyboardButton(text="Статистика", callback_data=MENU_STATS),
            ],
            [InlineKeyboardButton(text="Подсказка по командам", callback_data=MENU_HELP)],
        ]
    )


def build_home_navigation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)]]
    )


def build_flow_navigation_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Отмена", callback_data=MENU_CANCEL_FLOW)],
            [InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)],
        ]
    )


def build_list_filters_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Все", callback_data=LIST_ALL),
                InlineKeyboardButton(text="New", callback_data=LIST_NEW),
            ],
            [
                InlineKeyboardButton(text="To Read", callback_data=LIST_TO_READ),
                InlineKeyboardButton(text="Verified", callback_data=LIST_VERIFIED),
            ],
            [InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)],
        ]
    )


def build_add_topic_picker_keyboard(topics: list[TopicDTO]) -> InlineKeyboardMarkup:
    rows = []
    for topic in topics:
        label = _render_topic_button_label(topic)
        rows.append(
            [
                InlineKeyboardButton(
                    text=label,
                    callback_data=f"{ADD_TOPIC_PREFIX}{topic.id}",
                )
            ]
        )

    rows.extend(build_flow_navigation_keyboard().inline_keyboard)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _render_topic_button_label(topic: TopicDTO) -> str:
    if topic.level <= 0:
        label = topic.name
    else:
        label = f"● {topic.name}"
    return label[:64]


def build_entry_results_keyboard(
    items: list[object],
    *,
    include_back_to_list: bool = False,
    back_callback: str | None = None,
    back_text: str | None = None,
    page: int | None = None,
    has_prev_page: bool = False,
    has_next_page: bool = False,
    page_callback_prefix: str | None = None,
    entry_back_callback: str | None = None,
    preview_callback_prefix: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        entry_id = _extract_entry_id(item)
        if entry_id is None:
            continue
        if preview_callback_prefix:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=_render_entry_button_label(item),
                        callback_data=f"{preview_callback_prefix}{entry_id}",
                    ),
                ]
            )
            continue

        rows.append(
            [
                InlineKeyboardButton(
                    text=_render_entry_button_label(item),
                    callback_data=_build_entry_view_callback(entry_id, entry_back_callback),
                )
            ]
        )

    if page is not None and page_callback_prefix and (has_prev_page or has_next_page):
        pagination_row: list[InlineKeyboardButton] = []
        if has_prev_page:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀ Назад",
                    callback_data=f"{page_callback_prefix}{page - 1}",
                )
            )
        if has_next_page:
            pagination_row.append(
                InlineKeyboardButton(
                    text="Далее ▶",
                    callback_data=f"{page_callback_prefix}{page + 1}",
                )
            )
        if pagination_row:
            rows.append(pagination_row)

    if include_back_to_list:
        rows.append([InlineKeyboardButton(text="К быстрым спискам", callback_data=MENU_LIST)])
    if back_callback and back_text:
        rows.append([InlineKeyboardButton(text=back_text, callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_entry_detail_keyboard(
    entry_id: str,
    allowed_statuses: list[str],
    *,
    include_back_to_list: bool = False,
    back_callback: str | None = None,
    back_text: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []
    if allowed_statuses:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Изменить статус",
                    callback_data=f"{ENTRY_STATUS_MENU_PREFIX}{entry_id}",
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="Удалить запись",
                callback_data=f"{ENTRY_DELETE_PREFIX}{entry_id}",
            )
        ]
    )

    if include_back_to_list:
        rows.append([InlineKeyboardButton(text="К быстрым спискам", callback_data=MENU_LIST)])
    if back_callback and back_text:
        rows.append([InlineKeyboardButton(text=back_text, callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_entry_status_picker_keyboard(
    entry_id: str,
    allowed_statuses: list[str],
    *,
    entry_back_callback: str | None = None,
    back_callback: str | None = None,
    back_text: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for status_name in allowed_statuses:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"Статус: {status_name}",
                    callback_data=f"{ENTRY_STATUS_PREFIX}{entry_id}:{status_name}",
                )
            ]
        )

    rows.append(
        [
            InlineKeyboardButton(
                text="Назад к карточке",
                callback_data=_build_entry_view_callback(entry_id, entry_back_callback),
            )
        ]
    )
    if back_callback and back_text:
        rows.append([InlineKeyboardButton(text=back_text, callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_entry_delete_confirm_keyboard(
    entry_id: str,
    *,
    entry_back_callback: str | None = None,
    back_callback: str | None = None,
    back_text: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="Подтвердить удаление",
                callback_data=f"{ENTRY_DELETE_CONFIRM_PREFIX}{entry_id}",
            )
        ],
        [
            InlineKeyboardButton(
                text="Отмена",
                callback_data=_build_entry_view_callback(entry_id, entry_back_callback),
            )
        ],
    ]
    if back_callback and back_text:
        rows.append([InlineKeyboardButton(text=back_text, callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_post_entry_delete_keyboard(
    *,
    back_callback: str | None = None,
    back_text: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if back_callback and back_text:
        rows.append([InlineKeyboardButton(text=back_text, callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_entry_preview_keyboard(
    entry_id: str,
    *,
    entry_back_callback: str | None = None,
    back_callback: str | None = None,
    back_text: str | None = None,
) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="Открыть карточку",
                callback_data=_build_entry_view_callback(entry_id, entry_back_callback),
            )
        ]
    ]
    if back_callback and back_text:
        rows.append([InlineKeyboardButton(text=back_text, callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _render_entry_button_label(item: object) -> str:
    label = f"{item.title} [{item.status_name}]"
    return label[:64]


def _extract_entry_id(item: object):
    entry_id = getattr(item, "entry_id", None)
    if entry_id is not None:
        return entry_id
    return getattr(item, "id", None)


def _build_entry_view_callback(entry_id, entry_back_callback: str | None) -> str:
    base = f"{ENTRY_VIEW_PREFIX}{entry_id}"
    if not entry_back_callback:
        return base
    candidate = f"{base}:{entry_back_callback}"
    if len(candidate) <= 64:
        return candidate
    return base


def build_topics_keyboard(
    topics: list[TopicDTO],
    *,
    page: int | None = None,
    has_prev_page: bool = False,
    has_next_page: bool = False,
    page_callback_prefix: str | None = None,
) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Добавить корневую тему", callback_data=MENU_TOPIC_CREATE)]]
    for topic in topics:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_render_topic_button_label(topic),
                    callback_data=f"{TOPIC_VIEW_PREFIX}{topic.id}",
                )
            ]
        )
    if page is not None and page_callback_prefix and (has_prev_page or has_next_page):
        pagination_row: list[InlineKeyboardButton] = []
        if has_prev_page:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀ Назад",
                    callback_data=f"{page_callback_prefix}{page - 1}",
                )
            )
        if has_next_page:
            pagination_row.append(
                InlineKeyboardButton(
                    text="Далее ▶",
                    callback_data=f"{page_callback_prefix}{page + 1}",
                )
            )
        if pagination_row:
            rows.append(pagination_row)
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_topic_detail_keyboard(
    topic_id: str,
    *,
    topic_entries_callback: str | None = None,
    quick_entries: list[EntryDetail] | None = None,
) -> InlineKeyboardMarkup:
    entries_callback = topic_entries_callback or f"{TOPIC_ENTRIES_PAGE_PREFIX}{topic_id}:0"
    rows: list[list[InlineKeyboardButton]] = []
    if quick_entries:
        for entry in quick_entries[:5]:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=_render_entry_button_label(entry),
                        callback_data=f"{TOPIC_ENTRY_PREVIEW_PREFIX}{entry.entry_id}",
                    ),
                ]
            )

    rows.extend(
        [
            [InlineKeyboardButton(text="Открыть все записи темы", callback_data=entries_callback)],
            [InlineKeyboardButton(text="Добавить подтему", callback_data=f"{TOPIC_CREATE_CHILD_PREFIX}{topic_id}")],
            [InlineKeyboardButton(text="Переименовать тему", callback_data=f"{TOPIC_RENAME_PREFIX}{topic_id}")],
            [InlineKeyboardButton(text="Удалить тему", callback_data=f"{TOPIC_DELETE_PREFIX}{topic_id}")],
            [InlineKeyboardButton(text="Назад к списку тем", callback_data=MENU_TOPICS)],
            [InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)],
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_topic_delete_confirm_keyboard(topic_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Подтвердить удаление",
                    callback_data=f"{TOPIC_DELETE_CONFIRM_PREFIX}{topic_id}",
                )
            ],
            [InlineKeyboardButton(text="Отмена", callback_data=f"{TOPIC_VIEW_PREFIX}{topic_id}")],
            [InlineKeyboardButton(text="Назад к списку тем", callback_data=MENU_TOPICS)],
            [InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)],
        ]
    )


def build_collections_keyboard(
    collections: list[SavedViewDTO],
    *,
    page: int | None = None,
    has_prev_page: bool = False,
    has_next_page: bool = False,
    page_callback_prefix: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []
    for collection in collections:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_render_collection_button_label(collection),
                    callback_data=f"{COLLECTION_VIEW_PREFIX}{collection.id}",
                )
            ]
        )
    if page is not None and page_callback_prefix and (has_prev_page or has_next_page):
        pagination_row: list[InlineKeyboardButton] = []
        if has_prev_page:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀ Назад",
                    callback_data=f"{page_callback_prefix}{page - 1}",
                )
            )
        if has_next_page:
            pagination_row.append(
                InlineKeyboardButton(
                    text="Далее ▶",
                    callback_data=f"{page_callback_prefix}{page + 1}",
                )
            )
        if pagination_row:
            rows.append(pagination_row)
    rows.append([InlineKeyboardButton(text="Обновить список", callback_data=MENU_COLLECTIONS)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _render_collection_button_label(collection: SavedViewDTO) -> str:
    return collection.name[:64]


def build_import_export_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Импорт CSV/JSON", callback_data=MENU_IMPORT_START)],
            [
                InlineKeyboardButton(text="Экспорт CSV", callback_data=MENU_EXPORT_CSV),
                InlineKeyboardButton(text="Экспорт JSON", callback_data=MENU_EXPORT_JSON),
            ],
            [InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)],
        ]
    )


def build_backups_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Создать backup", callback_data=MENU_BACKUP_CREATE)],
            [InlineKeyboardButton(text="Показать backups", callback_data=MENU_BACKUP_LIST)],
            [InlineKeyboardButton(text="Восстановить backup (2 шага)", callback_data=MENU_BACKUP_RESTORE)],
            [InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)],
        ]
    )


def build_backup_restore_picker_keyboard(rows: list[object]) -> InlineKeyboardMarkup:
    buttons = []
    for row in rows[:10]:
        backup_id = getattr(row, "id", None)
        if backup_id is None:
            continue
        filename = str(getattr(row, "filename", "backup"))
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"Restore: {filename[:45]}",
                    callback_data=f"{BACKUP_RESTORE_PICK_PREFIX}{backup_id}",
                )
            ]
        )

    buttons.append([InlineKeyboardButton(text="К бэкапам", callback_data=MENU_BACKUPS)])
    buttons.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def build_backup_restore_warning_keyboard(backup_id: str, *, final: bool = False) -> InlineKeyboardMarkup:
    confirm_prefix = BACKUP_RESTORE_EXEC_PREFIX if final else BACKUP_RESTORE_ACK_PREFIX
    confirm_text = "Подтвердить restore" if final else "Я понимаю риск, продолжить"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=confirm_text, callback_data=f"{confirm_prefix}{backup_id}")],
            [InlineKeyboardButton(text="Отмена", callback_data=MENU_BACKUPS)],
            [InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)],
        ]
    )
