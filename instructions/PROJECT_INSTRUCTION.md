# Инструкция по проекту (локальный черновик)

## 1. Назначение

`telegram_knowledge_base` — локально-ориентированный Telegram-бот для сбора, структурирования и поиска базы знаний.
Текущий этап: проект готов к локальному запуску в solo-режиме, с CI и защищенной веткой `main`.

## 2. Базовая модель рантайма

- Бот запускается на локальной машине.
- Данные хранятся в локальном PostgreSQL.
- Взаимодействие идет через команды в Telegram.
- Бэкапы и восстановление доступны runtime-командами бота.

## 3. Требования к окружению

- Установлено Python-окружение с зависимостями проекта.
- Локальный PostgreSQL доступен по `DATABASE_URL`.
- Файл `.env` настроен (только локально, в git не коммитится).

Обязательные переменные `.env`:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_ID`
- `DATABASE_URL`
- `BACKUP_DIR`
- `PG_DUMP_BIN`
- `PG_RESTORE_BIN`

Проверка окружения:

```powershell
pwsh ./scripts/verify_prod_env.ps1 -EnvFilePath ./.env -Mode local
```

Ожидаемый результат: `SECTION2_ENV_CHECK: PASS`.

## 4. Ежедневные команды оператора

Проверка здоровья рантайма:

```powershell
pwsh ./scripts/runtime_healthcheck_local.ps1
```

Ручной запуск:

```powershell
pwsh ./scripts/start_bot_local.ps1
```

Регистрация автозапуска:

```powershell
pwsh ./scripts/register_autostart_task.ps1
schtasks /Query /TN tg-kb-bot
```

## 5. Telegram smoke-проверка

Запускать после рестарта/изменений/обновлений:

1. `/start`
2. `/stats`
3. `/list limit=5`

Если что-то не так — смотреть последний лог в `logs/`.

## 6. Безопасность бэкапа и восстановления

Основные runtime-команды:

- `/backup`
- `/backups`
- `/restore_token <backup_uuid>`
- `/restore <backup_uuid> <token>`

Базовый runbook:

- `docs/RESTORE_RUNBOOK.md`

## 7. Git workflow (обязательно)

- Никогда не работать напрямую в `main`.
- Одна задача -> одна ветка.
- Merge только через GitHub PR.
- Обязательный CI-check должен быть зеленым.

Ссылка:

- `GIT_WORKFLOW.md`

## 8. Правило защиты ветки для solo-режима

Для текущего solo-профиля репозитория:

- `main` защищена.
- required status check должен быть включен.
- `required_approving_review_count` должен быть `0` (solo-режим).

Проверка:

```bash
gh api repos/repetitorbel-ux/telegram_knowledge_base/branches/main/protection --jq '{required_reviews:.required_pull_request_reviews.required_approving_review_count, strict:.required_status_checks.strict, contexts:.required_status_checks.contexts}'
```

## 9. Отложенный инцидент

Отложенная проблема:

- `LAYER-3/incidents/INCIDENT_2026-03-29_TELEGRAM_DNS_LOOPBACK.md`
- `instructions/POSTGRES_SERVICE_INCIDENT_RU.md`

Кратко:

- Триггер автозапуска работает, но в части циклов после перезагрузки DNS для Telegram API может резолвиться в `127.*`.
- Если бот стартует, но кнопки списков/тем/статистики не работают, отдельно проверить локальную службу PostgreSQL.
- При возврате к задаче следовать шагам из incident-файла.

## 10. Чеклист возобновления на следующую сессию

1. Проверить текущую ветку и чистоту рабочего дерева.
2. Выполнить локальный healthcheck.
3. Выполнить Telegram smoke-команды.
4. Если возвращаемся к инциденту — пройти recovery steps и зафиксировать evidence.
5. Поддерживать актуальность чеклистов и handoff-файла.
