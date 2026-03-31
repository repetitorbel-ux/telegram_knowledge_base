from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker
import uuid

from kb_bot.core.topic_parsing import (
    parse_topic_add_command,
    parse_topic_delete_command,
    parse_topic_rename_command,
)
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import TopicConflictError, TopicNotFoundError
from kb_bot.services.topic_service import TopicService


def create_topic_manage_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("topic_add"))
    async def topic_add_handler(message: Message) -> None:
        command = parse_topic_add_command(message.text)
        if not command.name:
            await message.answer(
                "Usage:\n"
                "/topic_add <name>\n"
                "/topic_add <parent_uuid|root> <name>\n"
                "/topic_add parent=<parent_full_path_or_name> <name>\n"
                "/topic_add parent=\"Neural Networks / AI\" Codex\n"
                "/topic_add \"Neural Networks / AI\" -> Codex"
            )
            return

        async with session_factory() as session:
            topics_repo = TopicsRepository(session)
            service = TopicService(topics_repo, session=session)

            parent_topic_id = command.parent_topic_id
            if command.parent_selector:
                parent_topic_id, resolve_error = await _resolve_parent_topic_id(
                    topics_repo,
                    command.parent_selector,
                )
                if resolve_error:
                    await message.answer(resolve_error)
                    return

            try:
                topic = await service.create_topic(
                    name=command.name,
                    parent_topic_id=parent_topic_id,
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
            except Exception as exc:
                await message.answer(f"Topic add failed: {exc}")
                raise

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
            except Exception as exc:
                await message.answer(f"Topic rename failed: {exc}")
                raise

        await message.answer(f"Topic renamed: `{topic.id}` {topic.full_path}")

    @router.message(Command("topic_delete"))
    async def topic_delete_handler(message: Message) -> None:
        command = parse_topic_delete_command(message.text)
        if command.topic_id is None and not command.topic_selector:
            await message.answer(
                "Usage:\n"
                "/topic_delete <topic_uuid>\n"
                "/topic_delete <topic_full_path_or_name>\n"
                "/topic_delete \"Neural Networks / AI.Codex\""
            )
            return

        async with session_factory() as session:
            topics_repo = TopicsRepository(session)
            service = TopicService(topics_repo, session=session)

            topic_id = command.topic_id
            if topic_id is None and command.topic_selector:
                topic_id, resolve_error = await _resolve_topic_id(
                    topics_repo,
                    command.topic_selector,
                )
                if resolve_error:
                    await message.answer(resolve_error)
                    return

            if topic_id is None:
                await message.answer("Topic not found.")
                return

            try:
                deleted_count = await service.archive_topic_branch(topic_id)
            except TopicNotFoundError:
                await message.answer("Topic not found.")
                return
            except Exception as exc:
                await message.answer(f"Topic delete failed: {exc}")
                raise

        await message.answer(f"Topic archived: `{topic_id}`. Hidden topics: {deleted_count}")

    return router


async def _resolve_parent_topic_id(
    topics_repo: TopicsRepository,
    parent_selector: str,
) -> tuple[uuid.UUID | None, str | None]:
    return await _resolve_topic_id(topics_repo, parent_selector, not_found_message="Parent topic not found.")


async def _resolve_topic_id(
    topics_repo: TopicsRepository,
    selector_raw: str,
    *,
    not_found_message: str = "Topic not found.",
) -> tuple[uuid.UUID | None, str | None]:
    selector = selector_raw.strip()
    if not selector:
        return None, "Topic selector is empty."

    try:
        topic_id = uuid.UUID(selector)
    except ValueError:
        topic_id = None

    if topic_id is not None:
        topic = await topics_repo.get(topic_id)
        if topic is None:
            return None, not_found_message
        return topic.id, None

    topic_by_path = await topics_repo.get_by_full_path(selector)
    if topic_by_path is not None and topic_by_path.is_active:
        return topic_by_path.id, None

    by_name = await topics_repo.list_by_name(selector)
    if not by_name:
        return None, not_found_message
    if len(by_name) > 1:
        options = ", ".join(f"`{item.full_path}`" for item in by_name[:5])
        return (
            None,
            "Topic name is ambiguous. Use full path or UUID.\n"
            f"Candidates: {options}",
        )
    return by_name[0].id, None
