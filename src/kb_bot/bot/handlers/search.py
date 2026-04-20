import uuid

from aiogram import F
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.bot.handlers.menu import _show_screen
from kb_bot.bot.ui.callbacks import ENTRY_VIEW_PREFIX, RELATED_PAGE_PREFIX
from kb_bot.bot.ui.keyboards import build_entry_results_keyboard
from kb_bot.core.entry_parsing import parse_entry_command
from kb_bot.core.search_parsing import parse_search_query
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.domain.dto import RelatedEntryDTO
from kb_bot.domain.errors import EntryNotFoundError
from kb_bot.services.query_service import QueryService
from kb_bot.services.search_service import SearchService

RELATED_PAGE_SIZE = 5


def create_search_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("search"))
    async def search_handler(message: Message) -> None:
        query = parse_search_query(message.text)
        if not query:
            await message.answer("Usage: /search <query>")
            return

        async with session_factory() as session:
            service = SearchService(EntriesRepository(session))
            rows = await service.search(query, limit=10)

        if not rows:
            await message.answer("No results found.")
            return

        lines = []
        for item in rows:
            lines.append(f"- {item.title} [{item.status_name}]")
        await message.answer("Search results:\n" + "\n".join(lines))

    @router.message(Command("related"))
    async def related_handler(message: Message) -> None:
        entry_id = parse_entry_command(message.text)
        if entry_id is None:
            await message.answer("Usage: /related <entry_uuid>")
            return
        await _show_related_message(message, session_factory, entry_id=entry_id, page=0)

    @router.callback_query(F.data.startswith(RELATED_PAGE_PREFIX))
    async def related_page_handler(callback: CallbackQuery) -> None:
        parsed = _parse_related_page_callback(callback.data)
        if parsed is None:
            await callback.answer("Не удалось открыть похожие записи.", show_alert=True)
            return
        entry_id, page = parsed
        if page < 0:
            await callback.answer("Страница вне диапазона.", show_alert=True)
            return

        async with session_factory() as session:
            query_service = QueryService(EntriesRepository(session))
            source_detail = await query_service.get_entry_detail(entry_id)
            if source_detail is None:
                await callback.answer("Исходная запись не найдена.", show_alert=True)
                return

            service = SearchService(EntriesRepository(session))
            offset = page * RELATED_PAGE_SIZE
            rows = await service.related(entry_id=entry_id, limit=RELATED_PAGE_SIZE + 1, offset=offset)

        has_next_page = len(rows) > RELATED_PAGE_SIZE
        visible_rows = rows[:RELATED_PAGE_SIZE]
        await _show_screen(
            callback,
            _render_related_results_screen(source_detail.title, visible_rows, page=page),
            _build_related_results_keyboard(
                visible_rows,
                entry_id=entry_id,
                page=page,
                has_next_page=has_next_page,
            ),
        )

    return router


async def _show_related_message(
    message: Message,
    session_factory: async_sessionmaker,
    *,
    entry_id: uuid.UUID,
    page: int,
) -> None:
    async with session_factory() as session:
        query_service = QueryService(EntriesRepository(session))
        source_detail = await query_service.get_entry_detail(entry_id)
        if source_detail is None:
            await message.answer("Entry not found.")
            return

        service = SearchService(EntriesRepository(session))
        try:
            rows = await service.related(
                entry_id=entry_id,
                limit=RELATED_PAGE_SIZE + 1,
                offset=page * RELATED_PAGE_SIZE,
            )
        except EntryNotFoundError:
            await message.answer("Entry not found.")
            return

    has_next_page = len(rows) > RELATED_PAGE_SIZE
    visible_rows = rows[:RELATED_PAGE_SIZE]
    await message.answer(
        _render_related_results_screen(source_detail.title, visible_rows, page=page),
        reply_markup=_build_related_results_keyboard(
            visible_rows,
            entry_id=entry_id,
            page=page,
            has_next_page=has_next_page,
        ),
    )


def _parse_related_page_callback(raw: str | None) -> tuple[uuid.UUID, int] | None:
    if not raw or not raw.startswith(RELATED_PAGE_PREFIX):
        return None
    payload = raw[len(RELATED_PAGE_PREFIX) :]
    entry_part, separator, page_raw = payload.partition(":")
    if not separator:
        try:
            return uuid.UUID(entry_part), 0
        except ValueError:
            return None

    try:
        entry_id = uuid.UUID(entry_part)
        page = int(page_raw)
    except ValueError:
        return None
    return entry_id, page


def _render_related_results_screen(
    source_title: str,
    items: list[RelatedEntryDTO],
    *,
    page: int,
) -> str:
    page_hint = "" if page == 0 else f" (страница {page + 1})"
    header = f"Похожие материалы для: {source_title}{page_hint}"
    if not items:
        return header + "\n\nПохожих записей не найдено."
    return header


def _build_related_results_keyboard(
    items: list[RelatedEntryDTO],
    *,
    entry_id: uuid.UUID,
    page: int,
    has_next_page: bool,
):
    return build_entry_results_keyboard(
        items,
        back_callback=f"{ENTRY_VIEW_PREFIX}{entry_id}",
        back_text="К исходной записи",
        page=page,
        has_prev_page=page > 0,
        has_next_page=has_next_page,
        page_callback_prefix=f"{RELATED_PAGE_PREFIX}{entry_id}:",
        entry_back_callback=f"{RELATED_PAGE_PREFIX}{entry_id}:{page}",
        extra_rows=[
            [
                InlineKeyboardButton(
                    text="Обновить",
                    callback_data=f"{RELATED_PAGE_PREFIX}{entry_id}:{page}",
                )
            ]
        ],
    )
