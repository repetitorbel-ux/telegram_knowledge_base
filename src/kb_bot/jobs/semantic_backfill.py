from __future__ import annotations

import argparse
import asyncio
import logging
import os
import socket
import sys

from kb_bot.core.config import get_settings
from kb_bot.core.logging import setup_logging
from kb_bot.db.engine import create_engine
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.session import create_session_factory
from kb_bot.services.embedding_runtime import build_embedding_service


async def run_backfill(batch_size: int, max_entries: int | None) -> tuple[int, int]:
    settings = get_settings()
    engine = create_engine(settings.database_url)
    session_factory = create_session_factory(engine)
    logger = logging.getLogger(__name__)

    processed = 0
    updated = 0
    offset = 0

    try:
        while True:
            if max_entries is not None and processed >= max_entries:
                break

            current_batch_limit = batch_size
            if max_entries is not None:
                current_batch_limit = min(batch_size, max_entries - processed)
                if current_batch_limit <= 0:
                    break

            async with session_factory() as session:
                entries_repo = EntriesRepository(session)
                rows = await entries_repo.list_for_embedding(limit=current_batch_limit, offset=offset)
                if not rows:
                    break

                embedding_service = build_embedding_service(session, settings)
                if embedding_service is None:
                    logger.warning("semantic_backfill_skipped_provider_unavailable")
                    break

                for entry in rows:
                    entry_id = str(entry.id)
                    try:
                        changed = await embedding_service.upsert_for_entry(entry)
                    except Exception as exc:
                        logger.warning(
                            "semantic_backfill_entry_failed",
                            extra={
                                "entry_id": entry_id,
                                "error_type": exc.__class__.__name__,
                                "error": str(exc),
                            },
                            exc_info=True,
                        )
                        processed += 1
                        continue
                    processed += 1
                    if changed:
                        updated += 1

                offset += len(rows)

        return processed, updated
    finally:
        await engine.dispose()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill semantic embeddings for knowledge entries.")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size for entry scanning.")
    parser.add_argument("--max-entries", type=int, default=None, help="Optional max entries to process.")
    return parser.parse_args()


def _install_windows_socketpair_fallback() -> None:
    if not sys.platform.startswith("win"):
        return
    if hasattr(socket, "_kb_socketpair_patched"):
        return

    def _safe_socketpair() -> tuple[socket.socket, socket.socket]:
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect(listener.getsockname())
            server, _addr = listener.accept()
            return server, client
        except Exception:
            client.close()
            raise
        finally:
            listener.close()

    try:
        socket.socketpair()
    except Exception:
        socket.socketpair = _safe_socketpair  # type: ignore[assignment]
        setattr(socket, "_kb_socketpair_patched", True)


def _disable_unwritable_ssl_keylogfile() -> None:
    keylog_path = os.environ.get("SSLKEYLOGFILE")
    if not keylog_path:
        return
    try:
        with open(keylog_path, "a", encoding="utf-8"):
            pass
    except OSError:
        logging.getLogger(__name__).warning(
            "semantic_backfill_disabled_unwritable_sslkeylogfile",
            extra={"sslkeylogfile": keylog_path},
        )
        os.environ.pop("SSLKEYLOGFILE", None)


def main() -> None:
    args = _parse_args()
    setup_logging()
    _disable_unwritable_ssl_keylogfile()
    _install_windows_socketpair_fallback()
    if sys.platform.startswith("win") and hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        # On some Windows/Conda setups Proactor loop fails on socketpair() during loop init.
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    processed, updated = asyncio.run(run_backfill(batch_size=args.batch_size, max_entries=args.max_entries))
    print(f"semantic_backfill_processed={processed}")
    print(f"semantic_backfill_updated={updated}")


if __name__ == "__main__":
    main()
