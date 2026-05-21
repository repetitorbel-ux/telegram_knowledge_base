"""Tests for MCP server tools (unit tests with mocked DB)."""
from __future__ import annotations

import json
import types
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# --- helpers ---

def _make_entry(
    entry_id=None,
    title="Test Entry",
    description="desc",
    original_url="https://example.com",
    notes="some notes",
    saved_date=None,
    updated_at=None,
):
    from datetime import datetime, UTC
    e = MagicMock()
    e.id = entry_id or uuid.uuid4()
    e.title = title
    e.description = description
    e.original_url = original_url
    e.notes = notes
    e.saved_date = saved_date or datetime(2026, 1, 1, tzinfo=UTC)
    e.updated_at = updated_at or datetime(2026, 1, 2, tzinfo=UTC)
    e.primary_topic_id = uuid.uuid4()
    return e


def _make_topic(topic_id=None, name="Tech", full_path="tech", level=0):
    t = MagicMock()
    t.id = topic_id or uuid.uuid4()
    t.name = name
    t.full_path = full_path
    t.level = level
    t.is_active = True
    return t


# --- search_entries ---

@pytest.mark.asyncio
async def test_search_entries_returns_results():
    entry = _make_entry(title="Python guide")
    mock_session = AsyncMock()

    with patch("kb_bot.mcp_server.tools.entries.get_session") as mock_ctx:
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
        with patch("kb_bot.mcp_server.tools.entries.EntriesRepository") as MockRepo:
            instance = MockRepo.return_value
            instance.search = AsyncMock(return_value=[(entry, "New")])

            from kb_bot.mcp_server.tools.entries import search_entries
            result = await search_entries("Python")

    data = json.loads(result)
    assert data["count"] == 1
    assert data["results"][0]["title"] == "Python guide"
    assert data["results"][0]["status"] == "New"


@pytest.mark.asyncio
async def test_search_entries_empty_query_returns_error():
    from kb_bot.mcp_server.tools.entries import search_entries
    result = await search_entries("  ")
    data = json.loads(result)
    assert "error" in data


# --- list_entries ---

@pytest.mark.asyncio
async def test_list_entries_returns_results():
    entry = _make_entry(title="Article")
    mock_session = AsyncMock()

    with patch("kb_bot.mcp_server.tools.entries.get_session") as mock_ctx:
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
        with patch("kb_bot.mcp_server.tools.entries.EntriesRepository") as MockRepo:
            instance = MockRepo.return_value
            instance.list_entries = AsyncMock(return_value=[(entry, "To Read", "Tech")])

            from kb_bot.mcp_server.tools.entries import list_entries
            result = await list_entries(status="To Read")

    data = json.loads(result)
    assert data["count"] == 1
    assert data["results"][0]["status"] == "To Read"
    assert data["results"][0]["topic"] == "Tech"


@pytest.mark.asyncio
async def test_list_entries_invalid_topic_id_returns_error():
    from kb_bot.mcp_server.tools.entries import list_entries
    result = await list_entries(topic_id="not-a-uuid")
    data = json.loads(result)
    assert "error" in data


# --- get_entry ---

@pytest.mark.asyncio
async def test_get_entry_returns_full_details():
    entry = _make_entry(title="Full Details")
    topic = _make_topic(name="AI")
    mock_session = AsyncMock()

    with patch("kb_bot.mcp_server.tools.entries.get_session") as mock_ctx:
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
        with patch("kb_bot.mcp_server.tools.entries.EntriesRepository") as MockRepo:
            instance = MockRepo.return_value
            instance.get_detail = AsyncMock(return_value=(entry, "Important", "AI"))
            instance.list_secondary_topics = AsyncMock(return_value=[topic])

            from kb_bot.mcp_server.tools.entries import get_entry
            result = await get_entry(str(entry.id))

    data = json.loads(result)
    assert data["title"] == "Full Details"
    assert data["status"] == "Important"
    assert data["primary_topic"] == "AI"
    assert "AI" in data["secondary_topics"]


@pytest.mark.asyncio
async def test_get_entry_invalid_uuid():
    from kb_bot.mcp_server.tools.entries import get_entry
    result = await get_entry("bad-uuid")
    data = json.loads(result)
    assert "error" in data


@pytest.mark.asyncio
async def test_get_entry_not_found():
    mock_session = AsyncMock()
    with patch("kb_bot.mcp_server.tools.entries.get_session") as mock_ctx:
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
        with patch("kb_bot.mcp_server.tools.entries.EntriesRepository") as MockRepo:
            instance = MockRepo.return_value
            instance.get_detail = AsyncMock(return_value=None)

            from kb_bot.mcp_server.tools.entries import get_entry
            result = await get_entry(str(uuid.uuid4()))

    data = json.loads(result)
    assert "error" in data
    assert "not found" in data["error"].lower()


# --- list_topics ---

@pytest.mark.asyncio
async def test_list_topics_returns_tree():
    topic = _make_topic(name="Python", full_path="programming.python", level=1)
    mock_session = AsyncMock()

    with patch("kb_bot.mcp_server.tools.topics.get_session") as mock_ctx:
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
        with patch("kb_bot.mcp_server.tools.topics.TopicsRepository") as MockRepo:
            instance = MockRepo.return_value
            instance.list_tree = AsyncMock(return_value=[topic])
            mock_session.execute = AsyncMock(return_value=MagicMock(all=lambda: []))

            from kb_bot.mcp_server.tools.topics import list_topics
            result = await list_topics()

    data = json.loads(result)
    assert data["count"] == 1
    assert data["topics"][0]["name"] == "Python"
    assert data["topics"][0]["full_path"] == "programming.python"


# --- get_stats ---

@pytest.mark.asyncio
async def test_get_stats_returns_summary():
    mock_session = AsyncMock()

    with patch("kb_bot.mcp_server.tools.stats.get_session") as mock_ctx:
        mock_ctx.return_value.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.return_value.__aexit__ = AsyncMock(return_value=False)
        with patch("kb_bot.mcp_server.tools.stats.StatsService") as MockService:
            instance = MockService.return_value
            instance.get_stats = AsyncMock(return_value={
                "total_entries": 42,
                "by_status": {"New": 10, "Verified": 32},
                "by_topic": {"Tech": 20},
                "inbox_size": 10,
                "backlog": 0,
                "verified_coverage": 0.762,
                "duplicates_prevented": 3,
            })

            from kb_bot.mcp_server.tools.stats import get_stats
            result = await get_stats()

    data = json.loads(result)
    assert data["total_entries"] == 42
    assert data["by_status"]["New"] == 10


# --- semantic_search disabled ---

@pytest.mark.asyncio
async def test_semantic_search_disabled_returns_error(monkeypatch):
    monkeypatch.delenv("SEMANTIC_SEARCH_ENABLED", raising=False)
    from kb_bot.mcp_server.tools.semantic import semantic_search
    result = await semantic_search("machine learning")
    data = json.loads(result)
    assert "error" in data
    assert "disabled" in data["error"].lower()


# --- server tools registration ---

def test_server_registers_all_tools():
    from kb_bot.mcp_server.server import mcp
    tools = mcp._tool_manager.list_tools()
    names = {t.name for t in tools}
    expected = {
        "search_entries", "list_entries", "get_entry", "get_related",
        "list_topics", "get_topic_entries", "get_stats", "semantic_search",
    }
    assert expected == names
