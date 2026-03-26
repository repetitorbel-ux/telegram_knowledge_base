#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-tg-kb-bot.service}"

if systemctl is-active --quiet "${SERVICE_NAME}"; then
  logger -p user.info -t tg-kb-healthcheck "${SERVICE_NAME} is active"
  exit 0
fi

logger -p user.err -t tg-kb-healthcheck "${SERVICE_NAME} is NOT active"
systemctl --no-pager --full status "${SERVICE_NAME}" || true
journalctl -u "${SERVICE_NAME}" -n 100 --no-pager || true
exit 1
