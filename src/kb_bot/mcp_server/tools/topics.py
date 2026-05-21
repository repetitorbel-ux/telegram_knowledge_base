"""Topic-related MCP tools: list_topics, get_topic_entries."""
from __future__ import annotations

import json
import uuid

from sqlalchemy import func, select

from kb_bot.db.orm.entry import KnowledgeEntry
from kb_bot.db.orm.topic import Topic
from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.db.repositories.topics import TopicsRepository
from kb_bot.mcp_server.db_client import get_session


async def list_topics() -> str:
    """List all active topics in the knowledge base as a tree.

    Returns a flat list ordered by full_path, each item has: id, name,
    full_path, level, entry_count. Use this to discover topic IDs for
    use with list_entries or get_topic_entries. level=0 means root topic.
    """
    async with get_session() as session:
        repo = TopicsRepository(session)
        topics = await repo.list_tree()

        # count entries per topic (direct only)
        count_stmt = (
            select(KnowledgeEntry.primary_topic_id, func.count(KnowledgeEntry.id))
            .group_by(KnowledgeEntry.primary_topic_id)
        )
        count_result = await session.execute(count_stmt)
        counts = {str(row[0]): row[1] for row in count_result.all()}

    results = [
        {
            "id": str(t.id),
            "name": t.name,
            "full_path": t.full_path,
            "level": t.level,
            "entry_count": counts.get(str(t.id), 0),
        }
        for t in topics
    ]
    return json.dumps({"topics": results, "count": len(results)}, ensure_ascii=False)


async def get_topic_entries(
    topic_id: str | None = None,
    topic_path: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """Get entries belonging to a topic and all its subtopics.

    Provide either topic_id (UUID) or topic_path (e.g. 'programming.python').
    Returns entries from the topic AND all nested subtopics.
    Each entry has: id, title, status, url, saved_date.

    Args:
        topic_id: UUID of the topic. Get from list_topics.
        topic_path: Full dotted path of the topic (alternative to topic_id).
        limit: Max results (1-50). Default 20.
        offset: Pagination offset.
    """
    if not topic_id and not topic_path:
        return json.dumps({"error": "Provide either topic_id or topic_path"})

    async with get_session() as session:
        repo = TopicsRepository(session)
        topic = None

        if topic_id:
            try:
                tid = uuid.UUID(topic_id)
                topic = await repo.get(tid)
            except ValueError:
                return json.dumps({"error": f"Invalid topic_id UUID: {topic_id}"})
        elif topic_path:
            topic = await repo.get_by_full_path(topic_path)

        if topic is None:
            return json.dumps({"error": "Topic not found"})

        entries_repo = EntriesRepository(session)
        rows = await entries_repo.list_entries(
            topic_id=topic.id,
            limit=min(limit, 50),
            offset=offset,
        )

    results = [
        {
            "id": str(entry.id),
            "title": entry.title or "",
            "status": status_name,
            "url": entry.original_url or "",
            "saved_date": entry.saved_date.isoformat() if entry.saved_date else None,
        }
        for entry, status_name, _topic_name in rows
    ]
    return json.dumps({
        "topic": {"id": str(topic.id), "name": topic.name, "full_path": topic.full_path},
        "results": results,
        "count": len(results),
        "offset": offset,
        "has_more": len(results) == limit,
    }, ensure_ascii=False)
