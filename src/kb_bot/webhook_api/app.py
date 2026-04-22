from __future__ import annotations

from collections.abc import Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request, status

from kb_bot.core.config import Settings


def create_webhook_app(
    bot: Bot,
    dispatcher: Dispatcher,
    settings: Settings,
    on_startup: Callable[[], Awaitable[None]] | None = None,
    on_shutdown: Callable[[], Awaitable[None]] | None = None,
) -> FastAPI:
    webhook_path = settings.telegram_webhook_path.strip()
    if not webhook_path.startswith("/"):
        webhook_path = f"/{webhook_path}"

    @asynccontextmanager
    async def _lifespan(_: FastAPI):
        if on_startup is not None:
            await on_startup()
        yield
        if on_shutdown is not None:
            await on_shutdown()

    app = FastAPI(title="telegram-kb-bot webhook", version="1.0", lifespan=_lifespan)

    @app.post(webhook_path)
    async def telegram_webhook(
        request: Request,
        x_telegram_bot_api_secret_token: str | None = Header(
            default=None,
            alias="X-Telegram-Bot-Api-Secret-Token",
        ),
    ) -> dict[str, Any]:
        expected_secret = settings.telegram_webhook_secret_token
        if expected_secret and x_telegram_bot_api_secret_token != expected_secret:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Telegram secret token.",
            )

        payload = await request.json()
        update = Update.model_validate(payload, context={"bot": bot})
        await dispatcher.feed_update(bot, update)
        return {"ok": True}

    return app

