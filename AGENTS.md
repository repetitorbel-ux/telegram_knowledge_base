# AGENTS.md

## AI Workspace Baseline

- Canonical workspace guide: `D:\Development_codex\_workspace_admin\docs\WORKSPACE_GUIDE.md`
- This repository uses `GIT_WORKFLOW.md` as the source of truth for branch discipline and git actions.
- Read this file first, then read `GIT_WORKFLOW.md` before making substantial changes.
- Use `instructions/PROJECT_INSTRUCTION.md` for operator-oriented runtime context and local operational commands.
- Human-facing Russian documents live under `human\`; do not load them unless the user explicitly asks for user documentation or translation work.
- Local-only Codex overrides may be placed in `.codex\config.toml`; keep that file unversioned.

## Task Start Rule

- Before any file edit, confirm the current branch is not `main`.
- If the current branch is `main`, stop and create a task branch from updated `main`.
- Treat `README.md`, `GIT_WORKFLOW.md`, and `instructions/PROJECT_INSTRUCTION.md` as required project context for setup-oriented work.

## Git Safety

- Follow `GIT_WORKFLOW.md` unless a higher-priority instruction overrides it.
- Do not commit directly to `main`.
- Do not create commits until the user has reviewed changes or explicitly asked for a commit.
