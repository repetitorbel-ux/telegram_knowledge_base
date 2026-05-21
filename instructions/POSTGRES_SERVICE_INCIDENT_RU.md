# Инцидент: бот запущен, но кнопки не работают из-за PostgreSQL

## Симптом

- Бот формально стартует.
- Кнопка `Список` может открывать экран фильтров.
- Кнопки внутри `Списка`, а также `Темы`, `Статистика` и другие сценарии не отвечают или выглядят "мертвыми".

## Типовая причина

Локальная служба PostgreSQL остановлена, поэтому бот не может выполнить запросы к БД по `DATABASE_URL`.

Для этого проекта частый локальный адрес:

- `127.0.0.1:5432`

## Как проверить

Проверить healthcheck:

```powershell
pwsh ./scripts/runtime_healthcheck_local.ps1
```

Если база недоступна, теперь ожидается явный статус:

```text
RUNTIME_CHECK: FAIL (PostgreSQL is unreachable at 127.0.0.1:5432)
```

Проверить саму службу:

```powershell
Get-Service postgresql-x64-17
```

Проверить доступность порта:

```powershell
"C:\Program Files\PostgreSQL\17\bin\pg_isready.exe" -h 127.0.0.1 -p 5432
```

## Восстановление

Запустить службу PostgreSQL:

```powershell
Start-Service postgresql-x64-17
```

Если служба отключена, включить автозапуск или ручной старт через повышенную PowerShell-сессию:

```powershell
Set-Service -Name postgresql-x64-17 -StartupType Automatic
Start-Service postgresql-x64-17
```

После этого перезапустить бота:

```powershell
pwsh ./scripts/start_bot_local.ps1
```

## Проверка после восстановления

1. `pwsh ./scripts/runtime_healthcheck_local.ps1`
2. `/start`
3. `Список` -> любая кнопка статуса
4. `Темы`
5. `Статистика`

## Если проблема повторяется после настройки прокси

Если PostgreSQL снова самопроизвольно недоступен после изменений в proxy/VPN/ISP software, дополнительно проверить:

- статус службы `postgresql-x64-17`;
- локальный доступ к `127.0.0.1:5432`;
- сетевой стек Windows (`netsh winsock reset`, затем reboot), если появляются ошибки уровня `WinError 10106`.

## Заметка по проекту

Скрипты уже усилены:

- `scripts/runtime_healthcheck_local.ps1` теперь валит healthcheck при недоступной БД;
- `scripts/start_bot_local.ps1` теперь не маскирует запуск бота без доступного PostgreSQL.
