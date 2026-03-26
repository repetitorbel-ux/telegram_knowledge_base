# Release Notes Policy

This policy defines how release notes are maintained for `telegram-kb-bot`.

## Source of Truth

- `CHANGELOG.md` is the canonical release history.
- Every merge to `main` that changes behavior should be reflected in changelog.

## Entry Format

For each release version/date, include sections:

- `Added`
- `Changed`
- `Fixed`
- `Docs`

Entries should be short and user-impact oriented.

## Update Rule

- PR author adds changelog note in the same PR if behavior/config/ops changed.
- For docs-only changes, use `Docs` section.
- For operational changes (deploy, backup, restore), include runbook reference.

## Pre-Release Check

Before go-live:

1. Verify latest changes exist in `CHANGELOG.md`.
2. Ensure release notes mention migration/ops impact.
3. Link related runbooks if needed.
