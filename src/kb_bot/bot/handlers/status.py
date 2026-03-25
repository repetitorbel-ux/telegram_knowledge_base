from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.core.status_parsing import parse_status_command
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import EntryNotFoundError, InvalidStatusTransitionError, StatusNotFoundError
from kb_bot.services.entry_service import EntryService


def create_status_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("status"))
    async def status_handler(message: Message) -> None:
        entry_id, status_name = parse_status_command(message.text)
        if entry_id is None or status_name is None:
            await message.answer("Usage: /status <entry_uuid> <status name>")
            return

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
                await message.answer("Entry not found.")
                return
            except StatusNotFoundError:
                await message.answer("Unknown status name.")
                return
            except InvalidStatusTransitionError as exc:
                await message.answer(str(exc))
                return

        await message.answer(f"Status updated: `{updated.id}` -> {updated.status_name}")

    return router

