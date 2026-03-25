from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.core.list_parsing import parse_list_command
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.services.query_service import QueryService


def create_list_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("list"))
    async def list_handler(message: Message) -> None:
        filters = parse_list_command(message.text)
        async with session_factory() as session:
            service = QueryService(EntriesRepository(session))
            items = await service.list_entries(
                status_name=filters.status_name,
                topic_id=filters.topic_id,
                limit=filters.limit,
            )

        if not items:
            await message.answer("No entries found for given filters.")
            return

        lines = []
        for item in items:
            lines.append(f"- `{item.entry_id}` | {item.title} [{item.status_name}] ({item.topic_name})")
        await message.answer("Entries:\n" + "\n".join(lines))

    return router

