from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.services.stats_service import StatsService


def create_stats_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("stats"))
    async def stats_handler(message: Message) -> None:
        async with session_factory() as session:
            service = StatsService(session)
            stats = await service.get_stats()

        status_lines = [f"- {k}: {v}" for k, v in sorted(stats["by_status"].items())]
        topic_lines = [f"- {k}: {v}" for k, v in sorted(stats["by_topic"].items())]
        await message.answer(
            "Stats:\n"
            f"Total entries: {stats['total_entries']}\n"
            f"Inbox size (New): {stats['inbox_size']}\n"
            f"Backlog (To Read): {stats['backlog']}\n"
            f"Verified coverage: {stats['verified_coverage']}\n"
            f"Duplicates prevented: {stats['duplicates_prevented']}\n\n"
            "By status:\n"
            + ("\n".join(status_lines) if status_lines else "-")
            + "\n\nBy topic:\n"
            + ("\n".join(topic_lines) if topic_lines else "-")
        )

    return router

