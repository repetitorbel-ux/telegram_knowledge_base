"""Semantic search MCP tool — only active when SEMANTIC_SEARCH_ENABLED=true."""
from __future__ import annotations

import json
import os


async def semantic_search(query: str, limit: int = 10) -> str:
    """Search entries using semantic similarity (vector embeddings).

    This tool is only available when SEMANTIC_SEARCH_ENABLED=true and a
    local Ollama or OpenAI embedding provider is configured. Use this
    when you want to find conceptually related entries even if they don't
    share exact keywords with the query. For precise keyword lookup, use
    search_entries instead.

    Args:
        query: Natural language query (e.g. "machine learning for text classification").
        limit: Number of results to return (1-20). Default 10.

    Returns JSON with results list: id, title, status, topic, score, saved_date.
    Returns an error if semantic search is disabled.
    """
    if os.environ.get("SEMANTIC_SEARCH_ENABLED", "false").lower() != "true":
        return json.dumps({
            "error": "Semantic search is disabled. Set SEMANTIC_SEARCH_ENABLED=true and configure an embedding provider."
        })

    if not query.strip():
        return json.dumps({"error": "query must not be empty"})

    # Import lazily — only if semantic search is enabled
    from kb_bot.mcp_server.db_client import get_session
    from kb_bot.db.repositories.entries import EntriesRepository
    from kb_bot.db.repositories.embeddings import EmbeddingsRepository
    from kb_bot.services.search_service import SearchService
    from kb_bot.services.embedding_runtime import build_embedding_provider
    from kb_bot.core.config import get_settings

    settings = get_settings()

    async with get_session() as session:
        provider = build_embedding_provider(settings)
        service = SearchService(
            entries_repo=EntriesRepository(session),
            embeddings_repo=EmbeddingsRepository(session),
            embedding_provider=provider,
            settings=settings,
        )
        results = await service.search(
            query=query.strip(),
            limit=min(limit, 20),
            semantic=True,
        )

    items = [
        {
            "id": str(r.entry_id if hasattr(r, "entry_id") else r.id),
            "title": getattr(r, "title", ""),
            "status": getattr(r, "status_name", ""),
            "topic": getattr(r, "topic_name", ""),
            "saved_date": r.saved_date.isoformat() if getattr(r, "saved_date", None) else None,
        }
        for r in results
    ]
    return json.dumps({
        "query": query,
        "results": items,
        "count": len(items),
    }, ensure_ascii=False)
