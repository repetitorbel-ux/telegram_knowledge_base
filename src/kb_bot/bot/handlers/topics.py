from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.services.topic_service import TopicService


def create_topics_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("topics"))
    async def topics_handler(message: Message) -> None:
        async with session_factory() as session:
            service = TopicService(TopicsRepository(session))
            topics = await service.list_tree()

        if not topics:
            await message.answer("No topics found.")
            return

        lines = []
        for topic in topics:
            indent = "  " * topic.level
            lines.append(f"{indent}- {topic.name} (`{topic.id}`)")
        await message.answer("Topics:\n" + "\n".join(lines))

    return router

