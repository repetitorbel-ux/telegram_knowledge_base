from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.core.entry_parsing import parse_entry_command
from kb_bot.db.repositories.entries import EntriesRepository
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
            f"Entry details:\n"
            f"ID: `{detail.entry_id}`\n"
            f"Title: {detail.title}\n"
            f"Status: {detail.status_name}\n"
            f"Topic: {detail.topic_name}\n"
            f"URL: {detail.normalized_url or detail.original_url or '-'}\n"
            f"Notes: {detail.notes or '-'}"
        )

    return router

