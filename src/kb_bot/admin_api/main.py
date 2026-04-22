from __future__ import annotations

import uvicorn

from kb_bot.admin_api.app import create_admin_app
from kb_bot.core.config import get_settings


def main() -> None:
    settings = get_settings()
    app = create_admin_app(settings=settings)
    uvicorn.run(
        app,
        host=settings.admin_api_host,
        port=settings.admin_api_port,
        log_level="info",
    )


if __name__ == "__main__":
    main()

