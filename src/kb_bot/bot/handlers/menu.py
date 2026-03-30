from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.bot.fsm.states import (
    AddEntryStates,
    GuidedSearchStates,
    GuidedImportStates,
    TopicCreateStates,
    TopicRenameStates,
)
from kb_bot.bot.handlers.start import render_welcome_text
from kb_bot.bot.ui.callbacks import (
    COLLECTION_VIEW_PREFIX,
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
    MENU_TOPICS,
    SEARCH_PAGE_PREFIX,
    TOPIC_RENAME_PREFIX,
    TOPIC_VIEW_PREFIX,
)
from kb_bot.bot.ui.keyboards import (
    build_backups_keyboard,
    build_import_export_keyboard,
    build_collections_keyboard,
    build_flow_navigation_keyboard,
    build_entry_detail_keyboard,
    build_entry_results_keyboard,
    build_home_navigation_keyboard,
    build_list_filters_keyboard,
    build_main_menu_keyboard,
    build_topic_detail_keyboard,
    build_topics_keyboard,
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

        async with session_factory() as session:
            service = TopicService(TopicsRepository(session), session)
            try:
                topic = await service.create_topic(name=name)
            except (ValueError, TopicConflictError, TopicNotFoundError) as exc:
                await message.answer(str(exc), reply_markup=build_flow_navigation_keyboard())
                return

        await state.clear()
        await message.answer(
            f"Тема создана: {topic.name}",
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
    async def list_all(callback: CallbackQuery) -> None:
        await _show_list_page(callback, session_factory, list_kind=LIST_KIND_ALL, page=0)

    @router.callback_query(StateFilter("*"), F.data == LIST_NEW)
    async def list_new(callback: CallbackQuery) -> None:
        await _show_list_page(callback, session_factory, list_kind=LIST_KIND_NEW, page=0)

    @router.callback_query(StateFilter("*"), F.data == LIST_TO_READ)
    async def list_to_read(callback: CallbackQuery) -> None:
        await _show_list_page(callback, session_factory, list_kind=LIST_KIND_TO_READ, page=0)

    @router.callback_query(StateFilter("*"), F.data == LIST_VERIFIED)
    async def list_verified(callback: CallbackQuery) -> None:
        await _show_list_page(callback, session_factory, list_kind=LIST_KIND_VERIFIED, page=0)

    @router.callback_query(StateFilter("*"), F.data.startswith(LIST_PAGE_PREFIX))
    async def list_page(callback: CallbackQuery) -> None:
        parsed = _parse_list_page_callback(callback.data)
        if parsed is None:
            await callback.answer("Не удалось открыть страницу списка.", show_alert=True)
            return

        list_kind, page = parsed
        if page < 0:
            await callback.answer("Страница вне диапазона.", show_alert=True)
            return

        await _show_list_page(callback, session_factory, list_kind=list_kind, page=page)

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_VIEW_PREFIX))
    async def entry_view(callback: CallbackQuery, state: FSMContext) -> None:
        parsed = _parse_entry_view_callback(callback.data)
        if parsed is None:
            await callback.answer("Не удалось открыть запись.", show_alert=True)
            return
        entry_id, entry_back_callback = parsed
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

    @router.callback_query(StateFilter("*"), F.data.startswith(ENTRY_STATUS_PREFIX))
    async def entry_status_update(callback: CallbackQuery, state: FSMContext) -> None:
        parsed = _parse_status_update_callback(callback.data)
        if parsed is None:
            await callback.answer("Не удалось прочитать действие.", show_alert=True)
            return
        entry_id, status_name = parsed
        state_data = await state.get_data()
        back_callback, back_text = _resolve_entry_back_action(state_data.get("entry_back_callback"))
        stored_back_text = state_data.get("entry_back_text")
        if isinstance(stored_back_text, str) and stored_back_text.strip():
            back_text = stored_back_text

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
        await _show_screen(
            callback,
            await _render_topics_overview_screen(session_factory),
            await _build_topics_keyboard_from_db(session_factory),
        )

    @router.callback_query(StateFilter("*"), F.data == MENU_TOPIC_CREATE)
    async def menu_topic_create(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await state.set_state(TopicCreateStates.waiting_name)
        await _show_screen(
            callback,
            "Создание корневой темы.\nОтправьте название новой темы следующим сообщением.",
            build_flow_navigation_keyboard(),
        )

    @router.callback_query(F.data.startswith(TOPIC_VIEW_PREFIX))
    async def topic_view(callback: CallbackQuery) -> None:
        topic_id = _parse_entry_id_from_callback(callback.data, TOPIC_VIEW_PREFIX)
        if topic_id is None:
            await callback.answer("Не удалось открыть тему.", show_alert=True)
            return

        async with session_factory() as session:
            service = TopicService(TopicsRepository(session))
            topics = await service.list_tree()

        topic = next((item for item in topics if str(item.id) == str(topic_id)), None)
        if topic is None:
            await callback.answer("Тема не найдена.", show_alert=True)
            return

        await _show_screen(
            callback,
            _render_topic_detail_screen(topic),
            build_topic_detail_keyboard(str(topic.id)),
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
        await _show_screen(
            callback,
            await _render_collections_overview_screen(session_factory),
            await _build_collections_keyboard_from_db(session_factory),
        )

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
            else await _build_collections_keyboard_from_db(session_factory)
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
            rows = await service.list_backups()
        if callback.message is not None:
            await callback.message.answer(
                _render_backups_list_screen(rows),
                reply_markup=build_backups_keyboard(),
            )
            

    @router.callback_query(StateFilter("*"), F.data == MENU_HELP)
    async def menu_help(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await _show_screen(
            callback,
            "Сейчас бот поддерживает два режима работы:\n"
            "- через кнопки и меню\n"
            "- через текстовые команды\n\n"
            "Быстрые команды:\n"
            "/start\n"
            "/add\n"
            "/search <query>\n"
            "/list [status=New] [topic=<uuid>] [limit=20]\n"
            "/topics\n"
            "/stats\n"
            "/backup\n"
            "/backups\n\n"
            "Если вы в пошаговом сценарии, используйте кнопку `Отмена` или `/cancel`.",
            build_home_navigation_keyboard(),
        )

    return router


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


async def _show_list_page(
    callback: CallbackQuery,
    session_factory: async_sessionmaker,
    *,
    list_kind: str,
    page: int,
) -> None:
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
        ),
    )


async def _show_screen(
    callback: CallbackQuery,
    text: str,
    markup,
) -> None:
    await callback.answer()
    if callback.message is None:
        return

    if callback.message.text is None:
        await callback.message.answer(text, reply_markup=markup)
        return

    try:
        await callback.message.edit_text(text, reply_markup=markup)
    except TelegramBadRequest as exc:
        error_text = str(exc).lower()
        if "message is not modified" in error_text:
            await callback.message.edit_reply_markup(reply_markup=markup)
            return
        await callback.message.answer(text, reply_markup=markup)


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


def _render_topic_detail_screen(topic: TopicDTO) -> str:
    return (
        "Карточка темы:\n"
        f"ID: `{topic.id}`\n"
        f"Название: {topic.name}\n"
        f"Путь: {topic.full_path}\n"
        f"Уровень: {topic.level}"
    )


def _render_entry_list_screen(items: list[EntryDetail], title: str, *, page: int = 0) -> str:
    header = title if page == 0 else f"{title} (страница {page + 1})"
    if not items:
        return (
            f"{header}:\n"
            "Записей не найдено.\n\n"
            "Что можно сделать дальше:\n"
            "- вернуться к быстрым фильтрам;\n"
            "- выбрать другой статус;\n"
            "- добавить новую запись через меню."
        )

    lines = [header + ":"]
    for item in items:
        lines.append(f"- {item.title} [{item.status_name}] ({item.topic_name})")
    return "\n".join(lines)


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


def _render_entry_detail_screen(detail: EntryDetail) -> str:
    return (
        "Карточка записи:\n"
        f"ID: `{detail.entry_id}`\n"
        f"Заголовок: {detail.title}\n"
        f"Статус: {detail.status_name}\n"
        f"Тема: {detail.topic_name}\n"
        f"URL: {detail.normalized_url or detail.original_url or '-'}\n"
        f"Заметки: {detail.notes or '-'}"
    )


def _allowed_target_statuses(current_status: str) -> list[str]:
    options = sorted(ALLOWED_STATUS_TRANSITIONS.get(current_status, set()))
    if not options:
        return []
    return options


async def _build_topics_keyboard_from_db(session_factory: async_sessionmaker):
    async with session_factory() as session:
        service = TopicService(TopicsRepository(session))
        topics = await service.list_tree()
    return build_topics_keyboard(topics)


async def _render_topics_overview_screen(session_factory: async_sessionmaker) -> str:
    async with session_factory() as session:
        service = TopicService(TopicsRepository(session))
        topics = await service.list_tree()
    if not topics:
        return "Темы пока не найдены.\n\nМожно создать первую тему кнопкой ниже."
    return "Темы:\nВыберите тему кнопкой ниже или создайте новую."


async def _build_collections_keyboard_from_db(session_factory: async_sessionmaker):
    async with session_factory() as session:
        service = CollectionService(SavedViewsRepository(session), session)
        collections = await service.list_saved_views()
    return build_collections_keyboard(collections)


async def _render_collections_overview_screen(session_factory: async_sessionmaker) -> str:
    async with session_factory() as session:
        service = CollectionService(SavedViewsRepository(session), session)
        collections = await service.list_saved_views()
    if not collections:
        return (
            "Сохраненные коллекции пока не найдены.\n\n"
            "Создать новую коллекцию пока можно командой:\n"
            "/collection_add <name> [status=...] [topic=...] [limit=...]"
        )
    return "Коллекции:\nВыберите сохраненную коллекцию кнопкой ниже."


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


def _resolve_entry_back_action(entry_back_callback: str | None):
    if not entry_back_callback:
        return MENU_LIST, "Назад к фильтрам"
    if entry_back_callback.startswith(LIST_PAGE_PREFIX):
        return entry_back_callback, "Назад к списку"
    if entry_back_callback.startswith(SEARCH_PAGE_PREFIX):
        return entry_back_callback, "Назад к поиску"
    if entry_back_callback == MENU_COLLECTIONS:
        return MENU_COLLECTIONS, "К коллекциям"
    if entry_back_callback == MENU_LIST:
        return MENU_LIST, "Назад к фильтрам"
    return MENU_LIST, "Назад к фильтрам"


def _parse_uuid_string(raw: str | None):
    import uuid

    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError:
        return None
