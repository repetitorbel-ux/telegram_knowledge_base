import asyncio
import logging
import os
from pathlib import Path

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

from kb_bot.bot.router import build_router
from kb_bot.core.auth import AllowlistMiddleware
from kb_bot.core.config import get_settings
from kb_bot.core.logging import setup_logging
from kb_bot.db.engine import create_engine
from kb_bot.db.session import create_session_factory


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

    logger.info("bot_starting")
    try:
        await dispatcher.start_polling(bot)
    finally:
        await engine.dispose()
        await bot.session.close()


def main() -> None:
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
