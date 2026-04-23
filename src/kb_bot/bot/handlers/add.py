import uuid

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.bot.fsm.states import AddEntryStates
from kb_bot.bot.handlers.add_parsing import parse_content_input
from kb_bot.bot.ui.callbacks import ADD_TOPIC_PREFIX
from kb_bot.bot.ui.keyboards import (
    build_add_topic_picker_keyboard,
    build_flow_navigation_keyboard,
    build_main_menu_keyboard,
)
from kb_bot.core.config import get_settings
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.domain.errors import DuplicateEntryError, TopicNotFoundError
from kb_bot.services.embedding_runtime import build_embedding_service
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
        await message.answer(
            "Send URL (http/https) or plain note text.",
            reply_markup=build_flow_navigation_keyboard(),
        )

    @router.message(AddEntryStates.waiting_content, F.text & ~F.text.startswith("/"))
    async def add_content(message: Message, state: FSMContext) -> None:
        original_url, notes = parse_content_input(message.text or "")
        await state.update_data(original_url=original_url, notes=notes)
        await state.set_state(AddEntryStates.waiting_title)
        await message.answer("Now send title.", reply_markup=build_flow_navigation_keyboard())

    @router.message(AddEntryStates.waiting_title, F.text & ~F.text.startswith("/"))
    async def add_title(message: Message, state: FSMContext) -> None:
        title = (message.text or "").strip()
        if not title:
            await message.answer(
                "Title cannot be empty. Send title again.",
                reply_markup=build_flow_navigation_keyboard(),
            )
            return

        await state.update_data(title=title)
        async with session_factory() as session:
            topics = await TopicsRepository(session).list_tree()
        if not topics:
            await message.answer("No topics available. Seed topics first.")
            await state.clear()
            return

        await state.set_state(AddEntryStates.waiting_topic)
        await message.answer(
            "Choose topic with buttons below.\n\n"
            "You can still send topic UUID manually if needed.",
            reply_markup=build_add_topic_picker_keyboard(topics),
        )

    @router.message(AddEntryStates.waiting_topic, F.text & ~F.text.startswith("/"))
    async def add_topic(message: Message, state: FSMContext) -> None:
        try:
            topic_id = uuid.UUID((message.text or "").strip())
        except ValueError:
            await message.answer(
                "Invalid UUID. Choose topic with buttons or send topic UUID exactly.",
                reply_markup=await _build_topic_picker_from_db(session_factory),
            )
            return

        response = await _create_entry_from_state(session_factory, state, topic_id)
        await message.answer(response, reply_markup=_result_keyboard_for_response(response))

    @router.callback_query(
        AddEntryStates.waiting_topic,
        F.data.startswith(ADD_TOPIC_PREFIX),
    )
    async def add_topic_callback(callback: CallbackQuery, state: FSMContext) -> None:
        await callback.answer()
        raw_value = (callback.data or "")[len(ADD_TOPIC_PREFIX) :]
        try:
            topic_id = uuid.UUID(raw_value)
        except ValueError:
            if callback.message is not None:
                await callback.message.answer(
                    "Topic selection is invalid. Try again.",
                    reply_markup=await _build_topic_picker_from_db(session_factory),
                )
            return

        response = await _create_entry_from_state(session_factory, state, topic_id)
        if callback.message is not None:
            await callback.message.answer(response, reply_markup=_result_keyboard_for_response(response))

    @router.message(AddEntryStates.waiting_content, F.text.startswith("/"))
    @router.message(AddEntryStates.waiting_title, F.text.startswith("/"))
    @router.message(AddEntryStates.waiting_topic, F.text.startswith("/"))
    async def add_state_command_hint(message: Message) -> None:
        await message.answer("You are in /add flow. Send expected value or /cancel.")

    return router


async def _build_topic_picker_from_db(session_factory: async_sessionmaker):
    async with session_factory() as session:
        topics = await TopicsRepository(session).list_tree()
    return build_add_topic_picker_keyboard(topics)


async def _create_entry_from_state(
    session_factory: async_sessionmaker,
    state: FSMContext,
    topic_id: uuid.UUID,
) -> str:
    data = await state.get_data()
    settings = get_settings()
    async with session_factory() as session:
        service = EntryService(
            session=session,
            entries_repo=EntriesRepository(session),
            topics_repo=TopicsRepository(session),
            statuses_repo=StatusesRepository(session),
            embedding_service=build_embedding_service(session, settings),
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
            await state.clear()
            return "Duplicate detected. Entry was not created."
        except TopicNotFoundError:
            return "Topic not found. Try again."
        except ValueError as exc:
            return f"Validation error: {exc}"

    await state.clear()
    return (
        f"Saved entry:\n"
        f"ID: `{entry.id}`\n"
        f"Title: {entry.title}\n"
        f"Status: {entry.status_name}\n"
        f"URL: {entry.normalized_url or '-'}"
    )


def _result_keyboard_for_response(response: str):
    if response.startswith("Saved entry:") or response.startswith("Duplicate detected."):
        return build_main_menu_keyboard()
    return build_flow_navigation_keyboard()
