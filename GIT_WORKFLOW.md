# Git Workflow

## Current setup

- Local repository: `d:\Development_codex\tg_db`
- Main integration branch: `main`
- GitHub remote is the source of truth for `main`
- Task work happens in short-lived branches

## Working model

Use this workflow consistently:

- every new task starts in a new branch
- do not develop directly in local `main`
- do not merge task branches into local `main`
- push task branches to GitHub
- merge into `main` on GitHub via pull request or web merge
- after GitHub merge, sync local `main` from `origin/main`

In practice:

- local `main` is a sync branch
- feature work lives only in `feature/...`, `fix/...`, or `docs/...`
- GitHub `main` is the canonical stable history
- one task equals one dedicated branch with a meaningful name

## Branch naming

Recommended branch names:

- `feature/tg-topic-filters`
- `feature/tg-import-hardening`
- `fix/restore-token-validation`
- `docs/refine-git-workflow`

## Start a new task

Before starting a new task, make sure local `main` is up to date:

```bash
git checkout main
git pull origin main
git checkout -b feature/<short-task-name>
```

Hard gate before any edit:

```bash
git branch --show-current
```

- if the result is `main`, stop and create the task branch first
- do not edit files while still on `main`, even for a small quick fix
- do not rely on remembering this mentally; verify the branch explicitly before the first edit

Important rules:

- every new task must start from a new branch
- do not reuse an old task branch for unrelated work
- do not create placeholder branches such as `feature/next-task`
- start a new branch only from updated `main`
- keep the working tree clean before switching branches
- if local `main` has accidental commits, do not continue from it until the situation is resolved

## Daily work

Make small logical commits instead of one large commit.

Useful commands:

```bash
git status
git add <file>
git commit -m "Short clear message"
```

Good commit message examples:

- `Add restore runbook for backup operations`
- `Fix backup checksum verification on restore`
- `Add CI workflow for migrations and tests`

## Before pushing a task branch

Run the minimum project checks:

```bash
python -m pytest -q
```

## Publish the branch to GitHub

Push the task branch and set upstream:

```bash
git push -u origin feature/<short-task-name>
```

After push:

- open the branch on GitHub
- create a pull request into `main`
- merge on GitHub, not locally

Preferred GitHub CLI path:

```bash
gh pr create --base main --head <task-branch> --title "Short title" --body "Summary"
gh pr merge --merge --delete-branch
git checkout main
git pull origin main
```

Use this path when `gh` is authenticated and working.

## Solo profile (important)

This repository currently uses a **solo-maintainer protection profile**:

- branch protection on `main` is enabled
- required status check is enabled (`test-and-migration-smoke`)
- `required_approving_review_count` is intentionally set to `0`

Why this matters:

- in solo mode GitHub does not allow approving your own PR
- if required reviews are set to `1`, merge will be blocked and creates unnecessary overhead
- CI remains the hard merge gate for quality

Quick verification command:

```bash
gh api repos/repetitorbel-ux/telegram_knowledge_base/branches/main/protection --jq '{required_reviews:.required_pull_request_reviews.required_approving_review_count, strict:.required_status_checks.strict, contexts:.required_status_checks.contexts, enforce_admins:.enforce_admins.enabled}'
```

Expected for solo mode:

- `required_reviews: 0`
- `contexts` includes `test-and-migration-smoke`
- `strict: true`

If this drifts back to `required_reviews: 1`, restore it before continuing normal flow.

## Sandbox notes for git commands

Most local editing work can stay inside sandbox, but some git commands may fail there because of
network access, credential prompts, or shell subprocess restrictions.

Typical failure signs:

- `Win32 error 5`
- `prompt script failure`
- `could not read Username`
- `permission denied` around git credential or shell helper processes

Practical rule:

- if `git pull`, `git push`, remote branch deletion, or GitHub CLI commands fail with these symptoms,
  rerun them with escalation outside sandbox
- do not treat that as a repo problem by default; first suspect environment restrictions
- if authentication works in your host terminal but fails in sandbox, repeat the same command outside sandbox without changing workflow intent

## Execution policy for this project

- run the full git cycle end-to-end by default:
  - sync `main`
  - create task branch
  - run required checks
  - push branch
  - create PR
  - merge PR
  - sync local `main`
- do not pause to ask whether to merge/push/create PR once the task is approved; proceed automatically
- do not create commits until the user has reviewed changes or explicitly requested a commit
- only pause when an action is destructive, ambiguous, or blocked by missing access/credentials

## After GitHub merge

Once the branch is merged on GitHub:

```bash
git checkout main
git pull origin main
git branch -d feature/<short-task-name>
```

Optional cleanup of the remote branch:

```bash
git push origin --delete feature/<short-task-name>
```

## Rules for `main`

- do not commit directly to `main`
- do not merge task branches into local `main`
- use local `main` only to sync from GitHub and create new task branches

## What should not be committed

Do not commit generated or local-only files:

- `__pycache__/`
- `.pytest_cache/`
- `.mypy_cache/`
- `.venv/`
- `venv/`
- `logs/`
- `errors/`
- `.vscode/`
- `.idea/`
- `*.zip`
- `.env`
- `.env.*`
- `.e2e.alembic.ini`
- `.e2e_pgdata/`
- `*.egg-info/`

These are covered by `.gitignore`.

## Minimal happy path

Typical task flow:

```bash
git checkout main
git pull origin main
git checkout -b feature/<task>
git status
git add <files>
git commit -m "Short clear message"
python -m pytest -q
git push -u origin feature/<task>
```

Then:

1. Create PR on GitHub.
2. Merge into `main` on GitHub.
3. Sync local `main`.
4. Delete the finished branch.
