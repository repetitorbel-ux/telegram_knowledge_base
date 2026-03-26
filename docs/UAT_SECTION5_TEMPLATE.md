# Section 5 UAT Template (Critical Flows)

Use this file during production UAT for checklist Section 5.

## Test Metadata

- Date (UTC):
- Environment:
- Operator:
- Telegram user:
- Bot version/commit:

## Preconditions

- Production deploy completed.
- `Section 2` is closed (`SECTION2_ENV_CHECK: PASS` recorded).
- Test dataset available (topics, entries, sample import/export files).

## Execution Log

For each case, record command, expected result, actual result, and status.

### UAT-01 `/start` + auth guard

- Command(s):
  - `/start` from allowed user
  - `/start` from non-allowed user (or controlled simulation)
- Expected:
  - allowed user gets normal start response
  - non-allowed user is blocked
- Actual:
- Status: `[ ] PASS` / `[ ] FAIL`
- Evidence (message IDs/screenshots):

### UAT-02 `/add` manual flow

- Command(s):
  - `/add` with URL mode
  - `/add` with note mode
- Expected:
  - both flows complete and create entries
  - dedup/validation behaves correctly
- Actual:
- Status: `[ ] PASS` / `[ ] FAIL`
- Evidence:

### UAT-03 `/search`, `/list`, `/entry`, `/status`

- Command(s):
  - `/search <query>`
  - `/list limit=5`
  - `/entry <uuid>`
  - `/status <uuid> <status>`
- Expected:
  - results are returned and consistent with DB state
  - status transitions follow allowed workflow
- Actual:
- Status: `[ ] PASS` / `[ ] FAIL`
- Evidence:

### UAT-04 Topic flow

- Command(s):
  - `/topics`
  - `/topic_add`
  - `/topic_rename`
- Expected:
  - topic hierarchy updates correctly
  - new/renamed topics visible in subsequent commands
- Actual:
- Status: `[ ] PASS` / `[ ] FAIL`
- Evidence:

### UAT-05 Import/Export

- Command(s):
  - `/import` with representative CSV
  - `/import` with representative JSON
  - `/export` with filters
- Expected:
  - import jobs finish successfully
  - export files are generated and downloadable
- Actual:
- Status: `[ ] PASS` / `[ ] FAIL`
- Evidence:

### UAT-06 Collections

- Command(s):
  - `/collection_add`
  - `/collections`
  - `/collection_run`
- Expected:
  - collection saved and executable
  - output matches underlying query filters
- Actual:
- Status: `[ ] PASS` / `[ ] FAIL`
- Evidence:

### UAT-07 `/stats`

- Command(s):
  - `/stats`
- Expected:
  - dashboard appears without errors
  - metrics are plausible for current dataset
- Actual:
- Status: `[ ] PASS` / `[ ] FAIL`
- Evidence:

## Defects / Follow-ups

- ID:
- Severity:
- Description:
- Owner:
- Mitigation / rollback impact:

## Final UAT Decision

- Result: `[ ] PASS` / `[ ] FAIL`
- Approved by:
- Notes:
