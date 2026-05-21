"""MCP server entry point for the Knowledge Base bot.

Exposes 8 tools for LLM access to the knowledge base database:
  - search_entries      — keyword search
  - list_entries        — filtered list with pagination
  - get_entry           — full details of a single entry
  - get_related         — similarity-scored related entries
  - list_topics         — topic tree with entry counts
  - get_topic_entries   — entries in a topic and its subtopics
  - get_stats           — knowledge base summary
  - semantic_search     — vector search (requires SEMANTIC_SEARCH_ENABLED=true)

Run with:
    python -m kb_bot.mcp_server.server

Required env:
    DATABASE_URL  — PostgreSQL connection string (asyncpg dialect supported)

Optional env:
    SEMANTIC_SEARCH_ENABLED=true   — enables semantic_search tool
    OPENAI_API_KEY / LOCAL_EMBEDDING_URL — embedding provider config
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from kb_bot.mcp_server.tools.entries import (
    get_entry,
    get_related,
    list_entries,
    search_entries,
)
from kb_bot.mcp_server.tools.semantic import semantic_search
from kb_bot.mcp_server.tools.stats import get_stats
from kb_bot.mcp_server.tools.topics import get_topic_entries, list_topics

mcp = FastMCP(
    name="kb-bot",
    instructions=(
        "Knowledge base MCP server. Provides read access to a personal knowledge "
        "database: articles, notes, bookmarks organised by topics and statuses."
    ),
)

# --- Entry tools ---
mcp.tool()(search_entries)
mcp.tool()(list_entries)
mcp.tool()(get_entry)
mcp.tool()(get_related)

# --- Topic tools ---
mcp.tool()(list_topics)
mcp.tool()(get_topic_entries)

# --- Stats ---
mcp.tool()(get_stats)

# --- Semantic search (always registered; returns error if disabled) ---
mcp.tool()(semantic_search)


if __name__ == "__main__":
    mcp.run()
