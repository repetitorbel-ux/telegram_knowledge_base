import uuid

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.core.collection_parsing import parse_collection_add_name, parse_collection_run_id
from kb_bot.core.list_parsing import ListFilters, parse_list_command
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.saved_views import SavedViewsRepository
from kb_bot.services.collection_service import CollectionService
from kb_bot.services.query_service import QueryService


def create_collections_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("collection_add"))
    async def collection_add_handler(message: Message) -> None:
        name = parse_collection_add_name(message.text)
        if not name:
            await message.answer(
                "Usage: /collection_add <name> [status=New] [topic=<uuid>] [limit=20]"
            )
            return

        parsed = parse_list_command(message.text)
        filters = ListFilters(
            status_name=parsed.status_name,
            topic_id=parsed.topic_id,
            limit=parsed.limit,
        )
        async with session_factory() as session:
            service = CollectionService(SavedViewsRepository(session), session)
            try:
                saved = await service.create_saved_view(name=name, filters=filters)
            except ValueError as exc:
                await message.answer(f"Collection error: {exc}")
                return

        await message.answer(f"Collection saved: `{saved.id}` {saved.name}")

    @router.message(Command("collections"))
    async def collections_handler(message: Message) -> None:
        async with session_factory() as session:
            service = CollectionService(SavedViewsRepository(session), session)
            rows = await service.list_saved_views()

        if not rows:
            await message.answer("No saved collections.")
            return

        lines = []
        for row in rows:
            lines.append(f"- `{row.id}` | {row.name} | {row.filter_snapshot}")
        await message.answer("Saved collections:\n" + "\n".join(lines))

    @router.message(Command("collection_run"))
    async def collection_run_handler(message: Message) -> None:
        view_id = parse_collection_run_id(message.text)
        if view_id is None:
            await message.answer("Usage: /collection_run <collection_uuid>")
            return

        async with session_factory() as session:
            collection_service = CollectionService(SavedViewsRepository(session), session)
            view = await collection_service.get_saved_view(view_id)
            if view is None:
                await message.answer("Collection not found.")
                return

            snapshot = view.filter_snapshot
            topic_id = snapshot.get("topic_id")
            parsed_topic_id = None
            if topic_id:
                try:
                    parsed_topic_id = uuid.UUID(topic_id)
                except ValueError:
                    parsed_topic_id = None

            query_service = QueryService(EntriesRepository(session))
            entries = await query_service.list_entries(
                status_name=snapshot.get("status_name"),
                topic_id=parsed_topic_id,
                limit=int(snapshot.get("limit", 20)),
            )

        if not entries:
            await message.answer(f"Collection '{view.name}' has no entries.")
            return

        lines = [f"Collection: {view.name}"]
        for item in entries:
            lines.append(f"- `{item.entry_id}` | {item.title} [{item.status_name}] ({item.topic_name})")
        await message.answer("\n".join(lines))

    return router

