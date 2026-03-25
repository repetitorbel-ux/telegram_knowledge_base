from aiogram import F, Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.core.forward_parsing import build_forward_notes, build_forward_title, extract_first_url
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import DuplicateEntryError, TopicNotFoundError
from kb_bot.services.entry_service import CreateManualEntryPayload, EntryService


def _origin_repr(message: Message) -> str | None:
    origin = getattr(message, "forward_origin", None)
    if origin is not None:
        return origin.type if hasattr(origin, "type") else "forward_origin"
    if message.forward_from_chat:
        return f"chat:{message.forward_from_chat.id}"
    if message.forward_from:
        return f"user:{message.forward_from.id}"
    return None


def create_forward_save_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(F.forward_origin | F.forward_from | F.forward_from_chat)
    async def save_forward_handler(message: Message) -> None:
        text = message.text or message.caption or ""
        original_url = extract_first_url(text)
        title = build_forward_title(text)
        notes = build_forward_notes(text, _origin_repr(message))

        async with session_factory() as session:
            topics_repo = TopicsRepository(session)
            default_topic = await topics_repo.get_by_name("Useful Channels")
            if default_topic is None:
                await message.answer("Default topic 'Useful Channels' not found.")
                return

            service = EntryService(
                session=session,
                entries_repo=EntriesRepository(session),
                topics_repo=topics_repo,
                statuses_repo=StatusesRepository(session),
            )
            payload = CreateManualEntryPayload(
                title=title,
                primary_topic_id=default_topic.id,
                original_url=original_url,
                notes=notes,
            )
            try:
                entry = await service.create_manual(payload)
            except DuplicateEntryError:
                await message.answer("Forward already saved (duplicate).")
                return
            except TopicNotFoundError:
                await message.answer("Topic validation failed.")
                return

        await message.answer(
            f"Forward saved:\n"
            f"ID: `{entry.id}`\n"
            f"Title: {entry.title}\n"
            f"Topic: Useful Channels\n"
            f"URL: {entry.normalized_url or '-'}"
        )

    return router

