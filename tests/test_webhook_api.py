import os
from typing import Any

from fastapi.testclient import TestClient

os.environ.pop("SSLKEYLOGFILE", None)

from kb_bot.core.config import Settings
from kb_bot.webhook_api.app import create_webhook_app


class _FakeDispatcher:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def feed_update(self, bot, update) -> None:
        self.calls.append({"bot": bot, "update": update})


def _make_settings(secret_token: str | None = None) -> Settings:
    return Settings.model_construct(
        telegram_bot_token="test-token",
        telegram_allowed_user_id=1,
        telegram_mode="webhook",
        telegram_webhook_base_url="https://example.test",
        telegram_webhook_path="/telegram/webhook",
        telegram_webhook_secret_token=secret_token,
        telegram_webhook_host="127.0.0.1",
        telegram_webhook_port=8081,
        telegram_webhook_drop_pending_updates=False,
        database_url="postgresql+asyncpg://u:p@127.0.0.1:5432/db",
        backup_dir="backups",
        pg_dump_bin="pg_dump",
        pg_restore_bin="pg_restore",
        restore_timeout_sec=1800,
        admin_api_enabled=False,
        admin_api_host="127.0.0.1",
        admin_api_port=8080,
        admin_api_token=None,
        admin_export_dir="exports",
    )


def test_webhook_rejects_invalid_secret_token() -> None:
    dispatcher = _FakeDispatcher()
    app = create_webhook_app(
        bot=object(),
        dispatcher=dispatcher,  # type: ignore[arg-type]
        settings=_make_settings(secret_token="expected"),
    )

    with TestClient(app) as client:
        response = client.post("/telegram/webhook", json={"update_id": 1})

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Telegram secret token."
    assert dispatcher.calls == []


def test_webhook_dispatches_update() -> None:
    dispatcher = _FakeDispatcher()
    app = create_webhook_app(
        bot=object(),
        dispatcher=dispatcher,  # type: ignore[arg-type]
        settings=_make_settings(secret_token="expected"),
    )

    with TestClient(app) as client:
        response = client.post(
            "/telegram/webhook",
            headers={"X-Telegram-Bot-Api-Secret-Token": "expected"},
            json={"update_id": 123456},
        )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    assert len(dispatcher.calls) == 1
    assert dispatcher.calls[0]["update"].update_id == 123456
