# Runtime Reliability Runbook

This runbook describes an optional Linux/VPS runtime profile for checklist Section 4.  
It is not required for local-only Windows usage.

## Scope

- process supervision via `systemd`
- persistent/queryable logs via `journald`
- basic alerts for startup/runtime failures
- startup/reboot verification flow

## Files In Repo

- `deploy/systemd/tg-kb-bot.service`
- `deploy/systemd/tg-kb-alert@.service`
- `deploy/systemd/tg-kb-healthcheck.service`
- `deploy/systemd/tg-kb-healthcheck.timer`
- `scripts/runtime_healthcheck.sh`

## Install On Target Host (Linux)

From repo root on host:

```bash
sudo install -m 755 scripts/runtime_healthcheck.sh /usr/local/bin/tg-kb-runtime-healthcheck
sudo install -m 644 deploy/systemd/tg-kb-bot.service /etc/systemd/system/tg-kb-bot.service
sudo install -m 644 deploy/systemd/tg-kb-alert@.service /etc/systemd/system/tg-kb-alert@.service
sudo install -m 644 deploy/systemd/tg-kb-healthcheck.service /etc/systemd/system/tg-kb-healthcheck.service
sudo install -m 644 deploy/systemd/tg-kb-healthcheck.timer /etc/systemd/system/tg-kb-healthcheck.timer
sudo systemctl daemon-reload
sudo systemctl enable --now tg-kb-bot.service
sudo systemctl enable --now tg-kb-healthcheck.timer
```

## Persistent Logs

Ensure journald persistence is enabled:

```bash
sudo mkdir -p /var/log/journal
sudo systemctl restart systemd-journald
```

Primary log queries:

```bash
journalctl -u tg-kb-bot.service -n 200 --no-pager
journalctl -u tg-kb-bot.service --since "1 hour ago" --no-pager
journalctl -u tg-kb-bot.service -p err --since "24 hours ago" --no-pager
```

## Monitoring / Alerts (Minimum Baseline)

- `tg-kb-bot.service` has `OnFailure=tg-kb-alert@%n.service`.
- `tg-kb-healthcheck.timer` runs every 5 minutes.
- healthcheck writes to syslog/journal (`tg-kb-healthcheck` tag).

Check timer and recent runs:

```bash
systemctl status tg-kb-healthcheck.timer --no-pager
systemctl status tg-kb-healthcheck.service --no-pager
journalctl -t tg-kb-healthcheck -n 50 --no-pager
journalctl -t tg-kb-alert -n 50 --no-pager
```

## Startup / Reboot Verification

After reboot:

```bash
systemctl is-enabled tg-kb-bot.service
systemctl is-active tg-kb-bot.service
systemctl is-enabled tg-kb-healthcheck.timer
systemctl is-active tg-kb-healthcheck.timer
```

Then run bot smoke in Telegram:

- `/start`
- `/stats`
- `/list limit=5`

## Evidence To Attach (Checklist Section 4)

- output of `systemctl is-enabled/is-active` for bot service + timer
- recent `journalctl` snippets for `tg-kb-bot`, `tg-kb-healthcheck`, `tg-kb-alert`
- Telegram smoke command confirmations after reboot
