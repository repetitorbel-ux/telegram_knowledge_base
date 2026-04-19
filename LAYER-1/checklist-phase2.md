# LAYER-1: Checklist Template — Phase 2

> Use this template for every new Phase 2 task.
> Copy this file, rename to `checklist-<feature-slug>.md`, fill in the blanks.
> See `LAYER-3/HANDOFF.md` for the current Phase 2 task queue.

---

## Task: [Feature Name]

**Branch:** `feature/<slug>`
**Status:** [ ] In Progress / [ ] Ready for Review / [ ] Done

---

## Pre-Work
- [ ] Read `LAYER-3/HANDOFF.md` — confirm current branch and state.
- [ ] Read spec from `LAYER-2/specs/` relevant to this task.
- [ ] Confirm working branch is NOT `main`.

## Implementation
- [ ] Code changes match the spec in `LAYER-2/specs/`.
- [ ] Single-user allowlist verified on any new handler.
- [ ] Status invariant not broken (if status logic touched).
- [ ] Schema change → migration created and tested on clean DB.
- [ ] URL normalization / dedup not regressed (if touched).

## Tests
- [ ] Unit tests added/updated for changed logic.
- [ ] Integration test passes (`python -m pytest -q`).
- [ ] CI green.

## Docs
- [ ] `LAYER-3/HANDOFF.md` updated with new state.
- [ ] `CHANGELOG.md` updated.

## Merge
- [ ] PR created from feature branch.
- [ ] CI checks pass.
- [ ] Merged to `main` only after all boxes above are checked.
