from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.bot.handlers.menu import _allowed_target_statuses, _render_entry_detail_screen
from kb_bot.bot.ui.keyboards import build_entry_detail_keyboard
from kb_bot.core.entry_parsing import parse_entry_command
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import EntryNotFoundError
from kb_bot.services.entry_service import EntryService
from kb_bot.services.query_service import QueryService


def create_entry_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("entry"))
    async def entry_handler(message: Message) -> None:
        entry_id = parse_entry_command(message.text)
        if entry_id is None:
            await message.answer("Usage: /entry <entry_uuid>")
            return

        async with session_factory() as session:
            service = QueryService(EntriesRepository(session))
            detail = await service.get_entry_detail(entry_id)

        if detail is None:
            await message.answer("Entry not found.")
            return

        await message.answer(
            _render_entry_detail_screen(detail),
            reply_markup=build_entry_detail_keyboard(
                str(detail.entry_id),
                _allowed_target_statuses(detail.status_name),
            ),
        )

    @router.message(Command("entry_delete"))
    async def entry_delete_handler(message: Message) -> None:
        entry_id = parse_entry_command(message.text)
        if entry_id is None:
            await message.answer("Usage: /entry_delete <entry_uuid>")
            return

        async with session_factory() as session:
            service = EntryService(
                session=session,
                entries_repo=EntriesRepository(session),
                topics_repo=TopicsRepository(session),
                statuses_repo=StatusesRepository(session),
            )
            try:
                await service.delete(entry_id)
            except EntryNotFoundError:
                await message.answer("Entry not found.")
                return

        await message.answer(f"Entry deleted: `{entry_id}`")

    return router
