from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from kb_bot.bot.ui.callbacks import (
    ADD_TOPIC_PREFIX,
    COLLECTION_VIEW_PREFIX,
    ENTRY_STATUS_PREFIX,
    ENTRY_VIEW_PREFIX,
    LIST_ALL,
    LIST_NEW,
    LIST_TO_READ,
    LIST_VERIFIED,
    MENU_ADD,
    MENU_BACKUPS,
    MENU_CANCEL_FLOW,
    MENU_COLLECTIONS,
    MENU_HELP,
    MENU_IMPORT_EXPORT,
    MENU_LIST,
    MENU_MAIN,
    MENU_SEARCH,
    MENU_STATS,
    MENU_TOPIC_CREATE,
    MENU_TOPICS,
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
    prefix = "  " * topic.level
    label = f"{prefix}{topic.name}"
    return label[:64]


def build_entry_results_keyboard(
    items: list[EntryDetail],
    *,
    include_back_to_list: bool = False,
    back_callback: str | None = None,
    back_text: str | None = None,
) -> InlineKeyboardMarkup:
    rows = []
    for item in items:
        rows.append(
            [
                InlineKeyboardButton(
                    text=_render_entry_button_label(item),
                    callback_data=f"{ENTRY_VIEW_PREFIX}{item.entry_id}",
                )
            ]
        )

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
        for status_name in allowed_statuses:
            rows.append(
                [
                    InlineKeyboardButton(
                        text=f"Статус: {status_name}",
                        callback_data=f"{ENTRY_STATUS_PREFIX}{entry_id}:{status_name}",
                    )
                ]
            )

    if include_back_to_list:
        rows.append([InlineKeyboardButton(text="К быстрым спискам", callback_data=MENU_LIST)])
    if back_callback and back_text:
        rows.append([InlineKeyboardButton(text=back_text, callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _render_entry_button_label(item: EntryDetail) -> str:
    label = f"{item.title} [{item.status_name}]"
    return label[:64]


def build_topics_keyboard(topics: list[TopicDTO]) -> InlineKeyboardMarkup:
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
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def build_topic_detail_keyboard(topic_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Переименовать тему", callback_data=f"{TOPIC_RENAME_PREFIX}{topic_id}")],
            [InlineKeyboardButton(text="К темам", callback_data=MENU_TOPICS)],
            [InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)],
        ]
    )


def build_collections_keyboard(collections: list[SavedViewDTO]) -> InlineKeyboardMarkup:
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
    rows.append([InlineKeyboardButton(text="Обновить список", callback_data=MENU_COLLECTIONS)])
    rows.append([InlineKeyboardButton(text="В главное меню", callback_data=MENU_MAIN)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _render_collection_button_label(collection: SavedViewDTO) -> str:
    return collection.name[:64]
