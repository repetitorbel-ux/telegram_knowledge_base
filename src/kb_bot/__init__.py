from __future__ import annotations

import os
from pathlib import Path

__all__ = ["__version__"]

__version__ = "0.1.0"


def _sanitize_sslkeylogfile() -> None:
    """
    Clear SSLKEYLOGFILE only when it points to a non-writable location.

    Some local environments export SSLKEYLOGFILE globally (for TLS debugging).
    If the configured path is not writable, aiohttp import fails early with
    PermissionError while creating default SSL context.
    """

    value = os.environ.get("SSLKEYLOGFILE")
    if not value:
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
