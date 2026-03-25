from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.core.search_parsing import parse_search_query
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.services.search_service import SearchService


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

    return router
