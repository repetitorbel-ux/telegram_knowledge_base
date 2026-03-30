from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from kb_bot.bot.ui.keyboards import build_backups_keyboard
from kb_bot.core.backup_parsing import parse_restore_args, parse_single_uuid_arg
from kb_bot.core.config import get_settings
from kb_bot.db.repositories.backups import BackupsRepository
from kb_bot.services.backup_service import BackupService


def create_backup_restore_router(session_factory: async_sessionmaker) -> Router:
    router = Router()
    settings = get_settings()

    @router.message(Command("backup"))
    async def backup_handler(message: Message) -> None:
        async with session_factory() as session:
            service = BackupService(BackupsRepository(session), session)
            try:
                result = await service.create_backup(
                    database_url=settings.database_url,
                    backup_dir=settings.backup_dir,
                    pg_dump_bin=settings.pg_dump_bin,
                )
            except Exception as exc:
                await message.answer(f"Backup failed: {exc}")
                return

        await message.answer(
            f"Backup created:\nID: `{result.backup_id}`\nFile: {result.filename}\nSHA256: {result.checksum}",
            reply_markup=build_backups_keyboard(),
        )

    @router.message(Command("backups"))
    async def backups_handler(message: Message) -> None:
        async with session_factory() as session:
            service = BackupService(BackupsRepository(session), session)
            rows = await service.list_backups()
        if not rows:
            await message.answer("No backups found.")
            return

        lines = []
        for row in rows:
            lines.append(f"- `{row.id}` | {row.filename} | tested={row.restore_tested_at or '-'}")
        await message.answer("Backups:\n" + "\n".join(lines), reply_markup=build_backups_keyboard())

    @router.message(Command("restore_token"))
    async def restore_token_handler(message: Message) -> None:
        backup_id = parse_single_uuid_arg(message.text)
        if backup_id is None:
            await message.answer("Usage: /restore_token <backup_uuid>")
            return
        async with session_factory() as session:
            service = BackupService(BackupsRepository(session), session)
            token = await service.issue_restore_token(str(backup_id))
        await message.answer(f"Restore token (valid 10 min): `{token}`")

    @router.message(Command("restore"))
    async def restore_handler(message: Message) -> None:
        backup_id, token = parse_restore_args(message.text)
        if backup_id is None or token is None:
            await message.answer("Usage: /restore <backup_uuid> <token>")
            return

        async with session_factory() as session:
            service = BackupService(BackupsRepository(session), session)
            try:
                await service.restore_backup(
                    backup_id=str(backup_id),
                    token=token,
                    database_url=settings.database_url,
                    pg_restore_bin=settings.pg_restore_bin,
                )
            except Exception as exc:
                await message.answer(f"Restore failed: {exc}")
                return

        await message.answer("Restore completed.")

    return router
