from aiogram import Router
from aiogram.filters import Filter, StateFilter
from aiogram.types import Message
from aiogram.utils.text_decorations import html_decoration
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.core.forward_parsing import (
    build_forward_description,
    build_forward_description_html,
    build_forward_notes,
    build_forward_title,
    extract_first_url,
)
from kb_bot.core.config import get_settings
from kb_bot.db.orm.topic import Topic
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import DuplicateEntryError, TopicConflictError, TopicNotFoundError
from kb_bot.services.embedding_runtime import build_embedding_service
from kb_bot.services.entry_service import CreateManualEntryPayload, EntryService
from kb_bot.services.topic_service import TopicService


class ForwardLikeFilter(Filter):
    async def __call__(self, message: Message) -> bool:
        return _is_forward_like_message(message)


def _is_forward_like_message(message: Message) -> bool:
    return any(
        (
            getattr(message, "forward_origin", None) is not None,
            getattr(message, "forward_from", None) is not None,
            getattr(message, "forward_from_chat", None) is not None,
            getattr(message, "forward_sender_name", None) is not None,
            bool(getattr(message, "is_automatic_forward", False)),
        )
    )


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
    settings = get_settings()

    @router.message(
        StateFilter("*"),
        ForwardLikeFilter(),
    )
    async def save_forward_handler(message: Message) -> None:
        text = message.text or message.caption or ""
        entities = [*(message.entities or []), *(message.caption_entities or [])]
        original_url = extract_first_url(text, entities=entities)
        title = build_forward_title(text)
        html_text = None
        if text and entities:
            # Prefer entity-based HTML: it uses Telegram-safe tags and keeps emphasis/links.
            html_text = html_decoration.unparse(text, entities)
        if not html_text:
            html_text = getattr(message, "html_text", None) or getattr(message, "caption_html", None)
        description = build_forward_description_html(html_text) or build_forward_description(text)
        # Keep original text in notes for note-mode dedup stability.
        # Without this, different forwards from the same source can collide.
        notes = build_forward_notes(text, _origin_repr(message))

        async with session_factory() as session:
            topics_repo = TopicsRepository(session)
            default_topic = await _resolve_forward_topic(topics_repo, session)
            if default_topic is None:
                await message.answer("Forward topic 'To read' is unavailable.")
                return

            service = EntryService(
                session=session,
                entries_repo=EntriesRepository(session),
                topics_repo=topics_repo,
                statuses_repo=StatusesRepository(session),
                embedding_service=build_embedding_service(session, settings),
            )
            payload = CreateManualEntryPayload(
                title=title,
                primary_topic_id=default_topic.id,
                original_url=original_url,
                description=description,
                notes=notes,
                status_code="TO_READ",
            )
            try:
                await service.create_manual(payload)
            except DuplicateEntryError:
                await _try_delete_forward_message(message)
                return
            except TopicNotFoundError:
                await message.answer("Topic validation failed.")
                return

        await _try_delete_forward_message(message)

    return router


async def _resolve_forward_topic(topics_repo: TopicsRepository, session) -> Topic | None:
    topic = await topics_repo.get_by_slug("to_read")
    if topic is not None:
        return topic

    topic = await topics_repo.get_by_name("To read")
    if topic is not None:
        return topic

    topic = await topics_repo.get_by_name("To Read")
    if topic is not None:
        return topic

    service = TopicService(topics_repo, session=session)
    try:
        await service.create_topic("To read")
    except TopicConflictError:
        pass

    topic = await topics_repo.get_by_slug("to_read")
    if topic is not None:
        return topic

    topic = await topics_repo.get_by_name("To read")
    if topic is not None:
        return topic

    return await topics_repo.get_by_name("To Read")


async def _try_delete_forward_message(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        # Best-effort cleanup: if Telegram refuses delete, keep flow silent anyway.
        return
