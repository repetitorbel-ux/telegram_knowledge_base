"""Stats MCP tool: get_stats."""
from __future__ import annotations

import json

from kb_bot.mcp_server.db_client import get_session
from kb_bot.services.stats_service import StatsService


async def get_stats() -> str:
    """Get a summary of the knowledge base: total entries, counts by status,
    counts by topic, inbox size, backlog, and verified coverage ratio.

    Use this to understand the overall state of the knowledge base before
    deciding what to work on. No arguments required.

    Returns: total_entries, by_status (dict), by_topic (dict),
             inbox_size (New count), backlog (To Read count),
             verified_coverage (0.0-1.0), duplicates_prevented.
    """
    async with get_session() as session:
        service = StatsService(session)
        stats = await service.get_stats()
    return json.dumps(stats, ensure_ascii=False)
