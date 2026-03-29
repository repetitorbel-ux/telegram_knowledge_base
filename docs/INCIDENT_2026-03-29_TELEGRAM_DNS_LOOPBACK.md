# Incident Note — 2026-03-29 — Telegram DNS Loopback on Autostart

## Summary

After Windows reboot on **2026-03-29**, Task Scheduler started the bot launcher, but the bot process did not stay alive.
Autostart itself worked, but runtime failed due to network/DNS resolution for Telegram API.

## Observed Symptoms

- Scheduled task `tg-kb-bot` status:
  - `Last Run Time: 29.03.2026 07:34:16`
  - `Last Result: 0`
- New log was created:
  - `logs/bot_20260329_073424.log`
- Runtime health check later failed:
  - `pwsh ./scripts/runtime_healthcheck_local.ps1`
  - result: `RUNTIME_CHECK: FAIL (bot process not found)`
- Bot traceback in log showed Telegram network failure:
  - `Cannot connect to host api.telegram.org:443`
  - attempted address: `127.164.0.27:443`

## Technical Findings

- `hosts` file has no override for `api.telegram.org`.
- WinHTTP proxy shows direct mode (`no proxy server`).
- DNS resolution from Python currently returns loopback-like address:
  - `socket.getaddrinfo('api.telegram.org', 443)` -> `127.164.0.27`
- `nslookup api.telegram.org` currently times out from this environment.

## Probable Root Cause

DNS/network path is unstable or locally filtered at startup time, causing invalid Telegram API resolution (`127.*`) and immediate bot startup failure.

## Initial Mitigation Applied

Local launcher `scripts/start_bot_local.ps1` was hardened with:

- preflight DNS check for `api.telegram.org`
- loopback (`127.*`) detection before bot start
- retry loop with delay instead of one-shot exit
- explicit launcher diagnostics in log file

Validation run produced:

- `logs/bot_20260329_080047.log`
- entries confirm DNS loopback detection and controlled retry behavior

## Resume Plan (When Reboot Is Possible)

1. Run network reset as Administrator:
   - `ipconfig /flushdns`
   - `netsh winsock reset`
2. Reboot PC.
3. Verify DNS from terminal:
   - `python -c "import socket; print(socket.getaddrinfo('api.telegram.org',443))"`
   - expected: non-`127.*` address set.
4. Validate bot runtime:
   - `pwsh ./scripts/runtime_healthcheck_local.ps1`
5. Telegram smoke:
   - `/start`
   - `/stats`
   - `/list limit=5`
6. If healthy, update checklist evidence with date/time and log file name.

## Notes

- This incident is about runtime connectivity, not Task Scheduler registration.
- Task Scheduler autostart trigger is functioning; failure is downstream at Telegram API connectivity stage.
