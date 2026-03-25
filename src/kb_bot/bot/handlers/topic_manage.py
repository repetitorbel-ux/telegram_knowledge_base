from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.core.topic_parsing import parse_topic_add_command, parse_topic_rename_command
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import TopicConflictError, TopicNotFoundError
from kb_bot.services.topic_service import TopicService


def create_topic_manage_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("topic_add"))
    async def topic_add_handler(message: Message) -> None:
        command = parse_topic_add_command(message.text)
        if not command.name:
            await message.answer("Usage: /topic_add <name> OR /topic_add <parent_uuid|root> <name>")
            return

        async with session_factory() as session:
            service = TopicService(TopicsRepository(session), session=session)
            try:
                topic = await service.create_topic(
                    name=command.name,
                    parent_topic_id=command.parent_topic_id,
                )
            except TopicNotFoundError:
                await message.answer("Parent topic not found.")
                return
            except TopicConflictError:
                await message.answer("Topic with same path already exists.")
                return
            except ValueError as exc:
                await message.answer(f"Validation error: {exc}")
                return

        await message.answer(f"Topic created: `{topic.id}` {topic.full_path}")

    @router.message(Command("topic_rename"))
    async def topic_rename_handler(message: Message) -> None:
        command = parse_topic_rename_command(message.text)
        if command.topic_id is None or not command.new_name:
            await message.answer("Usage: /topic_rename <topic_uuid> <new_name>")
            return

        async with session_factory() as session:
            service = TopicService(TopicsRepository(session), session=session)
            try:
                topic = await service.rename_topic(command.topic_id, command.new_name)
            except TopicNotFoundError:
                await message.answer("Topic not found.")
                return
            except TopicConflictError:
                await message.answer("Target topic path already exists.")
                return

        await message.answer(f"Topic renamed: `{topic.id}` {topic.full_path}")

    return router

