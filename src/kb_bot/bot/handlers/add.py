import uuid

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.bot.fsm.states import AddEntryStates
from kb_bot.bot.handlers.add_parsing import parse_content_input
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import DuplicateEntryError, TopicNotFoundError
from kb_bot.services.entry_service import CreateManualEntryPayload, EntryService


def create_add_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("cancel"))
    async def add_cancel(message: Message, state: FSMContext) -> None:
        if await state.get_state() is None:
            await message.answer("No active flow to cancel.")
            return
        await state.clear()
        await message.answer("Current flow cancelled.")

    @router.message(Command("add"))
    async def add_start(message: Message, state: FSMContext) -> None:
        await state.set_state(AddEntryStates.waiting_content)
        await message.answer("Send URL (http/https) or plain note text.")

    @router.message(AddEntryStates.waiting_content, F.text & ~F.text.startswith("/"))
    async def add_content(message: Message, state: FSMContext) -> None:
        original_url, notes = parse_content_input(message.text or "")
        await state.update_data(original_url=original_url, notes=notes)
        await state.set_state(AddEntryStates.waiting_title)
        await message.answer("Now send title.")

    @router.message(AddEntryStates.waiting_title, F.text & ~F.text.startswith("/"))
    async def add_title(message: Message, state: FSMContext) -> None:
        title = (message.text or "").strip()
        if not title:
            await message.answer("Title cannot be empty. Send title again.")
            return

        await state.update_data(title=title)
        async with session_factory() as session:
            topics = await TopicsRepository(session).list_tree()
        if not topics:
            await message.answer("No topics available. Seed topics first.")
            await state.clear()
            return

        lines = [f"- {topic.name}: `{topic.id}`" for topic in topics]
        await state.set_state(AddEntryStates.waiting_topic)
        await message.answer("Send topic UUID:\n" + "\n".join(lines))

    @router.message(AddEntryStates.waiting_topic, F.text & ~F.text.startswith("/"))
    async def add_topic(message: Message, state: FSMContext) -> None:
        try:
            topic_id = uuid.UUID((message.text or "").strip())
        except ValueError:
            await message.answer("Invalid UUID. Send topic UUID exactly.")
            return

        data = await state.get_data()
        async with session_factory() as session:
            service = EntryService(
                session=session,
                entries_repo=EntriesRepository(session),
                topics_repo=TopicsRepository(session),
                statuses_repo=StatusesRepository(session),
            )
            payload = CreateManualEntryPayload(
                title=data.get("title", ""),
                primary_topic_id=topic_id,
                original_url=data.get("original_url"),
                notes=data.get("notes"),
            )
            try:
                entry = await service.create_manual(payload)
            except DuplicateEntryError:
                await message.answer("Duplicate detected. Entry was not created.")
                await state.clear()
                return
            except TopicNotFoundError:
                await message.answer("Topic not found. Try again.")
                return
            except ValueError as exc:
                await message.answer(f"Validation error: {exc}")
                return

        await state.clear()
        await message.answer(
            f"Saved entry:\n"
            f"ID: `{entry.id}`\n"
            f"Title: {entry.title}\n"
            f"Status: {entry.status_name}\n"
            f"URL: {entry.normalized_url or '-'}"
        )

    @router.message(AddEntryStates.waiting_content, F.text.startswith("/"))
    @router.message(AddEntryStates.waiting_title, F.text.startswith("/"))
    @router.message(AddEntryStates.waiting_topic, F.text.startswith("/"))
    async def add_state_command_hint(message: Message) -> None:
        await message.answer("You are in /add flow. Send expected value or /cancel.")

    return router
