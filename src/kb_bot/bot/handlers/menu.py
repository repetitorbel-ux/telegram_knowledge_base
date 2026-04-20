import asyncio
import html
import re
import subprocess

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.bot.fsm.states import (
    AddEntryStates,
    EntryEditStates,
    EntryMoveStates,
    GuidedSearchStates,
    GuidedImportStates,
    TopicCreateStates,
    TopicRenameStates,
)
from kb_bot.bot.handlers.start import render_welcome_text
from kb_bot.bot.ui.callbacks import (
    BACKUP_RESTORE_ACK_PREFIX,
    BACKUP_RESTORE_EXEC_PREFIX,
    BACKUP_RESTORE_PICK_PREFIX,
    COLLECTIONS_PAGE_PREFIX,
    COLLECTION_VIEW_PREFIX,
    ENTRY_DELETE_CONFIRM_PREFIX,
    ENTRY_DELETE_PREFIX,
    ENTRY_EDIT_FIELD_PREFIX,
    ENTRY_EDIT_MENU_PREFIX,
    ENTRY_MOVE_CREATE_L0,
    ENTRY_MOVE_CREATE_L1,
    ENTRY_MOVE_MENU_PREFIX,
    ENTRY_MOVE_PAGE_PREFIX,
    ENTRY_MOVE_PARENT_PICK_PREFIX,
    ENTRY_MOVE_PICK_PREFIX,
    ENTRY_STATUS_MENU_PREFIX,
    ENTRY_STATUS_PREFIX,
    ENTRY_VIEW_PREFIX,
    LIST_ALL,
    LIST_NEW,
    LIST_PAGE_PREFIX,
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
    MENU_RELATED,
    MENU_SEARCH,
    MENU_STATS,
    MENU_TOPIC_CREATE,
    MENU_TOPICS,
    SEARCH_PAGE_PREFIX,
    RELATED_PAGE_PREFIX,
    RELATED_SOURCE_PAGE_PREFIX,
    TOPIC_ENTRIES_PAGE_PREFIX,
    TOPIC_CREATE_CHILD_PREFIX,
    TOPIC_DELETE_CONFIRM_PREFIX,
    TOPIC_DELETE_PREFIX,
    TOPIC_ENTRY_PREVIEW_PREFIX,
    TOPIC_QUICK_ENTRY_PREFIX,
    TOPIC_TOGGLE_PREFIX,
    TOPICS_PAGE_PREFIX,
    TOPIC_RENAME_PREFIX,
    TOPIC_VIEW_PREFIX,
)
from kb_bot.bot.ui.keyboards import (
    build_backups_keyboard,
    build_backup_restore_picker_keyboard,
    build_backup_restore_warning_keyboard,
    build_import_export_keyboard,
    build_collections_keyboard,
    build_flow_navigation_keyboard,
    build_entry_detail_keyboard,
    build_entry_move_topic_keyboard,
    build_entry_delete_confirm_keyboard,
    build_post_entry_delete_keyboard,
    build_entry_edit_fields_keyboard,
    build_entry_preview_keyboard,
    build_entry_results_keyboard,
    build_entry_status_picker_keyboard,
    build_home_navigation_keyboard,
    build_list_filters_keyboard,
    build_main_menu_keyboard,
    build_topic_delete_confirm_keyboard,
    build_topic_detail_keyboard,
    build_topic_entries_actions_rows,
    build_topics_tree_keyboard,
)
from kb_bot.core.config import get_settings
from kb_bot.core.list_parsing import ListFilters
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.backups import BackupsRepository
from kb_bot.db.repositories.jobs import JobsRepository
from kb_bot.db.repositories.saved_views import SavedViewsRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import (
    DuplicateEntryError,
    EntryNotFoundError,
    InvalidStatusTransitionError,
    StatusNotFoundError,
    TopicConflictError,
    TopicNotFoundError,
)
from kb_bot.domain.dto import TopicDTO
from kb_bot.domain.status_machine import ALLOWED_STATUS_TRANSITIONS
from kb_bot.services.backup_service import BackupService
from kb_bot.services.collection_service import CollectionService, SavedViewDTO
from kb_bot.services.entry_service import EntryService
from kb_bot.services.export_service import ExportService
from kb_bot.services.query_service import EntryDetail, QueryService
from kb_bot.services.search_service import SearchService
from kb_bot.services.stats_service import StatsService
from kb_bot.services.topic_service import TopicService

PAGE_SIZE = 10

LIST_KIND_ALL = "all"
LIST_KIND_NEW = "new"
LIST_KIND_TO_READ = "to_read"
LIST_KIND_VERIFIED = "verified"
_ACTIVE_RESTORE_CHAT_IDS: set[int] = set()
_RESTORE_HEARTBEAT_INTERVAL_SEC = 60
_RESTORE_UI_DIAGNOSTIC_MAX_LEN = 280


def create_menu_router(session_factory: async_sessionmaker) -> Router:
    router = Router()
    settings = get_settings()

    @router.callback_query(StateFilter("*"), F.data == MENU_MAIN)
    async def menu_main(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _show_screen(callback, render_welcome_text(), build_main_menu_keyboard())

    @router.callback_query(StateFilter("*"), F.data == MENU_CANCEL_FLOW)
    async def menu_cancel_flow(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _show_screen(callback, "Текущий сценарий отменен.", build_main_menu_keyboard())

    @router.message(TopicCreateStates.waiting_name, F.text & ~F.text.startswith("/"))
    async def topic_create_name(message: Message, state: FSMContext) -> None:
        name = (message.text or "").strip()
        if not name:
            await message.answer(
                "Название темы не может быть пустым. Отправьте название еще раз.",
                reply_markup=build_flow_navigation_keyboard(),
            )
            return

        state_data = await state.get_data()
        parent_topic_id = _parse_uuid_string(state_data.get("parent_topic_id"))

        async with session_factory() as session:
            service = TopicService(TopicsRepository(session), session)
            try:
                topic = await service.create_topic(name=name, parent_topic_id=parent_topic_id)
            except (ValueError, TopicConflictError, TopicNotFoundError) as exc:
                await message.answer(str(exc), reply_markup=build_flow_navigation_keyboard())
                return

        await state.clear()
        created_label = "Подтема создана" if parent_topic_id is not None else "Тема создана"
        await message.answer(
            f"{created_label}: {topic.full_path}",
            reply_markup=await _build_topics_keyboard_from_db(session_factory),
        )

    @router.message(TopicRenameStates.waiting_name, F.text & ~F.text.startswith("/"))
    async def topic_rename_name(message: Message, state: FSMContext) -> None:
        name = (message.text or "").strip()
        if not name:
            await message.answer(
                "Новое имя темы не может быть пустым. Отправьте имя еще раз.",
                reply_markup=build_flow_navigation_keyboard(),
            )
            return

        data = await state.get_data()
        topic_id = _parse_uuid_string(data.get("topic_id"))
        if topic_id is None:
            await state.clear()
            await message.answer("Не удалось определить тему для переименования.")
            return

        async with session_factory() as session:
            service = TopicService(TopicsRepository(session), session)
            try:
                topic = await service.rename_topic(topic_id=topic_id, new_name=name)
            except (ValueError, TopicConflictError, TopicNotFoundError) as exc:
                await message.answer(str(exc), reply_markup=build_flow_navigation_keyboard())
                return

        await state.clear()
        await message.answer(
            f"Тема переименована: {topic.name}",
            reply_markup=await _build_topics_keyboard_from_db(session_factory),
        )

    @router.message(EntryMoveStates.waiting_topic_name, F.text & ~F.text.startswith("/"))
    async def entry_move_create_topic_name(message: Message, state: FSMContext) -> None:
        name = (message.text or "").strip()
        if not name:
            await message.answer(
                "Название темы не может быть пустым. Отправьте название еще раз.",
                reply_markup=build_flow_navigation_keyboard(),
            )
            return

        state_data = await state.get_data()
        entry_id = _parse_uuid_string(state_data.get("entry_move_entry_id"))
        if entry_id is None:
            await state.clear()
            await message.answer("Сценарий переноса устарел. Откройте запись и начните перенос заново.")
            return

        create_level = state_data.get("entry_move_create_level")
        parent_topic_id = None
        if create_level == "L1":
            parent_topic_id = _parse_uuid_string(state_data.get("entry_move_parent_topic_id"))
            if parent_topic_id is None:
                await state.clear()
                await message.answer("Не выбрана родительская тема для L1. Начните перенос заново.")
                return

        entry_back_callback, back_callback, back_text = _resolve_entry_action_back_context(state_data)
        entry_back_callback = entry_back_callback or back_callback

        async with session_factory() as session:
            topic_service = TopicService(TopicsRepository(session), session)
            entry_service = EntryService(
                session=session,
                entries_repo=EntriesRepository(session),
                topics_repo=TopicsRepository(session),
                statuses_repo=StatusesRepository(session),
            )
            query_service = QueryService(EntriesRepository(session))
            try:
                created_topic = await topic_service.create_topic(
                    name=name,
                    parent_topic_id=parent_topic_id,
                )
                await entry_service.move_to_topic(entry_id, created_topic.id)
            except (ValueError, TopicConflictError, TopicNotFoundError) as exc:
                await message.answer(str(exc), reply_markup=build_flow_navigation_keyboard())
                return
            except EntryNotFoundError:
                await message.answer("Запись не найдена.", reply_markup=build_home_navigation_keyboard())
                return

            detail = await query_service.get_entry_detail(entry_id)

        await state.set_state(None)
        await _clear_entry_move_state(state)

        if detail is None:
            await message.answer(
                "Тема создана и перенос выполнен, но карточку записи перечитать не удалось.",
                reply_markup=build_home_navigation_keyboard(),
            )
            return

        await message.answer(
            _render_entry_detail_screen(detail) + f"\n\nЗапись перенесена в тему: {created_topic.full_path}",
            reply_markup=build_entry_detail_keyboard(
                str(detail.entry_id),
                _allowed_target_statuses(detail.status_name),
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_ADD)
    async def menu_add(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await state.set_state(AddEntryStates.waiting_content)
        await _show_screen(
            callback,
            "Режим добавления записи.\n"
            "Отправьте URL (`http/https`) или обычный текст заметки.\n\n"
            "Если передумаете, нажмите `Отмена` или используйте `/cancel`.",
            build_flow_navigation_keyboard(),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_SEARCH)
    async def menu_search(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await state.set_state(GuidedSearchStates.waiting_query)
        await _show_screen(
            callback,
            "Режим поиска.\n"
            "Отправьте поисковую строку следующим сообщением.\n\n"
            "Пример: `PostgreSQL backup`",
            build_flow_navigation_keyboard(),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_RELATED)
    async def menu_related(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _show_related_source_page(callback, session_factory, state=state, page=0)

    @router.callback_query(StateFilter("*"), F.data.startswith(RELATED_SOURCE_PAGE_PREFIX))
    async def related_source_page(callback: CallbackQuery, state: FSMContext) -> None:
        page = _parse_page_callback(callback.data, RELATED_SOURCE_PAGE_PREFIX)
        if page is None:
            await callback.answer("Не удалось открыть список записей.", show_alert=True)
            return
        if page < 0:
            await callback.answer("Страница вне диапазона.", show_alert=True)
            return

        await _show_related_source_page(callback, session_factory, state=state, page=page)

    @router.message(GuidedSearchStates.waiting_query, F.text & ~F.text.startswith("/"))
    @router.message(GuidedSearchStates.showing_results, F.text & ~F.text.startswith("/"))
    async def guided_search(message: Message, state: FSMContext) -> None:
        query = (message.text or "").strip()
        if not query:
            await message.answer(
                "Запрос пустой. Отправьте текст для поиска.",
                reply_markup=build_flow_navigation_keyboard(),
            )
            return

        rows, has_next_page = await _load_search_results(
            session_factory,
            query=query,
            page=0,
            page_size=PAGE_SIZE,
        )

        if not rows:
            await message.answer(
                "Ничего не найдено. Отправьте другой запрос или отмените сценарий.",
                reply_markup=build_flow_navigation_keyboard(),
            )
            return

        await state.set_state(GuidedSearchStates.showing_results)
        await state.update_data(search_query=query)
        await message.answer(
            _render_search_results_screen(rows, query, page=0),
            reply_markup=build_entry_results_keyboard(
                rows,
                back_callback=MENU_SEARCH,
                back_text="Назад к поиску",
                page=0,
                has_prev_page=False,
                has_next_page=has_next_page,
                page_callback_prefix=SEARCH_PAGE_PREFIX,
                entry_back_callback=f"{SEARCH_PAGE_PREFIX}0",
            ),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(SEARCH_PAGE_PREFIX))
    async def search_page(callback: CallbackQuery, state: FSMContext) -> None:
        page = _parse_page_callback(callback.data, SEARCH_PAGE_PREFIX)
        if page is None:
            await callback.answer("Не удалось открыть страницу результатов.", show_alert=True)
            return
        if page < 0:
            await callback.answer("Страница вне диапазона.", show_alert=True)
            return

        state_data = await state.get_data()
        query = (state_data.get("search_query") or "").strip()
        if not query:
            await callback.answer("Сессия поиска завершена. Запустите поиск заново.", show_alert=True)
            return

        rows, has_next_page = await _load_search_results(
            session_factory,
            query=query,
            page=page,
            page_size=PAGE_SIZE,
        )

        await state.set_state(GuidedSearchStates.showing_results)
        await state.update_data(search_query=query)
        await _show_screen(
            callback,
            _render_search_results_screen(rows, query, page=page),
            build_entry_results_keyboard(
                rows,
                back_callback=MENU_SEARCH,
                back_text="Назад к поиску",
                page=page,
                has_prev_page=page > 0,
                has_next_page=has_next_page,
                page_callback_prefix=SEARCH_PAGE_PREFIX,
                entry_back_callback=f"{SEARCH_PAGE_PREFIX}{page}",
            ),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_LIST)
    async def menu_list(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _show_screen(
            callback,
            "Быстрые списки.\n"
            "Выберите, какие записи показать.\n\n"
            "Подсказка по статусам:\n"
            "- New: входящий поток\n"
            "- To Read: очередь на разбор\n"
            "- Verified: проверенные материалы",
            build_list_filters_keyboard(),
        )

    @router.callback_query(StateFilter("*"), F.data == LIST_ALL)
    async def list_all(callback: CallbackQuery, state: FSMContext) -> None:
        await _show_list_page(callback, session_factory, state=state, list_kind=LIST_KIND_ALL, page=0)

    @router.callback_query(StateFilter("*"), F.data == LIST_NEW)
    async def list_new(callback: CallbackQuery, state: FSMContext) -> None:
        await _show_list_page(callback, session_factory, state=state, list_kind=LIST_KIND_NEW, page=0)

    @router.callback_query(StateFilter("*"), F.data == LIST_TO_READ)
    async def list_to_read(callback: CallbackQuery, state: FSMContext) -> None:
        await _show_list_page(callback, session_factory, state=state, list_kind=LIST_KIND_TO_READ, page=0)

    @router.callback_query(StateFilter("*"), F.data == LIST_VERIFIED)
    async def list_verified(callback: CallbackQuery, state: FSMContext) -> None:
        await _show_list_page(callback, session_factory, state=state, list_kind=LIST_KIND_VERIFIED, page=0)

    @router.callback_query(StateFilter("*"), F.data.startswith(LIST_PAGE_PREFIX))
    async def list_page(callback: CallbackQuery, state: FSMContext) -> None:
        parsed = _parse_list_page_callback(callback.data)
        if parsed is None:
            await callback.answer("Не удалось открыть страницу списка.", show_alert=True)
            return

        list_kind, page = parsed
        if page < 0:
            await callback.answer("Страница вне диапазона.", show_alert=True)
            return

        await _show_list_page(callback, session_factory, state=state, list_kind=list_kind, page=page)

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_VIEW_PREFIX))
    async def entry_view(callback: CallbackQuery, state: FSMContext) -> None:
        parsed = _parse_entry_view_callback(callback.data)
        if parsed is None:
            await callback.answer("Не удалось открыть запись.", show_alert=True)
            return
        entry_id, entry_back_callback = parsed
        if entry_back_callback is None:
            state_data = await state.get_data()
            entry_back_callback = _resolve_entry_back_callback_from_state(state_data)
        back_callback, back_text = _resolve_entry_back_action(entry_back_callback)
        await state.update_data(entry_back_callback=back_callback, entry_back_text=back_text)

        async with session_factory() as session:
            service = QueryService(EntriesRepository(session))
            detail = await service.get_entry_detail(entry_id)

        if detail is None:
            await callback.answer("Запись не найдена.", show_alert=True)
            return

        await _show_screen(
            callback,
            _render_entry_detail_screen(detail),
            build_entry_detail_keyboard(
                str(detail.entry_id),
                _allowed_target_statuses(detail.status_name),
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_MOVE_MENU_PREFIX))
    async def entry_move_menu(callback: CallbackQuery, state: FSMContext) -> None:
        entry_id = _parse_entry_id_from_callback(callback.data, ENTRY_MOVE_MENU_PREFIX)
        if entry_id is None:
            await callback.answer("Не удалось открыть перенос записи.", show_alert=True)
            return

        state_data = await state.get_data()
        raw_entry_back_callback, back_callback, back_text = _resolve_entry_action_back_context(state_data)
        entry_back_callback = raw_entry_back_callback or back_callback

        await state.update_data(
            entry_back_callback=back_callback,
            entry_back_text=back_text,
            entry_move_entry_id=str(entry_id),
            entry_move_mode="pick_existing",
        )
        await _clear_entry_move_draft_state(state)
        await _show_entry_move_topics_page(
            callback,
            session_factory,
            state=state,
            entry_id=entry_id,
            entry_back_callback=entry_back_callback,
            mode="pick_existing",
            page=0,
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_MOVE_PAGE_PREFIX))
    async def entry_move_topics_page(callback: CallbackQuery, state: FSMContext) -> None:
        page = _parse_page_callback(callback.data, ENTRY_MOVE_PAGE_PREFIX)
        if page is None:
            await callback.answer("Не удалось открыть страницу тем.", show_alert=True)
            return
        if page < 0:
            await callback.answer("Страница вне диапазона.", show_alert=True)
            return

        state_data = await state.get_data()
        entry_id = _parse_uuid_string(state_data.get("entry_move_entry_id"))
        if entry_id is None:
            await callback.answer("Сценарий переноса устарел. Откройте запись заново.", show_alert=True)
            return

        mode = state_data.get("entry_move_mode")
        if mode not in {"pick_existing", "pick_parent"}:
            mode = "pick_existing"
        raw_entry_back_callback, back_callback, _ = _resolve_entry_action_back_context(state_data)
        entry_back_callback = raw_entry_back_callback or back_callback

        await _show_entry_move_topics_page(
            callback,
            session_factory,
            state=state,
            entry_id=entry_id,
            entry_back_callback=entry_back_callback,
            mode=mode,
            page=page,
        )

    @router.callback_query(StateFilter("*"), F.data == ENTRY_MOVE_CREATE_L0)
    async def entry_move_create_l0(callback: CallbackQuery, state: FSMContext) -> None:
        state_data = await state.get_data()
        entry_id = _parse_uuid_string(state_data.get("entry_move_entry_id"))
        if entry_id is None:
            await callback.answer("Сценарий переноса устарел. Откройте запись заново.", show_alert=True)
            return

        await state.update_data(
            entry_move_entry_id=str(entry_id),
            entry_move_create_level="L0",
            entry_move_parent_topic_id=None,
        )
        await state.set_state(EntryMoveStates.waiting_topic_name)
        await _show_screen(
            callback,
            "Создание новой темы L0.\nОтправьте название темы следующим сообщением.",
            build_flow_navigation_keyboard(),
        )

    @router.callback_query(StateFilter("*"), F.data == ENTRY_MOVE_CREATE_L1)
    async def entry_move_create_l1(callback: CallbackQuery, state: FSMContext) -> None:
        state_data = await state.get_data()
        entry_id = _parse_uuid_string(state_data.get("entry_move_entry_id"))
        if entry_id is None:
            await callback.answer("Сценарий переноса устарел. Откройте запись заново.", show_alert=True)
            return

        raw_entry_back_callback, back_callback, _ = _resolve_entry_action_back_context(state_data)
        entry_back_callback = raw_entry_back_callback or back_callback
        await state.update_data(entry_move_mode="pick_parent")
        await _clear_entry_move_draft_state(state)

        await _show_entry_move_topics_page(
            callback,
            session_factory,
            state=state,
            entry_id=entry_id,
            entry_back_callback=entry_back_callback,
            mode="pick_parent",
            page=0,
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_MOVE_PARENT_PICK_PREFIX))
    async def entry_move_pick_parent(callback: CallbackQuery, state: FSMContext) -> None:
        parent_topic_id = _parse_entry_id_from_callback(callback.data, ENTRY_MOVE_PARENT_PICK_PREFIX)
        if parent_topic_id is None:
            await callback.answer("Не удалось выбрать родительскую тему.", show_alert=True)
            return

        async with session_factory() as session:
            topic_service = TopicService(TopicsRepository(session))
            topics = await topic_service.list_tree()

        parent_topic = next((item for item in topics if str(item.id) == str(parent_topic_id)), None)
        if parent_topic is None:
            await callback.answer("Родительская тема не найдена.", show_alert=True)
            return

        await state.update_data(
            entry_move_create_level="L1",
            entry_move_parent_topic_id=str(parent_topic_id),
        )
        await state.set_state(EntryMoveStates.waiting_topic_name)
        await _show_screen(
            callback,
            "Создание подтемы L1.\n"
            f"Родитель: `{parent_topic.full_path}`\n"
            "Отправьте название новой подтемы следующим сообщением.",
            build_flow_navigation_keyboard(),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_MOVE_PICK_PREFIX))
    async def entry_move_pick_existing_topic(callback: CallbackQuery, state: FSMContext) -> None:
        topic_id = _parse_entry_id_from_callback(callback.data, ENTRY_MOVE_PICK_PREFIX)
        if topic_id is None:
            await callback.answer("Не удалось выбрать тему.", show_alert=True)
            return

        state_data = await state.get_data()
        entry_id = _parse_uuid_string(state_data.get("entry_move_entry_id"))
        if entry_id is None:
            await callback.answer("Сценарий переноса устарел. Откройте запись заново.", show_alert=True)
            return

        _, back_callback, back_text = _resolve_entry_action_back_context(state_data)

        async with session_factory() as session:
            entry_service = EntryService(
                session=session,
                entries_repo=EntriesRepository(session),
                topics_repo=TopicsRepository(session),
                statuses_repo=StatusesRepository(session),
            )
            query_service = QueryService(EntriesRepository(session))
            topic_service = TopicService(TopicsRepository(session))
            try:
                await entry_service.move_to_topic(entry_id, topic_id)
            except EntryNotFoundError:
                await callback.answer("Запись не найдена.", show_alert=True)
                return
            except TopicNotFoundError:
                await callback.answer("Тема не найдена.", show_alert=True)
                return
            detail = await query_service.get_entry_detail(entry_id)
            topics = await topic_service.list_tree()

        await _clear_entry_move_state(state)

        redirected = await _return_to_list_after_entry_delete(
            callback,
            session_factory,
            state=state,
            back_callback=back_callback,
        )
        if redirected:
            return

        if detail is None:
            await callback.answer("Не удалось перечитать запись после переноса.", show_alert=True)
            return

        moved_topic = next((item for item in topics if str(item.id) == str(topic_id)), None)
        moved_label = moved_topic.full_path if moved_topic is not None else detail.topic_name
        await _show_screen(
            callback,
            _render_entry_detail_screen(detail) + f"\n\nЗапись перенесена в тему: {moved_label}",
            build_entry_detail_keyboard(
                str(detail.entry_id),
                _allowed_target_statuses(detail.status_name),
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_STATUS_MENU_PREFIX))
    async def entry_status_menu(callback: CallbackQuery, state: FSMContext) -> None:
        entry_id = _parse_entry_id_from_callback(callback.data, ENTRY_STATUS_MENU_PREFIX)
        if entry_id is None:
            await callback.answer("Не удалось открыть выбор статуса.", show_alert=True)
            return

        state_data = await state.get_data()
        entry_back_callback, back_callback, back_text = _resolve_entry_action_back_context(state_data)

        async with session_factory() as session:
            query_service = QueryService(EntriesRepository(session))
            detail = await query_service.get_entry_detail(entry_id)

        if detail is None:
            await callback.answer("Запись не найдена.", show_alert=True)
            return

        await _show_screen(
            callback,
            _render_entry_detail_screen(detail) + "\n\nВыберите новый статус:",
            build_entry_status_picker_keyboard(
                str(detail.entry_id),
                _allowed_target_statuses(detail.status_name),
                entry_back_callback=entry_back_callback,
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_EDIT_MENU_PREFIX))
    async def entry_edit_menu(callback: CallbackQuery, state: FSMContext) -> None:
        entry_id = _parse_entry_id_from_callback(callback.data, ENTRY_EDIT_MENU_PREFIX)
        if entry_id is None:
            await callback.answer("Не удалось открыть редактирование.", show_alert=True)
            return

        state_data = await state.get_data()
        entry_back_callback, back_callback, back_text = _resolve_entry_action_back_context(state_data)

        async with session_factory() as session:
            query_service = QueryService(EntriesRepository(session))
            detail = await query_service.get_entry_detail(entry_id)

        if detail is None:
            await callback.answer("Запись не найдена.", show_alert=True)
            return

        await _clear_entry_edit_state(state)
        await _show_screen(
            callback,
            _render_entry_detail_screen(detail)
            + "\n\nВыберите поле для редактирования.\n"
            "Для очистки значения отправьте `-` следующим сообщением.",
            build_entry_edit_fields_keyboard(
                str(detail.entry_id),
                entry_back_callback=entry_back_callback,
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_EDIT_FIELD_PREFIX))
    async def entry_edit_pick_field(callback: CallbackQuery, state: FSMContext) -> None:
        parsed = _parse_entry_edit_field_callback(callback.data)
        if parsed is None:
            await callback.answer("Не удалось выбрать поле для редактирования.", show_alert=True)
            return
        entry_id, field_name = parsed

        state_data = await state.get_data()
        _, back_callback, back_text = _resolve_entry_action_back_context(state_data)

        await state.update_data(
            entry_back_callback=back_callback,
            entry_back_text=back_text,
            entry_edit_entry_id=str(entry_id),
            entry_edit_field=field_name,
        )
        await state.set_state(EntryEditStates.waiting_value)

        field_labels = {
            "title": "Заголовок",
            "url": "Ссылка",
            "description": "Описание",
            "notes": "Заметки",
        }
        label = field_labels.get(field_name, field_name)
        await _show_screen(
            callback,
            f"Редактирование поля: {label}\n"
            "Отправьте новое значение следующим сообщением.\n"
            "Для очистки поля отправьте `-`.",
            build_flow_navigation_keyboard(),
        )

    @router.message(EntryEditStates.waiting_value)
    async def entry_edit_receive_value(message: Message, state: FSMContext) -> None:
        state_data = await state.get_data()
        entry_id = _parse_uuid_string(state_data.get("entry_edit_entry_id"))
        field_name = state_data.get("entry_edit_field")
        if entry_id is None or not isinstance(field_name, str):
            await state.clear()
            await message.answer(
                "Сценарий редактирования устарел. Откройте карточку записи заново.",
                reply_markup=build_main_menu_keyboard(),
            )
            return

        if not message.text:
            await message.answer(
                "Ожидается текстовое значение. Отправьте текст или `-` для очистки поля.",
                reply_markup=build_flow_navigation_keyboard(),
            )
            return

        back_callback, back_text = _resolve_status_back_action(state_data)

        async with session_factory() as session:
            service = EntryService(
                session=session,
                entries_repo=EntriesRepository(session),
                topics_repo=TopicsRepository(session),
                statuses_repo=StatusesRepository(session),
            )
            query_service = QueryService(EntriesRepository(session))
            try:
                await service.update_field(entry_id, field_name, message.text)
            except EntryNotFoundError:
                await state.clear()
                await message.answer("Запись не найдена.")
                return
            except DuplicateEntryError:
                await message.answer(
                    "Найден дубликат записи. Изменение отклонено.\n"
                    "Попробуйте другое значение.",
                    reply_markup=build_flow_navigation_keyboard(),
                )
                return
            except ValueError:
                await message.answer(
                    "Некорректное значение для выбранного поля.\n"
                    "Попробуйте снова или отправьте `-` для очистки.",
                    reply_markup=build_flow_navigation_keyboard(),
                )
                return

            detail = await query_service.get_entry_detail(entry_id)

        await _clear_entry_edit_state(state)
        await state.update_data(entry_back_callback=back_callback, entry_back_text=back_text)
        if detail is None:
            await message.answer("Запись обновлена, но карточку не удалось перечитать.")
            return

        await _safe_delete_message(message)
        await message.answer(
            _render_entry_detail_screen(detail) + "\n\nЗапись обновлена.",
            reply_markup=build_entry_detail_keyboard(
                str(detail.entry_id),
                _allowed_target_statuses(detail.status_name),
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_DELETE_PREFIX))
    async def entry_delete_start(callback: CallbackQuery, state: FSMContext) -> None:
        entry_id = _parse_entry_id_from_callback(callback.data, ENTRY_DELETE_PREFIX)
        if entry_id is None:
            await callback.answer("Не удалось выбрать запись для удаления.", show_alert=True)
            return

        state_data = await state.get_data()
        entry_back_callback, back_callback, back_text = _resolve_entry_action_back_context(state_data)
        await state.update_data(entry_back_callback=back_callback, entry_back_text=back_text)

        async with session_factory() as session:
            query_service = QueryService(EntriesRepository(session))
            detail = await query_service.get_entry_detail(entry_id)

        if detail is None:
            await callback.answer("Запись не найдена.", show_alert=True)
            return

        await _show_screen(
            callback,
            "Подтвердите удаление записи.\n"
            f"ID: `{detail.entry_id}`\n"
            f"Заголовок: {detail.title}\n\n"
            "Действие необратимо.",
            build_entry_delete_confirm_keyboard(
                str(detail.entry_id),
                entry_back_callback=entry_back_callback,
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_DELETE_CONFIRM_PREFIX))
    async def entry_delete_confirm(callback: CallbackQuery, state: FSMContext) -> None:
        entry_id = _parse_entry_id_from_callback(callback.data, ENTRY_DELETE_CONFIRM_PREFIX)
        if entry_id is None:
            await callback.answer("Не удалось прочитать подтверждение удаления.", show_alert=True)
            return

        state_data = await state.get_data()
        _, back_callback, back_text = _resolve_entry_action_back_context(state_data)

        async with session_factory() as session:
            query_service = QueryService(EntriesRepository(session))
            detail = await query_service.get_entry_detail(entry_id)
            if detail is None:
                await callback.answer("Запись не найдена.", show_alert=True)
                return

            service = EntryService(
                session=session,
                entries_repo=EntriesRepository(session),
                topics_repo=TopicsRepository(session),
                statuses_repo=StatusesRepository(session),
            )
            try:
                await service.delete(entry_id)
            except EntryNotFoundError:
                await callback.answer("Запись уже удалена.", show_alert=True)
                return

        redirected = await _return_to_list_after_entry_delete(
            callback,
            session_factory,
            state=state,
            back_callback=back_callback,
        )
        if redirected:
            return

        await _show_screen(
            callback,
            "Запись удалена.\n"
            f"ID: `{entry_id}`\n"
            f"Заголовок: {detail.title}",
            build_post_entry_delete_keyboard(
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_STATUS_PREFIX))
    async def entry_status_update(callback: CallbackQuery, state: FSMContext) -> None:
        parsed = _parse_status_update_callback(callback.data)
        if parsed is None:
            await callback.answer("Не удалось прочитать действие.", show_alert=True)
            return
        entry_id, status_name = parsed
        state_data = await state.get_data()
        back_callback, back_text = _resolve_status_back_action(state_data)

        async with session_factory() as session:
            service = EntryService(
                session=session,
                entries_repo=EntriesRepository(session),
                topics_repo=TopicsRepository(session),
                statuses_repo=StatusesRepository(session),
            )
            try:
                updated = await service.set_status(entry_id, status_name)
            except EntryNotFoundError:
                await callback.answer("Запись не найдена.", show_alert=True)
                return
            except StatusNotFoundError:
                await callback.answer("Статус не найден.", show_alert=True)
                return
            except InvalidStatusTransitionError as exc:
                await callback.answer(str(exc), show_alert=True)
                return

            query_service = QueryService(EntriesRepository(session))
            detail = await query_service.get_entry_detail(updated.id)

        if detail is None:
            await callback.answer("Статус обновлен, но запись не удалось перечитать.", show_alert=True)
            return

        await _show_screen(
            callback,
            _render_entry_detail_screen(detail) + "\n\nСтатус успешно обновлен.",
            build_entry_detail_keyboard(
                str(detail.entry_id),
                _allowed_target_statuses(detail.status_name),
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_TOPICS)
    async def menu_topics(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await state.update_data(topics_expanded_paths=[], topics_page=0)
        await _show_topics_page(callback, session_factory, state=state, page=0)

    @router.callback_query(StateFilter("*"), F.data.startswith(TOPICS_PAGE_PREFIX))
    async def topics_page(callback: CallbackQuery, state: FSMContext) -> None:
        page = _parse_page_callback(callback.data, TOPICS_PAGE_PREFIX)
        if page is None:
            await callback.answer("Не удалось открыть страницу тем.", show_alert=True)
            return
        if page < 0:
            await callback.answer("Страница вне диапазона.", show_alert=True)
            return
        await state.update_data(topics_page=page)
        await _show_topics_page(callback, session_factory, state=state, page=page)

    @router.callback_query(StateFilter("*"), F.data.startswith(TOPIC_TOGGLE_PREFIX))
    async def topic_toggle(callback: CallbackQuery, state: FSMContext) -> None:
        topic_id = _parse_entry_id_from_callback(callback.data, TOPIC_TOGGLE_PREFIX)
        if topic_id is None:
            await callback.answer("Не удалось переключить ветку.", show_alert=True)
            return

        async with session_factory() as session:
            topic_service = TopicService(TopicsRepository(session))
            topics = await topic_service.list_tree()

        topic = next((item for item in topics if str(item.id) == str(topic_id)), None)
        if topic is None:
            await callback.answer("Тема не найдена.", show_alert=True)
            return

        state_data = await state.get_data()
        expanded_paths = set(_coerce_str_list(state_data.get("topics_expanded_paths")))
        if topic.full_path in expanded_paths:
            expanded_paths.discard(topic.full_path)
        else:
            expanded_paths.add(topic.full_path)

        page_raw = state_data.get("topics_page")
        page = page_raw if isinstance(page_raw, int) and page_raw >= 0 else 0
        await state.update_data(topics_expanded_paths=sorted(expanded_paths), topics_page=page)
        await _show_topics_page(callback, session_factory, page=page, state=state)

    @router.callback_query(StateFilter("*"), F.data == MENU_TOPIC_CREATE)
    async def menu_topic_create(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await state.set_state(TopicCreateStates.waiting_name)
        await _show_screen(
            callback,
            "Создание корневой темы.\nОтправьте название новой темы следующим сообщением.",
            build_flow_navigation_keyboard(),
        )

    @router.callback_query(F.data.startswith(TOPIC_CREATE_CHILD_PREFIX))
    async def topic_create_child_start(callback: CallbackQuery, state: FSMContext) -> None:
        parent_topic_id = _parse_entry_id_from_callback(callback.data, TOPIC_CREATE_CHILD_PREFIX)
        if parent_topic_id is None:
            await callback.answer("Не удалось выбрать родительскую тему.", show_alert=True)
            return

        async with session_factory() as session:
            service = TopicService(TopicsRepository(session))
            topics = await service.list_tree()

        parent_topic = next((item for item in topics if str(item.id) == str(parent_topic_id)), None)
        if parent_topic is None:
            await callback.answer("Родительская тема не найдена.", show_alert=True)
            return

        await state.clear()
        await state.update_data(parent_topic_id=str(parent_topic_id))
        await state.set_state(TopicCreateStates.waiting_name)
        await _show_screen(
            callback,
            "Создание подтемы.\n"
            f"Родитель: `{parent_topic.full_path}`\n"
            "Отправьте название подтемы следующим сообщением.",
            build_flow_navigation_keyboard(),
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(TOPIC_VIEW_PREFIX))
    async def topic_view(callback: CallbackQuery, state: FSMContext) -> None:
        topic_id = _parse_entry_id_from_callback(callback.data, TOPIC_VIEW_PREFIX)
        if topic_id is None:
            await callback.answer("Не удалось открыть тему.", show_alert=True)
            return

        async with session_factory() as session:
            topic_service = TopicService(TopicsRepository(session))
            topics = await topic_service.list_tree()

        topic = next((item for item in topics if str(item.id) == str(topic_id)), None)
        if topic is None:
            await callback.answer("Тема не найдена.", show_alert=True)
            return
        await state.update_data(topic_view_id=str(topic_id))
        await _show_topic_entries_page(
            callback,
            session_factory,
            state=state,
            topic=topic,
            topic_id=topic_id,
            page=0,
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(TOPIC_ENTRIES_PAGE_PREFIX))
    async def topic_entries_page(callback: CallbackQuery, state: FSMContext) -> None:
        parsed = _parse_topic_entries_page_callback(callback.data)
        if parsed is None:
            await callback.answer("Не удалось открыть записи темы.", show_alert=True)
            return

        topic_id, page = parsed
        if page < 0:
            await callback.answer("Страница вне диапазона.", show_alert=True)
            return

        async with session_factory() as session:
            topic_service = TopicService(TopicsRepository(session))
            topics = await topic_service.list_tree()

        topic = next((item for item in topics if str(item.id) == str(topic_id)), None)
        if topic is None:
            await callback.answer("Тема не найдена.", show_alert=True)
            return
        await state.update_data(topic_view_id=str(topic_id))

        await _show_topic_entries_page(
            callback,
            session_factory,
            state=state,
            topic=topic,
            topic_id=topic_id,
            page=page,
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(TOPIC_ENTRY_PREVIEW_PREFIX))
    async def topic_entry_preview(callback: CallbackQuery, state: FSMContext) -> None:
        entry_id = _parse_entry_id_from_callback(callback.data, TOPIC_ENTRY_PREVIEW_PREFIX)
        if entry_id is None:
            await callback.answer("Не удалось открыть предпросмотр.", show_alert=True)
            return

        state_data = await state.get_data()
        entry_back_callback = _resolve_entry_back_callback_from_state(state_data)
        back_callback, back_text = _resolve_entry_back_action(entry_back_callback)
        if back_callback.startswith(TOPIC_ENTRIES_PAGE_PREFIX):
            back_text = "Назад к записям"

        async with session_factory() as session:
            query_service = QueryService(EntriesRepository(session))
            detail = await query_service.get_entry_detail(entry_id)

        if detail is None:
            await callback.answer("Запись не найдена.", show_alert=True)
            return

        await state.update_data(entry_back_callback=back_callback, entry_back_text=back_text)

        await _show_screen(
            callback,
            _render_entry_preview_screen_html(detail),
            build_entry_preview_keyboard(
                str(detail.entry_id),
                entry_back_callback=entry_back_callback,
                back_callback=back_callback,
                back_text=back_text,
            ),
            parse_mode="HTML",
        )

    @router.callback_query(StateFilter("*"), F.data.startswith(TOPIC_QUICK_ENTRY_PREFIX))
    async def topic_quick_entry_view(callback: CallbackQuery, state: FSMContext) -> None:
        entry_id = _parse_entry_id_from_callback(callback.data, TOPIC_QUICK_ENTRY_PREFIX)
        if entry_id is None:
            await callback.answer("Не удалось открыть запись.", show_alert=True)
            return

        state_data = await state.get_data()
        topic_id = _parse_uuid_string(state_data.get("topic_view_id"))
        back_callback = MENU_TOPICS
        back_text = "Назад к списку тем"
        if topic_id is not None:
            back_callback = f"{TOPIC_VIEW_PREFIX}{topic_id}"
            back_text = "Назад к теме"

        async with session_factory() as session:
            query_service = QueryService(EntriesRepository(session))
            detail = await query_service.get_entry_detail(entry_id)

        if detail is None:
            await callback.answer("Запись не найдена.", show_alert=True)
            return

        await state.update_data(entry_back_callback=back_callback, entry_back_text=back_text)

        await _show_screen(
            callback,
            _render_entry_detail_screen(detail),
            build_entry_detail_keyboard(
                str(detail.entry_id),
                _allowed_target_statuses(detail.status_name),
                back_callback=back_callback,
                back_text=back_text,
            ),
        )

    @router.callback_query(F.data.startswith(TOPIC_RENAME_PREFIX))
    async def topic_rename_start(callback: CallbackQuery, state: FSMContext) -> None:
        topic_id = _parse_entry_id_from_callback(callback.data, TOPIC_RENAME_PREFIX)
        if topic_id is None:
            await callback.answer("Не удалось выбрать тему.", show_alert=True)
            return

        await state.clear()
        await state.update_data(topic_id=str(topic_id))
        await state.set_state(TopicRenameStates.waiting_name)
        await _show_screen(
            callback,
            "Переименование темы.\nОтправьте новое имя темы следующим сообщением.",
            build_flow_navigation_keyboard(),
        )

    @router.callback_query(F.data.startswith(TOPIC_DELETE_PREFIX))
    async def topic_delete_start(callback: CallbackQuery) -> None:
        topic_id = _parse_entry_id_from_callback(callback.data, TOPIC_DELETE_PREFIX)
        if topic_id is None:
            await callback.answer("Не удалось выбрать тему.", show_alert=True)
            return

        async with session_factory() as session:
            service = TopicService(TopicsRepository(session), session)
            try:
                topic, descendants_count = await service.get_topic_with_descendants_count(topic_id)
            except TopicNotFoundError:
                await callback.answer("Тема не найдена.", show_alert=True)
                return

        await _show_screen(
            callback,
            "Подтвердите удаление темы.\n"
            f"Будет скрыта ветка: `{topic.full_path}`\n"
            f"Подтем будет затронуто: {descendants_count}\n\n"
            "Действие обратимо только через прямое изменение в БД.",
            build_topic_delete_confirm_keyboard(str(topic_id)),
        )

    @router.callback_query(F.data.startswith(TOPIC_DELETE_CONFIRM_PREFIX))
    async def topic_delete_confirm(callback: CallbackQuery) -> None:
        topic_id = _parse_entry_id_from_callback(callback.data, TOPIC_DELETE_CONFIRM_PREFIX)
        if topic_id is None:
            await callback.answer("Не удалось прочитать подтверждение.", show_alert=True)
            return

        async with session_factory() as session:
            service = TopicService(TopicsRepository(session), session)
            try:
                deleted_count = await service.archive_topic_branch(topic_id)
            except TopicNotFoundError:
                await callback.answer("Тема уже недоступна.", show_alert=True)
                return

        await _show_screen(
            callback,
            f"Тема удалена (архивирована).\nСкрыто тем: {deleted_count}.",
            await _build_topics_keyboard_from_db(session_factory),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_STATS)
    async def menu_stats(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        async with session_factory() as session:
            service = StatsService(session)
            stats = await service.get_stats()

        await _show_screen(
            callback,
            _render_stats_screen(stats),
            build_home_navigation_keyboard(),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_COLLECTIONS)
    async def menu_collections(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _show_collections_page(callback, session_factory, page=0)

    @router.callback_query(StateFilter("*"), F.data.startswith(COLLECTIONS_PAGE_PREFIX))
    async def collections_page(callback: CallbackQuery) -> None:
        page = _parse_page_callback(callback.data, COLLECTIONS_PAGE_PREFIX)
        if page is None:
            await callback.answer("Не удалось открыть страницу коллекций.", show_alert=True)
            return
        if page < 0:
            await callback.answer("Страница вне диапазона.", show_alert=True)
            return
        await _show_collections_page(callback, session_factory, page=page)

    @router.callback_query(F.data.startswith(COLLECTION_VIEW_PREFIX))
    async def collection_view(callback: CallbackQuery) -> None:
        collection_id = _parse_entry_id_from_callback(callback.data, COLLECTION_VIEW_PREFIX)
        if collection_id is None:
            await callback.answer("Не удалось открыть коллекцию.", show_alert=True)
            return

        async with session_factory() as session:
            collection_service = CollectionService(SavedViewsRepository(session), session)
            view = await collection_service.get_saved_view(collection_id)
            if view is None:
                await callback.answer("Коллекция не найдена.", show_alert=True)
                return

            snapshot = view.filter_snapshot
            parsed_topic_id = _parse_uuid_string(snapshot.get("topic_id"))

            query_service = QueryService(EntriesRepository(session))
            entries = await query_service.list_entries(
                status_name=snapshot.get("status_name"),
                topic_id=parsed_topic_id,
                limit=int(snapshot.get("limit", 20)),
            )

        markup = (
            build_entry_results_keyboard(
                entries,
                back_callback=MENU_COLLECTIONS,
                back_text="К коллекциям",
                entry_back_callback=MENU_COLLECTIONS,
            )
            if entries
            else await _build_collections_keyboard_from_db(session_factory, page=0)
        )
        await _show_screen(
            callback,
            _render_collection_result_screen(view, entries),
            markup,
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_IMPORT_EXPORT)
    async def menu_import_export(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _show_screen(
            callback,
            (
                "Импорт и экспорт.\n\n"
                "Можно запустить импорт кнопкой ниже и затем просто отправить CSV/JSON файл.\n"
                "Также доступны быстрые экспорты без ручного ввода команды."
            ),
            build_import_export_keyboard(),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_IMPORT_START)
    async def menu_import_start(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await state.set_state(GuidedImportStates.waiting_document)
        await _show_screen(
            callback,
            "Режим импорта.\n"
            "Отправьте CSV или JSON файл следующим сообщением.\n\n"
            "Подпись /import в этом режиме не обязательна.",
            build_flow_navigation_keyboard(),
        )

    @router.callback_query(F.data == MENU_EXPORT_CSV)
    async def menu_export_csv(callback: CallbackQuery) -> None:
        await callback.answer()
        async with session_factory() as session:
            service = ExportService(
                jobs_repo=JobsRepository(session),
                entries_repo=EntriesRepository(session),
                session=session,
            )
            result = await service.export_entries(
                export_format="csv",
                filters=ListFilters(status_name=None, topic_id=None, limit=50),
            )
        if callback.message is not None:
            from aiogram.types import BufferedInputFile

            file = BufferedInputFile(result.content, filename=result.filename)
            await callback.message.answer_document(
                file,
                caption=f"Экспорт CSV готов. Job `{result.job_id}` records={result.total_records}",
                reply_markup=build_import_export_keyboard(),
            )

    @router.callback_query(F.data == MENU_EXPORT_JSON)
    async def menu_export_json(callback: CallbackQuery) -> None:
        await callback.answer()
        async with session_factory() as session:
            service = ExportService(
                jobs_repo=JobsRepository(session),
                entries_repo=EntriesRepository(session),
                session=session,
            )
            result = await service.export_entries(
                export_format="json",
                filters=ListFilters(status_name=None, topic_id=None, limit=50),
            )
        if callback.message is not None:
            from aiogram.types import BufferedInputFile

            file = BufferedInputFile(result.content, filename=result.filename)
            await callback.message.answer_document(
                file,
                caption=f"Экспорт JSON готов. Job `{result.job_id}` records={result.total_records}",
                reply_markup=build_import_export_keyboard(),
            )

    @router.callback_query(StateFilter("*"), F.data == MENU_BACKUPS)
    async def menu_backups(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _show_screen(
            callback,
            (
                "Бэкапы.\n\n"
                "Через кнопки ниже можно создать новый backup или посмотреть последние записи.\n"
                "Restore пока оставляем в командном и безопасном режиме."
            ),
            build_backups_keyboard(),
        )

    @router.callback_query(F.data == MENU_BACKUP_CREATE)
    async def menu_backup_create(callback: CallbackQuery) -> None:
        await callback.answer()
        async with session_factory() as session:
            service = BackupService(BackupsRepository(session), session)
            result = await service.create_backup(
                database_url=settings.database_url,
                backup_dir=settings.backup_dir,
                pg_dump_bin=settings.pg_dump_bin,
            )
        if callback.message is not None:
            await callback.message.answer(
                f"Backup created:\nID: `{result.backup_id}`\nFile: {result.filename}\nSHA256: {result.checksum}",
                reply_markup=build_backups_keyboard(),
            )

    @router.callback_query(F.data == MENU_BACKUP_LIST)
    async def menu_backup_list(callback: CallbackQuery) -> None:
        await callback.answer()
        async with session_factory() as session:
            service = BackupService(BackupsRepository(session), session)
            rows = await service.list_backups(settings.backup_dir)
        if callback.message is not None:
            await callback.message.answer(
                _render_backups_list_screen(rows),
                reply_markup=build_backups_keyboard(),
            )

    @router.callback_query(F.data == MENU_BACKUP_RESTORE)
    async def menu_backup_restore(callback: CallbackQuery) -> None:
        await callback.answer()
        async with session_factory() as session:
            service = BackupService(BackupsRepository(session), session)
            rows = await service.list_backups(settings.backup_dir)
        if callback.message is None:
            return
        if not rows:
            await callback.message.answer(
                "Restore недоступен: список backup пуст.",
                reply_markup=build_backups_keyboard(),
            )
            return
        await callback.message.answer(
            "Выберите backup для restore.\n\n"
            "Внимание: restore перезаписывает данные целевой БД.\n"
            "Командный безопасный путь `/restore_token` + `/restore` остается доступным.",
            reply_markup=build_backup_restore_picker_keyboard(rows),
        )

    @router.callback_query(F.data.startswith(BACKUP_RESTORE_PICK_PREFIX))
    async def menu_backup_restore_pick(callback: CallbackQuery) -> None:
        backup_id = _parse_entry_id_from_callback(callback.data, BACKUP_RESTORE_PICK_PREFIX)
        if backup_id is None:
            await callback.answer("Не удалось определить backup.", show_alert=True)
            return
        await _show_screen(
            callback,
            "Шаг 1 из 2: подтверждение риска.\n\n"
            "Restore выполнит очистку и восстановление объектов в целевой БД.\n"
            "Продолжайте только если понимаете последствия.",
            build_backup_restore_warning_keyboard(str(backup_id), final=False),
        )

    @router.callback_query(F.data.startswith(BACKUP_RESTORE_ACK_PREFIX))
    async def menu_backup_restore_ack(callback: CallbackQuery) -> None:
        backup_id = _parse_entry_id_from_callback(callback.data, BACKUP_RESTORE_ACK_PREFIX)
        if backup_id is None:
            await callback.answer("Не удалось определить backup.", show_alert=True)
            return
        await _show_screen(
            callback,
            "Шаг 2 из 2: финальное подтверждение.\n\n"
            "После нажатия restore будет запущен немедленно.",
            build_backup_restore_warning_keyboard(str(backup_id), final=True),
        )

    @router.callback_query(F.data.startswith(BACKUP_RESTORE_EXEC_PREFIX))
    async def menu_backup_restore_exec(callback: CallbackQuery) -> None:
        backup_id = _parse_entry_id_from_callback(callback.data, BACKUP_RESTORE_EXEC_PREFIX)
        if backup_id is None:
            await callback.answer("Не удалось определить backup.", show_alert=True)
            return

        await callback.answer("Запускаю restore...")
        if callback.message is None:
            return

        chat_id = callback.message.chat.id
        if chat_id in _ACTIVE_RESTORE_CHAT_IDS:
            await callback.message.answer(
                "Restore уже выполняется для этого чата. Дождитесь финального результата.",
                reply_markup=build_backups_keyboard(),
            )
            return

        _ACTIVE_RESTORE_CHAT_IDS.add(chat_id)
        heartbeat_stop = asyncio.Event()
        heartbeat_task: asyncio.Task[None] | None = None
        try:
            await callback.message.answer(
                f"Restore запущен. Это может занять время (таймаут: {settings.restore_timeout_sec} сек).\n"
                f"Чекпоинт прогресса отправляется каждые {_RESTORE_HEARTBEAT_INTERVAL_SEC} сек.",
                reply_markup=build_backups_keyboard(),
            )
            heartbeat_task = asyncio.create_task(
                _send_restore_heartbeat(
                    callback.message,
                    stop_event=heartbeat_stop,
                    timeout_sec=settings.restore_timeout_sec,
                    interval_sec=_RESTORE_HEARTBEAT_INTERVAL_SEC,
                )
            )
            async with session_factory() as session:
                service = BackupService(BackupsRepository(session), session)
                token = await service.issue_restore_token(str(backup_id))
                await service.restore_backup(
                    backup_id=str(backup_id),
                    token=token,
                    database_url=settings.database_url,
                    pg_restore_bin=settings.pg_restore_bin,
                    restore_timeout_sec=settings.restore_timeout_sec,
                )
        except Exception as exc:
            await callback.message.answer(
                _format_restore_failure_message(exc),
                reply_markup=build_backups_keyboard(),
            )
            return
        finally:
            heartbeat_stop.set()
            if heartbeat_task is not None:
                await heartbeat_task
            _ACTIVE_RESTORE_CHAT_IDS.discard(chat_id)

        await callback.message.answer(
            "Restore completed.\n\n"
            "Рекомендуется проверить `/stats` и быстрый список записей.",
            reply_markup=build_backups_keyboard(),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_HELP)
    async def menu_help(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _show_screen(
            callback,
            "Используйте меню и кнопки как основной режим работы.\n"
            "Сценарий `Похожие` запускается из просмотра записи или из карточки записи.\n\n"
            "Команды остаются как дополнительный (операторский) режим:\n"
            "/start\n"
            "/add\n"
            "/search <query>\n"
            "/list [status=New] [topic=<uuid>] [limit=20]\n"
            "/topics\n"
            "/topic_add <name>\n"
            "/topic_add \"<parent>\" -> <name>\n"
            "/topic_move <topic_uuid|path|name> <target_parent_uuid|path|root>\n"
            "/topic_rename <topic_uuid> <new_name>\n"
            "/topic_delete <topic_uuid|full_path|name>\n"
            "/entry_move <entry_uuid> <topic_uuid>\n"
            "/entry_edit <entry_uuid> <field> <value>\n"
            "/stats\n"
            "/backup\n"
            "/backups\n\n"
            "В пошаговом сценарии используйте кнопку `Отмена`.",
            build_home_navigation_keyboard(),
        )

    return router


async def _send_restore_heartbeat(
    message: Message,
    *,
    stop_event: asyncio.Event,
    timeout_sec: int,
    interval_sec: int,
) -> None:
    elapsed_sec = 0
    while not stop_event.is_set():
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_sec)
            return
        except TimeoutError:
            elapsed_sec += interval_sec

        try:
            await message.answer(_format_restore_progress_checkpoint(elapsed_sec, timeout_sec))
        except TelegramBadRequest:
            return


def _format_restore_progress_checkpoint(elapsed_sec: int, timeout_sec: int) -> str:
    timeout_safe = max(timeout_sec, 1)
    elapsed_safe = max(elapsed_sec, 0)
    percent = min(99, int((elapsed_safe / timeout_safe) * 100))
    return (
        "Restore в процессе.\n"
        f"Прошло: {_format_duration_seconds(elapsed_safe)}.\n"
        f"Лимит: {_format_duration_seconds(timeout_safe)} ({percent}% от таймаута).\n"
        "Ожидайте финальное сообщение."
    )


def _format_restore_failure_message(exc: Exception) -> str:
    reason = _format_restore_failure_reason(exc)
    diagnostics = _extract_restore_diagnostics(exc)
    if diagnostics:
        return f"Restore failed.\nПричина: {reason}\nДиагностика: {diagnostics}"
    return f"Restore failed.\nПричина: {reason}"


def _format_restore_failure_reason(exc: Exception) -> str:
    if isinstance(exc, subprocess.TimeoutExpired):
        timeout = int(exc.timeout) if isinstance(exc.timeout, (int, float)) else exc.timeout
        return f"timeout after {timeout} sec"
    if isinstance(exc, subprocess.CalledProcessError):
        return f"pg_restore exited with code {exc.returncode}"
    text = _compact_restore_text(str(exc), max_len=160)
    return text or exc.__class__.__name__


def _extract_restore_diagnostics(exc: Exception) -> str | None:
    parts: list[str] = []
    stderr_text = _compact_restore_text(getattr(exc, "stderr", None), max_len=180)
    stdout_text = _compact_restore_text(getattr(exc, "stdout", None), max_len=120)

    if stderr_text:
        parts.append(f"stderr={stderr_text}")
    elif stdout_text:
        parts.append(f"stdout={stdout_text}")

    cmd = getattr(exc, "cmd", None)
    if cmd:
        cmd_text = _compact_restore_text(_stringify_command(cmd), max_len=120)
        if cmd_text:
            parts.append(f"cmd={cmd_text}")

    if not parts:
        return None
    return _compact_restore_text(" | ".join(parts), max_len=_RESTORE_UI_DIAGNOSTIC_MAX_LEN)


def _compact_restore_text(value: str | bytes | None, *, max_len: int) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    normalized = " ".join(value.strip().split())
    if not normalized:
        return None
    if len(normalized) <= max_len:
        return normalized
    return normalized[: max_len - 3] + "..."


def _stringify_command(cmd: object) -> str:
    if isinstance(cmd, (list, tuple)):
        return " ".join(str(part) for part in cmd)
    return str(cmd)


def _format_duration_seconds(value: int) -> str:
    minutes, seconds = divmod(max(value, 0), 60)
    if minutes:
        return f"{minutes} мин {seconds} сек"
    return f"{seconds} сек"


async def _load_entries(
    session_factory: async_sessionmaker,
    status_name: str | None,
    *,
    page: int,
    page_size: int = PAGE_SIZE,
) -> tuple[list[EntryDetail], bool]:
    if page < 0:
        return [], False

    offset = page * page_size
    async with session_factory() as session:
        service = QueryService(EntriesRepository(session))
        rows = await service.list_entries(
            status_name=status_name,
            limit=page_size + 1,
            offset=offset,
        )

    has_next_page = len(rows) > page_size
    return rows[:page_size], has_next_page


async def _load_search_results(
    session_factory: async_sessionmaker,
    *,
    query: str,
    page: int,
    page_size: int = PAGE_SIZE,
):
    if page < 0:
        return [], False

    offset = page * page_size
    async with session_factory() as session:
        service = SearchService(EntriesRepository(session))
        rows = await service.search(query=query, limit=page_size + 1, offset=offset)

    has_next_page = len(rows) > page_size
    return rows[:page_size], has_next_page


async def _load_topic_entries(
    session_factory: async_sessionmaker,
    *,
    topic_id,
    page: int,
    page_size: int = PAGE_SIZE,
) -> tuple[list[EntryDetail], bool]:
    if page < 0:
        return [], False

    offset = page * page_size
    async with session_factory() as session:
        service = QueryService(EntriesRepository(session))
        rows = await service.list_entries(topic_id=topic_id, limit=page_size + 1, offset=offset)

    has_next_page = len(rows) > page_size
    return rows[:page_size], has_next_page


def _paginate_rows(rows: list, *, page: int, page_size: int) -> tuple[list, bool]:
    if page < 0:
        return [], False
    offset = page * page_size
    chunk = rows[offset : offset + page_size + 1]
    has_next_page = len(chunk) > page_size
    return chunk[:page_size], has_next_page


async def _load_topics_page(
    session_factory: async_sessionmaker,
    *,
    page: int,
    page_size: int = PAGE_SIZE,
) -> tuple[list[TopicDTO], bool]:
    async with session_factory() as session:
        service = TopicService(TopicsRepository(session))
        rows = await service.list_tree()
    return _paginate_rows(rows, page=page, page_size=page_size)


async def _load_topics_tree_page(
    session_factory: async_sessionmaker,
    *,
    page: int,
    expanded_paths: set[str],
    page_size: int = PAGE_SIZE,
) -> tuple[list[tuple[TopicDTO, bool, bool]], bool]:
    async with session_factory() as session:
        service = TopicService(TopicsRepository(session))
        topics = await service.list_tree()

    roots = [item for item in topics if item.level == 0]
    roots_page, has_next_page = _paginate_rows(roots, page=page, page_size=page_size)

    parent_children: dict[str, list[TopicDTO]] = {}
    for topic in topics:
        parent_path = _topic_parent_path(topic.full_path)
        if parent_path is None:
            continue
        parent_children.setdefault(parent_path, []).append(topic)

    rows: list[tuple[TopicDTO, bool, bool]] = []

    def _append_branch(current: TopicDTO) -> None:
        children = parent_children.get(current.full_path, [])
        has_children = bool(children)
        is_expanded = current.full_path in expanded_paths
        rows.append((current, has_children, is_expanded))
        if not has_children or not is_expanded:
            return
        for child in children:
            _append_branch(child)

    for root_topic in roots_page:
        _append_branch(root_topic)

    return rows, has_next_page


async def _load_collections_page(
    session_factory: async_sessionmaker,
    *,
    page: int,
    page_size: int = PAGE_SIZE,
) -> tuple[list[SavedViewDTO], bool]:
    async with session_factory() as session:
        service = CollectionService(SavedViewsRepository(session), session)
        rows = await service.list_saved_views()
    return _paginate_rows(rows, page=page, page_size=page_size)


async def _show_list_page(
    callback: CallbackQuery,
    session_factory: async_sessionmaker,
    *,
    state: FSMContext | None = None,
    list_kind: str,
    page: int,
) -> None:
    if state is not None:
        await state.update_data(
            list_entries_back_callback=f"{LIST_PAGE_PREFIX}{list_kind}:{page}",
        )
    status_name, title = _get_list_kind_config(list_kind)
    items, has_next_page = await _load_entries(
        session_factory,
        status_name=status_name,
        page=page,
        page_size=PAGE_SIZE,
    )
    await _show_screen(
        callback,
        _render_entry_list_screen(items, title, page=page),
        build_entry_results_keyboard(
            items,
            back_callback=MENU_LIST,
            back_text="Назад к фильтрам",
            page=page,
            has_prev_page=page > 0,
            has_next_page=has_next_page,
            page_callback_prefix=f"{LIST_PAGE_PREFIX}{list_kind}:",
            entry_back_callback=f"{LIST_PAGE_PREFIX}{list_kind}:{page}",
            merge_pagination_and_back=True,
        ),
    )


async def _show_related_source_page(
    callback: CallbackQuery,
    session_factory: async_sessionmaker,
    *,
    state: FSMContext | None = None,
    page: int,
) -> None:
    if state is not None:
        await state.update_data(
            related_source_back_callback=f"{RELATED_SOURCE_PAGE_PREFIX}{page}",
        )

    items, has_next_page = await _load_entries(
        session_factory,
        status_name=None,
        page=page,
        page_size=PAGE_SIZE,
    )
    await _show_screen(
        callback,
        _render_related_source_screen(items, page=page),
        build_entry_results_keyboard(
            items,
            back_callback=MENU_MAIN,
            back_text="В главное меню",
            page=page,
            has_prev_page=page > 0,
            has_next_page=has_next_page,
            page_callback_prefix=RELATED_SOURCE_PAGE_PREFIX,
            preview_callback_prefix=RELATED_PAGE_PREFIX,
            merge_back_and_main=True,
        ),
    )


async def _show_topics_page(
    callback: CallbackQuery,
    session_factory: async_sessionmaker,
    *,
    state: FSMContext | None = None,
    page: int,
) -> None:
    expanded_paths: set[str] = set()
    if state is not None:
        state_data = await state.get_data()
        expanded_paths = set(_coerce_str_list(state_data.get("topics_expanded_paths")))
        await state.update_data(topics_page=page)

    items, has_next_page = await _load_topics_tree_page(
        session_factory,
        page=page,
        expanded_paths=expanded_paths,
        page_size=PAGE_SIZE,
    )
    await _show_screen(
        callback,
        _render_topics_overview_screen(items, page=page),
        build_topics_tree_keyboard(
            items,
            page=page,
            has_prev_page=page > 0,
            has_next_page=has_next_page,
            page_callback_prefix=TOPICS_PAGE_PREFIX,
        ),
    )


async def _show_topic_entries_page(
    callback: CallbackQuery,
    session_factory: async_sessionmaker,
    *,
    state: FSMContext | None = None,
    topic: TopicDTO,
    topic_id,
    page: int,
) -> None:
    if state is not None:
        await state.update_data(
            topic_view_id=str(topic_id),
            topic_entries_back_callback=f"{TOPIC_ENTRIES_PAGE_PREFIX}{topic_id}:{page}",
        )
    back_callback, back_text = _resolve_topic_entries_back_action(topic)
    rows, has_next_page = await _load_topic_entries(
        session_factory,
        topic_id=topic_id,
        page=page,
        page_size=PAGE_SIZE,
    )
    await _show_screen(
        callback,
        _render_entry_list_screen(
            rows,
            f"Записи темы: {topic.name}",
            page=page,
        ),
        build_entry_results_keyboard(
            rows,
            back_callback=back_callback,
            back_text=back_text,
            page=page,
            has_prev_page=page > 0,
            has_next_page=has_next_page,
            page_callback_prefix=f"{TOPIC_ENTRIES_PAGE_PREFIX}{topic_id}:",
            entry_back_callback=f"{TOPIC_ENTRIES_PAGE_PREFIX}{topic_id}:{page}",
            preview_callback_prefix=TOPIC_ENTRY_PREVIEW_PREFIX,
            extra_rows=build_topic_entries_actions_rows(str(topic_id)),
            merge_back_and_main=True,
        ),
    )


async def _show_entry_move_topics_page(
    callback: CallbackQuery,
    session_factory: async_sessionmaker,
    *,
    state: FSMContext,
    entry_id,
    entry_back_callback: str | None,
    mode: str,
    page: int,
) -> None:
    async with session_factory() as session:
        query_service = QueryService(EntriesRepository(session))
        detail = await query_service.get_entry_detail(entry_id)

    if detail is None:
        await callback.answer("Запись не найдена.", show_alert=True)
        return

    topics, has_next_page = await _load_topics_page(session_factory, page=page, page_size=PAGE_SIZE)
    await state.update_data(
        entry_move_entry_id=str(entry_id),
        entry_move_mode=mode,
        entry_back_callback=entry_back_callback,
    )

    if mode == "pick_parent":
        header = (
            _render_entry_detail_screen(detail)
            + "\n\nВыберите родительскую тему для новой подтемы L1."
        )
    else:
        header = (
            _render_entry_detail_screen(detail)
            + "\n\nВыберите существующую тему для переноса или создайте новую (L0/L1)."
        )

    await _show_screen(
        callback,
        header,
        build_entry_move_topic_keyboard(
            topics=topics,
            mode=mode,
            entry_id=str(entry_id),
            entry_back_callback=entry_back_callback,
            page=page,
            has_prev_page=page > 0,
            has_next_page=has_next_page,
        ),
    )


async def _return_to_list_after_entry_delete(
    callback: CallbackQuery,
    session_factory: async_sessionmaker,
    *,
    state: FSMContext,
    back_callback: str,
) -> bool:
    if back_callback.startswith(TOPIC_ENTRIES_PAGE_PREFIX):
        parsed = _parse_topic_entries_page_callback(back_callback)
        if parsed is None:
            return False
        topic_id, page = parsed
        if page < 0:
            return False

        async with session_factory() as session:
            topic_service = TopicService(TopicsRepository(session))
            topics = await topic_service.list_tree()

        topic = next((item for item in topics if str(item.id) == str(topic_id)), None)
        if topic is None:
            return False

        await _show_topic_entries_page(
            callback,
            session_factory,
            state=state,
            topic=topic,
            topic_id=topic_id,
            page=page,
        )
        return True

    if back_callback.startswith(LIST_PAGE_PREFIX):
        parsed = _parse_list_page_callback(back_callback)
        if parsed is None:
            return False
        list_kind, page = parsed
        if page < 0:
            return False
        await _show_list_page(
            callback,
            session_factory,
            state=state,
            list_kind=list_kind,
            page=page,
        )
        return True

    return False


async def _show_collections_page(
    callback: CallbackQuery,
    session_factory: async_sessionmaker,
    *,
    page: int,
) -> None:
    items, has_next_page = await _load_collections_page(
        session_factory,
        page=page,
        page_size=PAGE_SIZE,
    )
    await _show_screen(
        callback,
        _render_collections_overview_screen(items, page=page),
        build_collections_keyboard(
            items,
            page=page,
            has_prev_page=page > 0,
            has_next_page=has_next_page,
            page_callback_prefix=COLLECTIONS_PAGE_PREFIX,
        ),
    )


async def _show_screen(
    callback: CallbackQuery,
    text: str,
    markup,
    parse_mode: str | None = None,
) -> None:
    await callback.answer()
    if callback.message is None:
        return

    if callback.message.text is None:
        await callback.message.answer(text, reply_markup=markup, parse_mode=parse_mode)
        return

    try:
        await callback.message.edit_text(text, reply_markup=markup, parse_mode=parse_mode)
    except TelegramBadRequest as exc:
        error_text = str(exc).lower()
        if "message is not modified" in error_text:
            current_text = (callback.message.text or "").strip()
            target_text = text.strip()
            if current_text == target_text:
                await callback.message.edit_reply_markup(reply_markup=markup)
                return
            await callback.message.answer(text, reply_markup=markup, parse_mode=parse_mode)
            return
        if parse_mode == "HTML" and "can't parse entities" in error_text:
            fallback_text = _html_to_plain_text(text)
            try:
                await callback.message.edit_text(fallback_text, reply_markup=markup)
            except TelegramBadRequest:
                await callback.message.answer(fallback_text, reply_markup=markup)
            return
        await callback.message.answer(text, reply_markup=markup, parse_mode=parse_mode)


async def _safe_delete_message(message: Message) -> None:
    try:
        await message.delete()
    except TelegramBadRequest:
        return


def _render_stats_screen(stats: dict) -> str:
    status_lines = [f"- {k}: {v}" for k, v in sorted(stats["by_status"].items())]
    topic_lines = [f"- {k}: {v}" for k, v in sorted(stats["by_topic"].items())]
    return (
        "Статистика:\n"
        f"Всего записей: {stats['total_entries']}\n"
        f"Inbox (New): {stats['inbox_size']}\n"
        f"Backlog (To Read): {stats['backlog']}\n"
        f"Покрытие Verified: {stats['verified_coverage']}\n"
        f"Предотвращено дублей: {stats['duplicates_prevented']}\n\n"
        "По статусам:\n"
        + ("\n".join(status_lines) if status_lines else "-")
        + "\n\nПо темам:\n"
        + ("\n".join(topic_lines) if topic_lines else "-")
    )


def _render_topics_screen(topics: list[TopicDTO]) -> str:
    if not topics:
        return "Темы пока не найдены."

    lines = []
    for topic in topics:
        indent = "  " * topic.level
        lines.append(f"{indent}- {topic.name}")
    return "Темы:\n" + "\n".join(lines)


def _render_topic_detail_screen(topic: TopicDTO, entries: list[EntryDetail] | None = None) -> str:
    header = (
        "Карточка темы:\n"
        f"ID: `{topic.id}`\n"
        f"Название: {topic.name}\n"
        f"Путь: {topic.full_path}\n"
        f"Уровень: {topic.level}"
    )
    if entries is None:
        return header

    if not entries:
        return header + "\n\nПоследние записи в теме:\n- Пока пусто."

    lines: list[str] = []
    for item in entries:
        lines.append(f"- {item.title} [{item.status_name}]")
        link = item.normalized_url or item.original_url
        if link:
            lines.append(f"  Ссылка: {link}")
    return header + "\n\nПоследние записи в теме:\n" + "\n".join(lines)


def _render_entry_list_screen(items: list[EntryDetail], title: str, *, page: int = 0) -> str:
    header = title if page == 0 else f"{title} (страница {page + 1})"
    if not items and title.startswith("Записи темы:"):
        return f"{header}:\nЗаписей не найдено."

    if not items:
        return (
            f"{header}:\n"
            "Записей не найдено.\n\n"
            "Что можно сделать дальше:\n"
            "- вернуться к быстрым фильтрам;\n"
            "- выбрать другой статус;\n"
            "- добавить новую запись через меню."
        )

    return f"{header}:\nВыберите запись кнопкой ниже."


def _render_collection_result_screen(view: SavedViewDTO, items: list[EntryDetail]) -> str:
    snapshot = view.filter_snapshot
    summary = (
        f"Коллекция: {view.name}\n"
        f"Фильтр status: {snapshot.get('status_name') or '-'}\n"
        f"Фильтр topic: {snapshot.get('topic_id') or '-'}\n"
        f"Лимит: {snapshot.get('limit') or '-'}"
    )
    if not items:
        return (
            summary
            + "\n\nДля текущих фильтров записей не найдено.\n"
            "Проверьте фильтр статуса/темы или увеличьте лимит."
        )
    return summary + "\n\nВыберите запись кнопкой ниже."


def _render_backups_list_screen(rows: list) -> str:
    if not rows:
        return "Backups:\nСписок пуст."
    lines = ["Backups:"]
    for row in rows[:10]:
        lines.append(f"- `{row.id}` | {row.filename} | tested={row.restore_tested_at or '-'}")
    return "\n".join(lines)


def _render_search_results_screen(items: list, query: str, *, page: int = 0) -> str:
    if not items:
        return (
            f"По запросу `{query}` ничего не найдено.\n"
            "Попробуйте уточнить формулировку или сократить запрос."
        )
    page_hint = "" if page == 0 else f" (страница {page + 1})"
    return (
        f"Результаты поиска по запросу `{query}`{page_hint}:\n"
        "Выберите запись кнопкой ниже."
    )


def _render_related_source_screen(items: list[EntryDetail], *, page: int = 0) -> str:
    page_hint = "" if page == 0 else f" (страница {page + 1})"
    if not items:
        return (
            f"Похожие материалы{page_hint}:\n"
            "Список записей пуст.\n\n"
            "Добавьте записи через меню `Добавить` или импорт."
        )
    return (
        f"Похожие материалы{page_hint}:\n"
        "Выберите исходную запись кнопкой ниже.\n"
        "После выбора бот покажет релевантные материалы."
    )


def _render_entry_detail_screen(detail: EntryDetail) -> str:
    compact_notes = _render_compact_card_notes(detail.notes)
    body = _render_card_body_text(detail.description, fallback=detail.notes)
    return (
        "Карточка записи:\n"
        f"ID: `{detail.entry_id}`\n"
        f"Заголовок: {detail.title}\n"
        f"Статус: {detail.status_name}\n"
        f"Тема: {detail.topic_name}\n"
        f"URL: {detail.normalized_url or detail.original_url or '-'}\n"
        f"Заметки: {compact_notes}\n"
        f"Текст:\n{body}"
    )


def _render_entry_preview_screen(detail: EntryDetail) -> str:
    if detail.description:
        return _render_preview_block(detail.description)
    if detail.notes:
        return _render_preview_block(detail.notes)
    if detail.title:
        return _render_preview_block(detail.title)
    return "-"


_HTML_TAG_RE = re.compile(r"</?[a-zA-Z][^>]*>")
_HTML_BR_RE = re.compile(r"(?i)<br\s*/?>")
_HTML_BLOCK_CLOSE_RE = re.compile(r"(?i)</(?:p|div|li|h[1-6]|blockquote)>")


def _render_entry_preview_screen_html(detail: EntryDetail) -> str:
    if detail.description:
        return _render_preview_block_html(detail.description)
    if detail.notes:
        return _render_preview_block_html(detail.notes)
    if detail.title:
        return _render_preview_block_html(detail.title)
    return "-"


def _allowed_target_statuses(current_status: str) -> list[str]:
    options = sorted(ALLOWED_STATUS_TRANSITIONS.get(current_status, set()))
    if not options:
        return []
    return options


async def _build_topics_keyboard_from_db(session_factory: async_sessionmaker, *, page: int = 0):
    items, has_next_page = await _load_topics_tree_page(
        session_factory,
        page=page,
        expanded_paths=set(),
        page_size=PAGE_SIZE,
    )
    return build_topics_tree_keyboard(
        items,
        page=page,
        has_prev_page=page > 0,
        has_next_page=has_next_page,
        page_callback_prefix=TOPICS_PAGE_PREFIX,
    )


def _render_topics_overview_screen(topics: list[tuple[TopicDTO, bool, bool]], *, page: int = 0) -> str:
    if not topics and page == 0:
        return "Темы пока не найдены.\n\nМожно создать первую тему кнопкой ниже."
    if not topics:
        return "Темы:\nСтраница пуста. Вернитесь назад."
    page_hint = "" if page == 0 else f" (страница {page + 1})"
    return (
        f"Темы{page_hint}:\n"
        "Выберите тему кнопкой ниже.\n"
        "Нажмите `▶/▼`, чтобы свернуть или развернуть подтемы."
    )


async def _build_collections_keyboard_from_db(session_factory: async_sessionmaker, *, page: int = 0):
    items, has_next_page = await _load_collections_page(session_factory, page=page, page_size=PAGE_SIZE)
    return build_collections_keyboard(
        items,
        page=page,
        has_prev_page=page > 0,
        has_next_page=has_next_page,
        page_callback_prefix=COLLECTIONS_PAGE_PREFIX,
    )


def _render_collections_overview_screen(collections: list[SavedViewDTO], *, page: int = 0) -> str:
    if not collections and page == 0:
        return (
            "Сохраненные коллекции пока не найдены.\n\n"
            "Создать новую коллекцию пока можно командой:\n"
            "/collection_add <name> [status=...] [topic=...] [limit=...]"
        )
    if not collections:
        return "Коллекции:\nСтраница пуста. Вернитесь назад."
    page_hint = "" if page == 0 else f" (страница {page + 1})"
    return f"Коллекции{page_hint}:\nВыберите сохраненную коллекцию кнопкой ниже."


def _parse_entry_id_from_callback(raw: str | None, prefix: str):
    import uuid

    if not raw or not raw.startswith(prefix):
        return None
    try:
        return uuid.UUID(raw[len(prefix) :])
    except ValueError:
        return None


def _parse_entry_view_callback(raw: str | None):
    import uuid

    if not raw or not raw.startswith(ENTRY_VIEW_PREFIX):
        return None

    payload = raw[len(ENTRY_VIEW_PREFIX) :]
    entry_part, separator, back_callback = payload.partition(":")
    try:
        entry_id = uuid.UUID(entry_part)
    except ValueError:
        return None

    if not separator:
        return entry_id, None
    if not back_callback:
        return entry_id, None
    return entry_id, back_callback


def _parse_status_update_callback(raw: str | None):
    import uuid

    if not raw or not raw.startswith(ENTRY_STATUS_PREFIX):
        return None
    payload = raw[len(ENTRY_STATUS_PREFIX) :]
    entry_part, separator, status_name = payload.partition(":")
    if not separator or not status_name:
        return None
    try:
        return uuid.UUID(entry_part), status_name
    except ValueError:
        return None


def _parse_entry_edit_field_callback(raw: str | None):
    import uuid

    if not raw or not raw.startswith(ENTRY_EDIT_FIELD_PREFIX):
        return None
    payload = raw[len(ENTRY_EDIT_FIELD_PREFIX) :]
    entry_part, separator, field_name = payload.partition(":")
    if not separator or not field_name:
        return None
    if field_name not in {"title", "url", "description", "notes"}:
        return None
    try:
        return uuid.UUID(entry_part), field_name
    except ValueError:
        return None


def _parse_list_page_callback(raw: str | None):
    if not raw or not raw.startswith(LIST_PAGE_PREFIX):
        return None
    payload = raw[len(LIST_PAGE_PREFIX) :]
    list_kind, separator, page_raw = payload.partition(":")
    if not separator:
        return None
    try:
        page = int(page_raw)
    except ValueError:
        return None
    if list_kind not in {LIST_KIND_ALL, LIST_KIND_NEW, LIST_KIND_TO_READ, LIST_KIND_VERIFIED}:
        return None
    return list_kind, page


def _parse_topic_entries_page_callback(raw: str | None):
    import uuid

    if not raw or not raw.startswith(TOPIC_ENTRIES_PAGE_PREFIX):
        return None

    payload = raw[len(TOPIC_ENTRIES_PAGE_PREFIX) :]
    topic_part, separator, page_raw = payload.partition(":")
    if not separator:
        return None

    try:
        topic_id = uuid.UUID(topic_part)
        page = int(page_raw)
    except ValueError:
        return None
    return topic_id, page


def _parse_page_callback(raw: str | None, prefix: str):
    if not raw or not raw.startswith(prefix):
        return None
    value = raw[len(prefix) :]
    try:
        return int(value)
    except ValueError:
        return None


def _get_list_kind_config(list_kind: str):
    mapping = {
        LIST_KIND_ALL: (None, "Последние записи"),
        LIST_KIND_NEW: ("New", "Статус New"),
        LIST_KIND_TO_READ: ("To Read", "Статус To Read"),
        LIST_KIND_VERIFIED: ("Verified", "Статус Verified"),
    }
    return mapping.get(list_kind, (None, "Последние записи"))


def _resolve_topic_entries_back_action(topic: TopicDTO) -> tuple[str, str]:
    return MENU_TOPICS, "Назад к списку тем"


def _resolve_entry_back_action(entry_back_callback: str | None):
    if not entry_back_callback:
        return MENU_LIST, "Назад к фильтрам"
    if entry_back_callback.startswith(LIST_PAGE_PREFIX):
        return entry_back_callback, "Назад к списку"
    if entry_back_callback.startswith(SEARCH_PAGE_PREFIX):
        return entry_back_callback, "Назад к поиску"
    if entry_back_callback.startswith(RELATED_PAGE_PREFIX):
        return entry_back_callback, "Назад к похожим"
    if entry_back_callback.startswith(TOPIC_ENTRIES_PAGE_PREFIX):
        return entry_back_callback, "Назад к записям"
    if entry_back_callback.startswith(TOPIC_VIEW_PREFIX):
        return entry_back_callback, "Назад к теме"
    if entry_back_callback == MENU_TOPICS:
        return MENU_TOPICS, "Назад к списку тем"
    if entry_back_callback == MENU_COLLECTIONS:
        return MENU_COLLECTIONS, "К коллекциям"
    if entry_back_callback == MENU_LIST:
        return MENU_LIST, "Назад к фильтрам"
    return MENU_LIST, "Назад к фильтрам"


def _resolve_entry_action_back_context(state_data: dict) -> tuple[str | None, str, str]:
    raw_back_callback = state_data.get("entry_back_callback")
    if isinstance(raw_back_callback, str) and raw_back_callback.strip():
        back_callback, back_text = _resolve_entry_back_action(raw_back_callback)
        stored_back_text = state_data.get("entry_back_text")
        if isinstance(stored_back_text, str) and stored_back_text.strip():
            back_text = stored_back_text.strip()
        return raw_back_callback, back_callback, back_text

    inferred_back_callback = _resolve_entry_back_callback_from_state(state_data)
    back_callback, back_text = _resolve_entry_back_action(inferred_back_callback)
    return inferred_back_callback, back_callback, back_text


def _resolve_entry_back_callback_from_state(state_data: dict) -> str | None:
    topic_entries_callback = state_data.get("topic_entries_back_callback")
    if isinstance(topic_entries_callback, str) and topic_entries_callback.startswith(TOPIC_ENTRIES_PAGE_PREFIX):
        return topic_entries_callback

    list_entries_callback = state_data.get("list_entries_back_callback")
    if isinstance(list_entries_callback, str) and list_entries_callback.startswith(LIST_PAGE_PREFIX):
        return list_entries_callback

    topic_id = _parse_uuid_string(state_data.get("topic_view_id"))
    if topic_id is not None:
        return f"{TOPIC_VIEW_PREFIX}{topic_id}"
    return None


def _resolve_status_back_action(state_data: dict):
    back_callback, back_text = _resolve_entry_back_action(state_data.get("entry_back_callback"))
    stored_back_text = state_data.get("entry_back_text")
    if isinstance(stored_back_text, str) and stored_back_text.strip():
        return back_callback, stored_back_text.strip()
    return back_callback, back_text


def _parse_uuid_string(raw: str | None):
    import uuid

    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None


def _coerce_str_list(raw: object) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, str) and item.strip()]


def _topic_parent_path(full_path: str) -> str | None:
    if "." not in full_path:
        return None
    parent_path, _, _ = full_path.rpartition(".")
    return parent_path or None


async def _clear_entry_move_draft_state(state: FSMContext) -> None:
    await state.update_data(
        entry_move_create_level=None,
        entry_move_parent_topic_id=None,
    )


async def _clear_entry_move_state(state: FSMContext) -> None:
    await _clear_entry_move_draft_state(state)
    await state.update_data(
        entry_move_entry_id=None,
        entry_move_mode=None,
    )


async def _clear_entry_edit_state(state: FSMContext) -> None:
    await state.update_data(
        entry_edit_entry_id=None,
        entry_edit_field=None,
    )


def _render_preview_block(value: str | None, *, limit: int = 1200) -> str:
    if not value:
        return "-"
    compact = value.strip()
    if not compact:
        return "-"
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def _render_preview_block_html(value: str | None, *, limit: int = 1200) -> str:
    if not value:
        return "-"
    compact = value.strip()
    if not compact:
        return "-"
    if _HTML_TAG_RE.search(compact):
        # Keep rich formatting when possible. For known problematic Telegram
        # variants (e.g. <blockquote expandable>) normalize to safe markup.
        safe_html = re.sub(r"(?i)<blockquote[^>]*>", "<blockquote>", compact)
        # Custom emoji identifiers from external sources can be invalid for the
        # current bot and crash HTML parsing. Keep plain glyph text only.
        safe_html = re.sub(r"(?is)<tg-emoji[^>]*>", "", safe_html)
        safe_html = re.sub(r"(?is)</tg-emoji>", "", safe_html)
        if len(_html_to_plain_text(safe_html)) > limit:
            truncated = _html_to_plain_text(safe_html)[: limit - 1] + "…"
            return html.escape(truncated)
        return safe_html
    if len(compact) > limit:
        compact = compact[: limit - 1] + "…"
    return html.escape(compact)


def _render_compact_card_notes(value: str | None, *, limit: int = 260) -> str:
    if not value:
        return "-"
    # Keep the card scannable: notes can be very long for forwarded posts.
    compact = " ".join(value.split())
    if not compact:
        return "-"
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def _render_card_body_text(value: str | None, *, fallback: str | None = None, limit: int = 260) -> str:
    primary = value or fallback
    if not primary:
        return "-"

    compact = primary.strip()
    if not compact:
        return "-"

    if _HTML_TAG_RE.search(compact):
        compact = _html_to_plain_text(compact)

    if len(compact) <= limit:
        return compact
    return compact[: limit - 1] + "…"


def _html_to_plain_text(value: str) -> str:
    normalized = _HTML_BR_RE.sub("\n", value)
    normalized = _HTML_BLOCK_CLOSE_RE.sub("\n\n", normalized)
    normalized = _HTML_TAG_RE.sub("", normalized)
    normalized = html.unescape(normalized)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()
