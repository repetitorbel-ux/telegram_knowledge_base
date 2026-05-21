"""Entry-related MCP tools: search, list, get, related."""
from __future__ import annotations

import json
import uuid

from kb_bot.db.repositories.entries import EntriesRepository
from kb_bot.mcp_server.db_client import get_session
from kb_bot.services.search_service import SearchService


async def search_entries(query: str, limit: int = 10, offset: int = 0) -> str:
    """Search entries by keyword across title, notes and description.

    Returns a JSON list of matching entries. Each item has: id, title,
    status, url, saved_date. Use this when you know specific keywords or
    phrases. For broad conceptual queries, prefer semantic_search (if
    enabled). Pass offset to paginate.
    """
    if not query.strip():
        return json.dumps({"error": "query must not be empty"})
    async with get_session() as session:
        repo = EntriesRepository(session)
        rows = await repo.search(query.strip(), limit=limit, offset=offset)
    results = [
        {
            "id": str(entry.id),
            "title": entry.title or "",
            "status": status_name,
            "url": entry.original_url or "",
            "saved_date": entry.saved_date.isoformat() if entry.saved_date else None,
        }
        for entry, status_name in rows
    ]
    return json.dumps({
        "results": results,
        "count": len(results),
        "offset": offset,
        "has_more": len(results) == limit,
    }, ensure_ascii=False)


async def list_entries(
    status: str | None = None,
    topic_id: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> str:
    """List knowledge base entries with optional filters.

    Args:
        status: Filter by status name. Valid values: New, To Read, Important,
                Archive, Verified, Outdated. Leave empty to list all.
        topic_id: Filter by topic UUID — includes all subtopics automatically.
                  Get topic IDs from list_topics first.
        limit: Max results per page (1-50). Default 20.
        offset: Number of records to skip for pagination.

    Returns JSON with results list (id, title, status, topic, url, saved_date).
    """
    topic_uuid = None
    if topic_id:
        try:
            topic_uuid = uuid.UUID(topic_id)
        except ValueError:
            return json.dumps({"error": f"Invalid topic_id UUID: {topic_id}"})

    async with get_session() as session:
        repo = EntriesRepository(session)
        rows = await repo.list_entries(
            status_name=status,
            topic_id=topic_uuid,
            limit=min(limit, 50),
            offset=offset,
        )
    results = [
        {
            "id": str(entry.id),
            "title": entry.title or "",
            "status": status_name,
            "topic": topic_name,
            "url": entry.original_url or "",
            "saved_date": entry.saved_date.isoformat() if entry.saved_date else None,
        }
        for entry, status_name, topic_name in rows
    ]
    return json.dumps({
        "results": results,
        "count": len(results),
        "offset": offset,
        "has_more": len(results) == limit,
    }, ensure_ascii=False)


async def get_entry(entry_id: str) -> str:
    """Get full details of a single knowledge base entry by its UUID.

    Returns all fields: id, title, description, url, notes, status,
    primary_topic, secondary_topics (list), saved_date, updated_at.
    Use this after finding an entry via search_entries or list_entries
    to read its full content. Returns an error if the UUID is invalid
    or the entry does not exist.
    """
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        return json.dumps({"error": f"Invalid entry_id UUID: {entry_id}"})

    async with get_session() as session:
        entries_repo = EntriesRepository(session)
        row = await entries_repo.get_detail(eid)
        if row is None:
            return json.dumps({"error": f"Entry not found: {entry_id}"})
        entry, status_name, topic_name = row
        secondary = await entries_repo.list_secondary_topics(eid)

    return json.dumps({
        "id": str(entry.id),
        "title": entry.title or "",
        "description": entry.description or "",
        "url": entry.original_url or "",
        "notes": entry.notes or "",
        "status": status_name,
        "primary_topic": topic_name,
        "secondary_topics": [t.name for t in secondary],
        "saved_date": entry.saved_date.isoformat() if entry.saved_date else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }, ensure_ascii=False)


async def get_related(entry_id: str, limit: int = 5) -> str:
    """Find entries similar to the given entry using content similarity scoring.

    Returns a scored list ordered by relevance (higher score = more similar).
    Each result has: id, title, status, topic, score, same_topic, saved_date.
    Use this to discover related content after viewing a specific entry.

    Args:
        entry_id: UUID of the source entry.
        limit: Number of related entries to return (1-20). Default 5.
    """
    try:
        eid = uuid.UUID(entry_id)
    except ValueError:
        return json.dumps({"error": f"Invalid entry_id UUID: {entry_id}"})

    async with get_session() as session:
        service = SearchService(EntriesRepository(session))
        related = await service.related(eid, limit=min(limit, 20))

    results = [
        {
            "id": str(r.id),
            "title": r.title,
            "status": r.status_name,
            "topic": r.topic_name,
            "score": r.score,
            "same_topic": r.same_topic,
            "saved_date": r.saved_date.isoformat() if r.saved_date else None,
        }
        for r in related
    ]
    return json.dumps({
        "source_entry_id": entry_id,
        "results": results,
        "count": len(results),
    }, ensure_ascii=False)
