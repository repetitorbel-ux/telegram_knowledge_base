import os
from pathlib import Path
from typing import Any, Awaitable, Callable


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

try:
    from aiogram import BaseMiddleware
    from aiogram.types import Message, TelegramObject
except (ModuleNotFoundError, PermissionError):  # pragma: no cover
    class BaseMiddleware:  # type: ignore[override]
        pass

    class TelegramObject:  # type: ignore[override]
        pass

    class Message:  # type: ignore[override]
        async def answer(self, _: str) -> None:
            return None


class AllowlistMiddleware(BaseMiddleware):
    def __init__(self, allowed_user_id: int) -> None:
        super().__init__()
        self.allowed_user_id = allowed_user_id

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from_user = getattr(event, "from_user", None)
        if from_user is None or from_user.id != self.allowed_user_id:
            if isinstance(event, Message):
                await event.answer("Access denied.")
            return None
        return await handler(event, data)


class AuthGuard:
    def __init__(self, allowed_user_id: int) -> None:
        self.allowed_user_id = allowed_user_id

    def is_allowed(self, user_id: int) -> bool:
        return user_id == self.allowed_user_id
