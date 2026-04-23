# P2-003 Manual Guide: Использование поиска

## 1. Перед началом

Проверить настройки `.env`:
- `SEMANTIC_SEARCH_ENABLED=true`
- `SEMANTIC_PROVIDER=local`
- `LOCAL_EMBEDDING_URL=http://127.0.0.1:11434/api/embeddings`
- `SEMANTIC_MODEL=nomic-embed-text`
- `SEMANTIC_EMBEDDING_DIM=768`
- `SEMANTIC_TIMEOUT_MS=20000`

Проверить модель в Ollama:
```powershell
ollama list
```

Проверить endpoint embeddings:
```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:11434/api/embeddings" `
  -ContentType "application/json" `
  -Body '{"model":"nomic-embed-text","prompt":"test"}'
```

## 2. Подготовка embeddings

```powershell
python -m kb_bot.jobs.semantic_backfill --max-entries 64
```

Интерпретация:
- `processed=64, updated>0` — embeddings дообновились.
- `processed=64, updated=0` — embeddings уже актуальны для текущей модели/провайдера.

Рекомендуется повторять запуск до стабилизации (`updated` перестает расти).

## 3. Как пользоваться поиском в Telegram

Базовый сценарий:
1. `/start`
2. `/search <keyword-запрос>`
3. `/search <смысловой запрос>`
4. открыть карточку записи из результатов

Примеры запросов:
- keyword: `/search pg_dump restore`
- смысловой: `/search безопасное восстановление базы после сбоя`

Ожидание:
- keyword-запрос возвращает релевантные записи по тексту;
- смысловой запрос поднимает записи, близкие по теме/контексту;
- интерфейс результатов и карточек работает без ошибок.

## 4. Проверка fallback (обязательно)

1. Остановить Ollama.
2. Выполнить `/search <запрос>`.
3. Убедиться, что поиск работает (fallback на keyword).
4. Запустить Ollama обратно и повторить `/search`.

## 5. Точная проверка актуальности embeddings (через БД)

Проверка summary (должно быть нули в `missing` и `stale`):
- `total_entries` — общее число записей;
- `missing_embeddings` — записи без embedding-строк;
- `stale_embeddings` — записи с неактуальным hash/model/provider/dim.

Целевое состояние:
- `missing_embeddings=0`
- `stale_embeddings=0`

## 6. Частые проблемы

`HTTP 500 Internal Server Error` от Ollama:
- причина часто в `input length exceeds the context length`;
- в проекте включен fallback с авто-укорочением текста, поэтому повторный прогон обычно добивает остаток;
- если 500 массовые, перезапустить Ollama и повторить backfill.

`processed=64, updated=0`:
- обычно это нормальный итог: embeddings уже синхронизированы.
