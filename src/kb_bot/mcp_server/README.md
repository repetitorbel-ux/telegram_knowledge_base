# KB Bot MCP Server

MCP server that exposes a personal knowledge base database to LLMs (Claude, Codex, etc.).

## Tools

| Tool | Description |
|---|---|
| `search_entries` | Keyword search across title/notes/description |
| `list_entries` | List entries filtered by status and/or topic |
| `get_entry` | Full details of a single entry by UUID |
| `get_related` | Similarity-scored entries related to a given entry |
| `list_topics` | Topic tree with entry counts |
| `get_topic_entries` | Entries in a topic and all its subtopics |
| `get_stats` | Knowledge base summary (totals, by status, by topic) |
| `semantic_search` | Vector similarity search (requires provider config) |

## Requirements

- Python 3.12+
- `mcp>=1.0.0` (installed via `pip install mcp`)
- PostgreSQL with the KB Bot schema migrated (`alembic upgrade head`)

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | **Yes** | — | PostgreSQL URL (asyncpg dialect). Example: `postgresql+asyncpg://user:pass@localhost:5432/tg_kb` |
| `SEMANTIC_SEARCH_ENABLED` | No | `false` | Set `true` to enable `semantic_search` tool |
| `OPENAI_API_KEY` | No | — | For OpenAI embedding provider |
| `LOCAL_EMBEDDING_URL` | No | — | For local Ollama provider (e.g. `http://localhost:11434`) |
| `SEMANTIC_PROVIDER` | No | `openai` | `openai` or `local` |
| `SEMANTIC_MODEL` | No | `text-embedding-3-small` | Embedding model name |

## Running

```bash
# Direct
python -m kb_bot.mcp_server.server

# With explicit env
DATABASE_URL="postgresql+asyncpg://..." python -m kb_bot.mcp_server.server
```

## Claude Desktop / Codex config (`.mcp.json`)

```json
{
  "mcpServers": {
    "kb-bot": {
      "command": "python",
      "args": ["-m", "kb_bot.mcp_server.server"],
      "cwd": "/path/to/tg_db",
      "env": {
        "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/tg_kb"
      }
    }
  }
}
```

## Pagination

All list tools support `offset` for pagination. When `has_more: true` is returned, pass `offset + limit` in the next call.

## Error Handling

All tools return JSON. On error, the response contains `{"error": "...human readable message..."}` — never raw HTTP errors or stack traces.

## Semantic Search Notes

`semantic_search` is always registered but returns an error when disabled. This allows the LLM to detect the tool exists but understand it needs configuration. To enable:

1. Set `SEMANTIC_SEARCH_ENABLED=true`
2. Configure `LOCAL_EMBEDDING_URL` (Ollama) or `OPENAI_API_KEY`
3. Run the backfill job: `python -m kb_bot.jobs.semantic_backfill`
