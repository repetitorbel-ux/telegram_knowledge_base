from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from textwrap import wrap

from kb_bot.bot.ui.callbacks import (
    ADD_TOPIC_PREFIX,
    BACKUP_RESTORE_ACK_PREFIX,
    BACKUP_RESTORE_EXEC_PREFIX,
    BACKUP_RESTORE_PICK_PREFIX,
    COLLECTION_VIEW_PREFIX,
    ENTRY_DELETE_CONFIRM_PREFIX,
    ENTRY_DELETE_PREFIX,
    ENTRY_EDIT_FIELD_PREFIX,
    ENTRY_EDIT_MENU_PREFIX,
    ENTRY_MOVE_CREATE_L0,
    ENTRY_MOVE_CREATE_L1,
    ENTRY_MOVE_PAGE_PREFIX,
    ENTRY_MOVE_PARENT_PICK_PREFIX,
    ENTRY_MOVE_PICK_PREFIX,
    ENTRY_MOVE_MENU_PREFIX,
    ENTRY_TOPICS_MENU_PREFIX,
    ENTRY_TOPIC_ADD_MENU_PREFIX,
    ENTRY_TOPIC_REMOVE_PICK_PREFIX,
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
    SEARCH_QUICK_PREFIX,
    SEARCH_REPEAT,
    MENU_STATS,
    MENU_TOPIC_CREATE,
    RELATED_PAGE_PREFIX,
    TOPIC_ENTRIES_PAGE_PREFIX,
    TOPIC_CREATE_CHILD_PREFIX,
    MENU_TOPICS,
    TOPIC_DELETE_CONFIRM_PREFIX,
    TOPIC_DELETE_PREFIX,
    TOPIC_ENTRY_PREVIEW_PREFIX,
    TOPIC_TOGGLE_PREFIX,
    TOPIC_RENAME_PREFIX,
    TOPIC_VIEW_PREFIX,
)
from kb_bot.domain.dto import TopicDTO
from kb_bot.services.collection_service import SavedViewDTO
from kb_bot.services.query_service import EntryDetail

MAIN_MENU_SEARCH_TEXT = "🔎 Поиск"
MAIN_MENU_NEW_TEXT = "📥 Новые"
MAIN_MENU_ADD_TEXT = "➕ Добавить"
MAIN_MENU_TOPICS_TEXT = "📚 Темы"
MAIN_MENU_LIST_TEXT = "📋 Список"
MAIN_MENU_STATS_TEXT = "📊 Статистика"
MAIN_MENU_COLLECTIONS_TEXT = "📦 Коллекции"
MAIN_MENU_EXPORT_TEXT = "📤 Экспорт"
MAIN_MENU_IMPORT_TEXT = "📥 Импорт"
MAIN_MENU_BACKUPS_TEXT = "💾 Бэкап"
MAIN_MENU_HELP_TEXT = "❓ Помощь"


def build_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=MAIN_MENU_SEARCH_TEXT, callback_data=MENU_SEARCH)],
            [
                InlineKeyboardButton(text=MAIN_MENU_NEW_TEXT, callback_data=LIST_NEW),
                InlineKeyboardButton(text=MAIN_MENU_ADD_TEXT, callback_data=MENU_ADD),
                InlineKeyboardButton(text=MAIN_MENU_TOPICS_TEXT, callback_data=MENU_TOPICS),
            ],
            [
                InlineKeyboardButton(text=MAIN_MENU_LIST_TEXT, callback_data=MENU_LIST),
                InlineKeyboardButton(text=MAIN_MENU_STATS_TEXT, callback_data=MENU_STATS),
                InlineKeyboardButton(text=MAIN_MENU_COLLECTIONS_TEXT, callback_data=MENU_COLLECTIONS),
            ],
            [
                InlineKeyboardButton(text=MAIN_MENU_EXPORT_TEXT, callback_data=MENU_IMPORT_EXPORT),
                InlineKeyboardButton(text=MAIN_MENU_IMPORT_TEXT, callback_data=MENU_IMPORT_START),
                InlineKeyboardButton(text=MAIN_MENU_BACKUPS_TEXT, callback_data=MENU_BACKUPS),
            ],
            [InlineKeyboardButton(text=MAIN_MENU_HELP_TEXT, callback_data=MENU_HELP)],
        ]
    )


def build_main_reply_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MAIN_MENU_SEARCH_TEXT)],
            [
                KeyboardButton(text=MAIN_MENU_NEW_TEXT),
                KeyboardButton(text=MAIN_MENU_ADD_TEXT),
                KeyboardButton(text=MAIN_MENU_TOPICS_TEXT),
            ],
            [
                KeyboardButton(text=MAIN_MENU_LIST_TEXT),
                KeyboardButton(text=MAIN_MENU_STATS_TEXT),
                KeyboardButton(text=MAIN_MENU_COLLECTIONS_TEXT),
            ],
            [
                KeyboardButton(text=MAIN_MENU_EXPORT_TEXT),
                KeyboardButton(text=MAIN_MENU_IMPORT_TEXT),
                KeyboardButton(text=MAIN_MENU_BACKUPS_TEXT),
            ],
            [KeyboardButton(text=MAIN_MENU_HELP_TEXT)],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Сообщение...",
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


def build_search_actions_keyboard(*, has_last_query: bool = False) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if has_last_query:
        rows.append([InlineKeyboardButton(text="Повторить последний запрос", callback_data=SEARCH_REPEAT)])

    rows.append(
        [
            InlineKeyboardButton(text="PostgreSQL", callback_data=f"{SEARCH_QUICK_PREFIX}pg"),
            InlineKeyboardButton(text="AI", callback_data=f"{SEARCH_QUICK_PREFIX}ai"),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(text="Backup", callback_data=f"{SEARCH_QUICK_PREFIX}backup"),
            InlineKeyboardButton(text="Infrastructure", callback_data=f"{SEARCH_QUICK_PREFIX}infra"),
        ]
    )
    rows.append([InlineKeyboardButton(text="Отмена", callback_data=MENU_CANCEL_FLOW)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
    extra_rows: list[list[InlineKeyboardButton]] | None = None,
    merge_back_and_main: bool = False,
    merge_pagination_and_back: bool = False,
    entries_per_row: int = 1,
    include_status_in_label: bool = True,
) -> InlineKeyboardMarkup:
    rows = []
    current_entry_row: list[InlineKeyboardButton] = []
    pagination_row: list[InlineKeyboardButton] | None = None
    entries_per_row = max(1, entries_per_row)
    for item in items:
        entry_id = _extract_entry_id(item)
        if entry_id is None:
            continue
        if preview_callback_prefix:
            current_entry_row.append(
                InlineKeyboardButton(
                    text=_render_entry_button_label(item, include_status=include_status_in_label),
                    callback_data=f"{preview_callback_prefix}{entry_id}",
                )
            )
        else:
            current_entry_row.append(
                InlineKeyboardButton(
                    text=_render_entry_button_label(item, include_status=include_status_in_label),
                    callback_data=_build_entry_view_callback(entry_id, entry_back_callback),
                )
            )

        if len(current_entry_row) == entries_per_row:
            rows.append(current_entry_row)
            current_entry_row = []

    if current_entry_row:
        rows.append(current_entry_row)

    if page is not None and page_callback_prefix and (has_prev_page or has_next_page):
        pagination_row = []
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

    if extra_rows:
        rows.extend(extra_rows)
    if include_back_to_list:
        rows.append([InlineKeyboardButton(text="К быстрым спискам", callback_data=MENU_LIST)])
    if back_callback and back_text:
        if merge_back_and_main:
            rows.append(
                [
                    InlineKeyboardButton(text=back_text, callback_data=back_callback),
                    InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN),
                ]
            )
        elif merge_pagination_and_back and pagination_row:
            pagination_row.append(InlineKeyboardButton(text=back_text, callback_data=back_callback))
            rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
            return InlineKeyboardMarkup(inline_keyboard=rows)
        else:
            rows.append([InlineKeyboardButton(text=back_text, callback_data=back_callback)])
            rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
            return InlineKeyboardMarkup(inline_keyboard=rows)
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
    rows.append(
        [
            InlineKeyboardButton(
                text="Переместить в тему",
                callback_data=f"{ENTRY_MOVE_MENU_PREFIX}{entry_id}",
            ),
            InlineKeyboardButton(
                text="Редактировать",
                callback_data=f"{ENTRY_EDIT_MENU_PREFIX}{entry_id}",
            ),
        ]
    )
    rows.append(
        [
            InlineKeyboardButton(
                text="Темы записи",
                callback_data=f"{ENTRY_TOPICS_MENU_PREFIX}{entry_id}",
            )
        ]
    )
    rows.append(
        [InlineKeyboardButton(text="Похожие", callback_data=f"{RELATED_PAGE_PREFIX}{entry_id}:0")]
    )
    if allowed_statuses:
        rows[-1].append(
            InlineKeyboardButton(
                text="Изменить статус",
                callback_data=f"{ENTRY_STATUS_MENU_PREFIX}{entry_id}",
            )
        )

    if include_back_to_list:
        rows.append([InlineKeyboardButton(text="К быстрым спискам", callback_data=MENU_LIST)])
    if back_callback and back_text:
        rows.append(
            [
                InlineKeyboardButton(text=back_text, callback_data=back_callback),
                InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN),
            ]
        )
        return InlineKeyboardMarkup(inline_keyboard=rows)
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_entry_edit_fields_keyboard(
    entry_id: str,
    *,
    entry_back_callback: str | None = None,
    back_callback: str | None = None,
    back_text: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="Заголовок",
                callback_data=f"{ENTRY_EDIT_FIELD_PREFIX}{entry_id}:title",
            ),
            InlineKeyboardButton(
                text="Ссылка",
                callback_data=f"{ENTRY_EDIT_FIELD_PREFIX}{entry_id}:url",
            ),
        ],
        [
            InlineKeyboardButton(
                text="Описание",
                callback_data=f"{ENTRY_EDIT_FIELD_PREFIX}{entry_id}:description",
            ),
            InlineKeyboardButton(
                text="Заметки",
                callback_data=f"{ENTRY_EDIT_FIELD_PREFIX}{entry_id}:notes",
            ),
        ],
        [
            InlineKeyboardButton(
                text="Назад к карточке",
                callback_data=_build_entry_view_callback(entry_id, entry_back_callback),
            )
        ],
    ]
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
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="Переместить",
                callback_data=f"{ENTRY_MOVE_MENU_PREFIX}{entry_id}",
            ),
            InlineKeyboardButton(
                text="Редактировать",
                callback_data=f"{ENTRY_EDIT_MENU_PREFIX}{entry_id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text="Похожие",
                callback_data=f"{RELATED_PAGE_PREFIX}{entry_id}:0",
            ),
            InlineKeyboardButton(
                text="Открыть карточку",
                callback_data=_build_entry_view_callback(entry_id, entry_back_callback),
            ),
        ],
        [
            InlineKeyboardButton(
                text="Темы записи",
                callback_data=f"{ENTRY_TOPICS_MENU_PREFIX}{entry_id}",
            )
        ],
        [InlineKeyboardButton(text="Удалить запись", callback_data=f"{ENTRY_DELETE_PREFIX}{entry_id}")],
    ]
    if back_callback and back_text:
        rows.append(
            [
                InlineKeyboardButton(text=back_text, callback_data=back_callback),
                InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN),
            ]
        )
    else:
        rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _render_entry_button_label(item: object, *, include_status: bool = True) -> str:
    label = item.title
    if include_status:
        label = f"{item.title} [{item.status_name}]"
    return _wrap_button_text(label, max_line_length=28, max_lines=2, hard_limit=64)


def _wrap_button_text(
    text: str,
    *,
    max_line_length: int,
    max_lines: int,
    hard_limit: int,
) -> str:
    compact = " ".join((text or "").split())
    if not compact:
        return ""
    lines = wrap(
        compact,
        width=max_line_length,
        break_long_words=True,
        break_on_hyphens=False,
    )
    clipped = lines[:max_lines]
    wrapped = "\n".join(clipped)

    if len(wrapped) > hard_limit:
        wrapped = wrapped[:hard_limit].rstrip()

    if len(lines) > max_lines or wrapped != compact:
        if len(wrapped) >= hard_limit:
            wrapped = wrapped[: max(0, hard_limit - 3)].rstrip()
        if not wrapped.endswith("..."):
            wrapped = f"{wrapped}..."

    return wrapped


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


def build_entry_move_topic_keyboard(
    *,
    topics: list[TopicDTO],
    mode: str,
    entry_id: str,
    entry_back_callback: str | None,
    page: int = 0,
    has_prev_page: bool = False,
    has_next_page: bool = False,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if mode == "pick_existing":
        rows.extend(
            [
                [InlineKeyboardButton(text="Добавить тему L0", callback_data=ENTRY_MOVE_CREATE_L0)],
                [InlineKeyboardButton(text="Добавить подтему L1", callback_data=ENTRY_MOVE_CREATE_L1)],
            ]
        )
    for topic in topics:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_render_topic_button_label(topic),
                    callback_data=(
                        f"{ENTRY_MOVE_PICK_PREFIX}{topic.id}"
                        if mode in {"pick_existing", "secondary_add"}
                        else f"{ENTRY_MOVE_PARENT_PICK_PREFIX}{topic.id}"
                    ),
                )
            ]
        )

    if has_prev_page or has_next_page:
        pagination_row: list[InlineKeyboardButton] = []
        if has_prev_page:
            pagination_row.append(
                InlineKeyboardButton(
                    text="◀ Назад",
                    callback_data=f"{ENTRY_MOVE_PAGE_PREFIX}{page - 1}",
                )
            )
        if has_next_page:
            pagination_row.append(
                InlineKeyboardButton(
                    text="Далее ▶",
                    callback_data=f"{ENTRY_MOVE_PAGE_PREFIX}{page + 1}",
                )
            )
        if pagination_row:
            rows.append(pagination_row)

    rows.append(
        [
            InlineKeyboardButton(
                text="Назад к карточке",
                callback_data=_build_entry_view_callback(entry_id, entry_back_callback),
            )
        ]
    )
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_entry_topics_manage_keyboard(
    entry_id: str,
    *,
    secondary_topic_options: list[TopicDTO],
    entry_back_callback: str | None = None,
    back_callback: str | None = None,
    back_text: str | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text="Добавить тему",
                callback_data=f"{ENTRY_TOPIC_ADD_MENU_PREFIX}{entry_id}",
            ),
            InlineKeyboardButton(
                text="Сменить основную тему",
                callback_data=f"{ENTRY_MOVE_MENU_PREFIX}{entry_id}",
            ),
        ]
    ]

    for topic in secondary_topic_options[:8]:
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"Убрать: {topic.name}"[:64],
                    callback_data=f"{ENTRY_TOPIC_REMOVE_PICK_PREFIX}{topic.id}",
                )
            ]
        )

    back_row: list[InlineKeyboardButton] = [
        InlineKeyboardButton(
            text="Назад к карточке",
            callback_data=_build_entry_view_callback(entry_id, entry_back_callback),
        )
    ]
    if back_callback and back_text:
        back_row.append(InlineKeyboardButton(text=back_text, callback_data=back_callback))
    rows.append(back_row)
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_topic_entries_actions_rows(topic_id: str) -> list[list[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(text="Переименовать тему", callback_data=f"{TOPIC_RENAME_PREFIX}{topic_id}"),
            InlineKeyboardButton(text="Добавить подтему", callback_data=f"{TOPIC_CREATE_CHILD_PREFIX}{topic_id}"),
        ],
        [InlineKeyboardButton(text="Удалить тему", callback_data=f"{TOPIC_DELETE_PREFIX}{topic_id}")],
    ]


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


def build_topics_tree_keyboard(
    topic_rows: list[tuple[TopicDTO, bool, bool]],
    *,
    page: int,
    has_prev_page: bool = False,
    has_next_page: bool = False,
    page_callback_prefix: str | None = None,
    topic_counts_by_id: dict[object, int] | None = None,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(text="Добавить корневую тему", callback_data=MENU_TOPIC_CREATE),
            InlineKeyboardButton(text="Обновить", callback_data=MENU_TOPICS),
        ],
        [InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)],
    ]
    child_row_buffer: list[InlineKeyboardButton] = []
    topic_counts_by_id = topic_counts_by_id or {}

    def _topic_label(topic: TopicDTO) -> str:
        count = int(topic_counts_by_id.get(topic.id, 0))
        return f"{_render_topic_button_label(topic)} ({count})"

    def _flush_child_row_buffer() -> None:
        nonlocal child_row_buffer
        if child_row_buffer:
            rows.append(child_row_buffer)
            child_row_buffer = []

    for topic, has_children, expanded in topic_rows:
        depth_indent = "  " * min(max(topic.level, 0), 4)
        if has_children:
            _flush_child_row_buffer()
            toggle_icon = "▼" if expanded else "▶"
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"{depth_indent}{toggle_icon} {_topic_label(topic)}",
                        callback_data=f"{TOPIC_TOGGLE_PREFIX}{topic.id}",
                    ),
                ]
            )
            if expanded:
                rows.append(
                    [
                        InlineKeyboardButton(
                            text="Добавить подтему",
                            callback_data=f"{TOPIC_CREATE_CHILD_PREFIX}{topic.id}",
                        ),
                        InlineKeyboardButton(
                            text="К списку тем",
                            callback_data=MENU_TOPICS,
                        ),
                    ]
                )
            continue

        if topic.level <= 0:
            _flush_child_row_buffer()
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"{depth_indent}{_topic_label(topic)}",
                        callback_data=f"{TOPIC_VIEW_PREFIX}{topic.id}",
                    )
                ]
            )
            continue

        child_row_buffer.append(
            InlineKeyboardButton(
                text=f"{depth_indent}{_topic_label(topic)}",
                callback_data=f"{TOPIC_VIEW_PREFIX}{topic.id}",
            )
        )
        if len(child_row_buffer) == 3:
            _flush_child_row_buffer()

    _flush_child_row_buffer()

    if page_callback_prefix and (has_prev_page or has_next_page):
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

    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_topic_detail_keyboard(
    topic_id: str,
    *,
    topic_entries_callback: str | None = None,
    quick_entries: list[EntryDetail] | None = None,
) -> InlineKeyboardMarkup:
    entries_callback = topic_entries_callback or f"{TOPIC_ENTRIES_PAGE_PREFIX}{topic_id}:0"
    rows: list[list[InlineKeyboardButton]] = []
    quick_entry_row: list[InlineKeyboardButton] = []
    if quick_entries:
        for entry in quick_entries[:5]:
            quick_entry_row.append(
                InlineKeyboardButton(
                    text=_render_entry_button_label(entry),
                    callback_data=f"{TOPIC_ENTRY_PREVIEW_PREFIX}{entry.entry_id}",
                )
            )
            if len(quick_entry_row) == 2:
                rows.append(quick_entry_row)
                quick_entry_row = []
        if quick_entry_row:
            rows.append(quick_entry_row)

    rows.extend(
        [
            [InlineKeyboardButton(text="Открыть все записи темы", callback_data=entries_callback)],
            [
                InlineKeyboardButton(text="Переименовать тему", callback_data=f"{TOPIC_RENAME_PREFIX}{topic_id}"),
                InlineKeyboardButton(text="Добавить подтему", callback_data=f"{TOPIC_CREATE_CHILD_PREFIX}{topic_id}"),
                InlineKeyboardButton(text="Удалить тему", callback_data=f"{TOPIC_DELETE_PREFIX}{topic_id}"),
            ],
            [
                InlineKeyboardButton(text="Назад к списку тем", callback_data=MENU_TOPICS),
                InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN),
            ],
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
