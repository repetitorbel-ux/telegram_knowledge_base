import io

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.core.import_parsing import detect_import_format
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.jobs import JobsRepository
from kb_bot.db.repositories.statuses import StatusesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.services.import_service import ImportService


def create_import_router(session_factory: async_sessionmaker) -> Router:
    router = Router()

    @router.message(Command("import"))
    async def import_help_handler(message: Message) -> None:
        await message.answer(
            "Send CSV or JSON document with caption /import.\n"
            "Supported columns: title, original_url, notes, topic_id"
        )

    @router.message(F.document, F.caption.startswith("/import"))
    async def import_document_handler(message: Message) -> None:
        if message.document is None:
            await message.answer("No document found.")
            return

        filename = message.document.file_name or "import.dat"
        source_format = detect_import_format(filename)
        if source_format is None:
            await message.answer("Unsupported format. Use .csv or .json file.")
            return

        file = await message.bot.get_file(message.document.file_id)
        buffer = io.BytesIO()
        await message.bot.download_file(file.file_path, destination=buffer)
        payload = buffer.getvalue()

        async with session_factory() as session:
            service = ImportService(
                session=session,
                jobs_repo=JobsRepository(session),
                entries_repo=EntriesRepository(session),
                topics_repo=TopicsRepository(session),
                statuses_repo=StatusesRepository(session),
            )
            result = await service.import_rows(filename, source_format, payload)

        await message.answer(
            f"Import completed:\n"
            f"Job: `{result.job_id}`\n"
            f"Total: {result.total_records}\n"
            f"Imported: {result.imported_records}\n"
            f"Duplicates: {result.duplicate_records}\n"
            f"Errors: {result.error_records}"
        )

    return router

