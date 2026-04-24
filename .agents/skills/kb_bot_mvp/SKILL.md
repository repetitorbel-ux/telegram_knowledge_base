---
name: kb-bot-mvp
description: Use this skill when implementing or modifying the Telegram KB bot MVP (topics tree, dedup, search, import/export, backups). It enforces the required entities, statuses, and DB schema patterns.
---

## Scope
Applies only to this repository. Use when:
- adding bot commands/handlers
- changing DB schema/migrations
- implementing URL normalization, dedup, search, or topic hierarchy
- adding import/export/backup/restore behaviors

## Non-negotiables
- Single-user allowlist must gate every handler.
- Status codes and display names must remain exactly: New, To Read, Important, Archive, Verified, Outdated.
- Topic hierarchy must remain dynamic and nested (no enums).
- Any change to schema requires a migration and a verification query.

## Definition of done for any change
- Unit tests updated or added (at least for URL normalization and dedup if touched).
- DB migration updated (if schema touched) and passes on a clean database.
- Bot command/flow updated with a minimal happy-path and an error-path response.
