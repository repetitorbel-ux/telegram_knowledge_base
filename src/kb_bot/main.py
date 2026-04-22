import asyncio
import logging
import os
import socket
import sys
from pathlib import Path

import uvicorn

def _sanitize_sslkeylogfile() -> None:
    value = os.environ.get("SSLKEYLOGFILE")
    if not value:
        return
    if os.name == "nt":
        os.environ.pop("SSLKEYLOGFILE", None)
        return

    target = Path(value)
    parent = target.parent if target.parent != Path("") else Path(".")
    parent_writable = parent.exists() and os.access(parent, os.W_OK)
    file_writable = (target.exists() and os.access(target, os.W_OK)) or (
        not target.exists() and parent_writable
    )
    if not file_writable:
        os.environ.pop("SSLKEYLOGFILE", None)


_sanitize_sslkeylogfile()

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeChat, MenuButtonCommands

from kb_bot.bot.router import build_router
from kb_bot.bot.handlers.start import render_boot_text
from kb_bot.bot.ui.keyboards import build_main_menu_keyboard
from kb_bot.core.auth import AllowlistMiddleware
from kb_bot.core.config import get_settings
from kb_bot.core.logging import setup_logging
from kb_bot.db.engine import create_engine
from kb_bot.db.session import create_session_factory
from kb_bot.webhook_api.app import create_webhook_app

# Windows + some Python distributions (e.g., Miniconda) may fail with
# Proactor loop socketpair creation. Selector policy avoids that startup crash.
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


def _patch_windows_socketpair_if_needed() -> None:
    if sys.platform != "win32":
        return
    try:
        probe_a, probe_b = socket.socketpair()
        probe_a.close()
        probe_b.close()
        return
    except ConnectionError as exc:
        if "Unexpected peer connection" not in str(exc):
            raise

    def _win_socketpair(
        family: int = socket.AF_INET,
        sock_type: int = socket.SOCK_STREAM,
        proto: int = 0,
    ) -> tuple[socket.socket, socket.socket]:
        if family == socket.AF_INET:
            host = "127.0.0.1"
        elif family == socket.AF_INET6:
            host = "::1"
        else:
            raise ValueError("Only AF_INET/AF_INET6 are supported on Windows fallback.")

        listener = socket.socket(family, sock_type, proto)
        try:
            listener.bind((host, 0))
            listener.listen(1)

            client = socket.socket(family, sock_type, proto)
            try:
                client.setblocking(False)
                try:
                    client.connect(listener.getsockname())
                except (BlockingIOError, InterruptedError):
                    pass
                server, _ = listener.accept()
            except Exception:
                client.close()
                raise
            finally:
                client.setblocking(True)
        finally:
            listener.close()

        return server, client

    socket.socketpair = _win_socketpair


_patch_windows_socketpair_if_needed()


async def run_bot() -> None:
    settings = get_settings()
    setup_logging()
    logger = logging.getLogger(__name__)

    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)

    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher()
    dispatcher.message.middleware(AllowlistMiddleware(settings.telegram_allowed_user_id))
    dispatcher.include_router(build_router(session_factory))

    mode = settings.telegram_mode.strip().lower()
    logger.info("bot_starting", extra={"telegram_mode": mode})

    if mode == "webhook":
        webhook_url = _build_webhook_url(settings.telegram_webhook_base_url, settings.telegram_webhook_path)

        async def _on_startup() -> None:
            await _setup_chat_menu(bot, settings.telegram_allowed_user_id)
            try:
                await bot.send_message(
                    chat_id=settings.telegram_allowed_user_id,
                    text=render_boot_text(),
                    reply_markup=build_main_menu_keyboard(),
                    disable_notification=True,
                )
            except Exception:
                logger.exception("bot_restart_notification_failed")

            await bot.set_webhook(
                url=webhook_url,
                secret_token=settings.telegram_webhook_secret_token,
                drop_pending_updates=settings.telegram_webhook_drop_pending_updates,
            )
            logger.info("webhook_registered", extra={"webhook_url": webhook_url})

        async def _on_shutdown() -> None:
            try:
                await bot.delete_webhook(drop_pending_updates=False)
            finally:
                await engine.dispose()
                await bot.session.close()

        app = create_webhook_app(
            bot=bot,
            dispatcher=dispatcher,
            settings=settings,
            on_startup=_on_startup,
            on_shutdown=_on_shutdown,
        )
        uvicorn.run(
            app,
            host=settings.telegram_webhook_host,
            port=settings.telegram_webhook_port,
            log_level="info",
        )
        return

    if mode != "polling":
        raise ValueError("TELEGRAM_MODE must be either 'polling' or 'webhook'.")

    try:
        await _setup_chat_menu(bot, settings.telegram_allowed_user_id)
        try:
            await bot.send_message(
                chat_id=settings.telegram_allowed_user_id,
                text=render_boot_text(),
                reply_markup=build_main_menu_keyboard(),
                disable_notification=True,
            )
        except Exception:
            logger.exception("bot_restart_notification_failed")
        await bot.delete_webhook(drop_pending_updates=False)
        await dispatcher.start_polling(bot)
    finally:
        await engine.dispose()
        await bot.session.close()


def main() -> None:
    asyncio.run(run_bot())


def _build_webhook_url(base_url: str | None, path: str) -> str:
    if not base_url:
        raise ValueError("TELEGRAM_WEBHOOK_BASE_URL is required when TELEGRAM_MODE=webhook.")
    normalized_path = path if path.startswith("/") else f"/{path}"
    return f"{base_url.rstrip('/')}{normalized_path}"


def _build_main_menu_commands() -> list[BotCommand]:
    return [
        BotCommand(command="start", description="Главное меню"),
        BotCommand(command="add", description="Добавить запись"),
        BotCommand(command="search", description="Поиск"),
        BotCommand(command="list", description="Быстрые списки"),
        BotCommand(command="topics", description="Темы"),
        BotCommand(command="topic_move", description="Переместить тему"),
        BotCommand(command="entry", description="Открыть карточку записи"),
        BotCommand(command="entry_move", description="Перенести запись в тему"),
        BotCommand(command="entry_edit", description="Редактировать поля записи"),
        BotCommand(command="entry_delete", description="Удалить запись по ID"),
        BotCommand(command="status", description="Сменить статус"),
        BotCommand(command="stats", description="Статистика"),
        BotCommand(command="backups", description="Резервные копии"),
    ]


async def _setup_chat_menu(bot: Bot, chat_id: int) -> None:
    logger = logging.getLogger(__name__)
    try:
        await bot.set_my_commands(
            _build_main_menu_commands(),
            scope=BotCommandScopeChat(chat_id=chat_id),
        )
        await bot.set_chat_menu_button(
            chat_id=chat_id,
            menu_button=MenuButtonCommands(),
        )
    except Exception:
        logger.exception("chat_menu_setup_failed")


if __name__ == "__main__":
    main()
