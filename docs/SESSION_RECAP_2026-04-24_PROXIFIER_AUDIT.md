# Session Recap — 2026-04-24 — Proxifier Configuration Audit

## Summary

Проведён полный аудит конфигурации Proxifier v4.14 x64 для связки proxifier + psiphon (SSH/SSH+ режим).
Цель: обеспечить маршрутизацию чувствительных процессов (Windsurf, Antigravity) через SOCKS5-прокси (Psiphon), сохраняя стабильность Psiphon под нагрузкой.

## Исходная конфигурация

Профиль загружается как Service Profile из `C:\Program Files (x86)\Proxifier\ServiceProfile.ppx`.
Прокси: SOCKS5 на `127.0.0.1:50551` (Psiphon tunnel).

### Исходный порядок правил

| # | Имя правила | Applications | Targets | Action |
|---|---|---|---|---|
| 1 | Bypass-Direct | windsurf.exe; antigravity.exe; python.exe; node.exe; language_server_windows_x64.exe; searchapp.exe; ollama.exe | localhost; 127.0.0.1 | Direct |
| 2 | SuperEtka-Direct | — | superetka.com; *.superetka.com | Direct |
| 3 | The Bat | thebat64.exe; thebat.exe | — | Direct |
| 4 | Localhost | — | localhost; 127.0.0.1; %ComputerName%; ::1 | Direct |
| 5 | Home-LAN | — | 192.168.1.* | Direct |
| 6 | Proxy_Client | psiphon-tunnel-core.exe; psiphon3.exe | — | Direct |
| 7 | RMS-Direct | rutserv.exe; winserv.exe; rman.exe; rfusclient.exe; rutview.exe | — | Direct |
| 8 | Docker-WSL-Proxied | com.docker.backend.exe; com.docker.build.exe; com.docker.proxy.exe; docker-sandbox.exe; vmcompute.exe; wsl.exe; wslhost.exe; wslrelay.exe; wslservice.exe | — | Proxy 100 |
| 9 | OpenAI-Upstream-Proxied | — | auth.openai.com; chatgpt.com; *.chatgpt.com; *.openai.com; *.oaistatic.com; *.oaiusercontent.com | Proxy 100 |
| 10 | Firefox Direct | firefox.exe | — | Direct |
| 11 | Python Direct | python.exe; pythonw.exe | — | Direct |
| 12 | Default | — | — | Proxy 100 |

### Параметры Options

| Параметр | Значение | Комментарий |
|---|---|---|
| ViaProxy (DNS) | enabled | DNS резолвится через прокси |
| LeakPreventionMode | enabled | Защита от утечек DNS/IP |
| ConnectionLoopDetection | enabled | Предотвращение петель |
| Udp mode | mode_bypass | UDP обходит прокси |
| DnsUdpMode | 0 | — |
| Encryption | basic | — |
| ProcessServices | enabled | Обрабатывает сервисы Windows |
| ProcessOtherUsers | enabled | Обрабатывает процессы других пользователей |

## Выявленные проблемы

### КРИТИЧЕСКАЯ: python.exe идёт напрямую (утечка трафика)

Правило "Python Direct" (#11) отправляло **весь** трафик `python.exe` и `pythonw.exe` в обход прокси.
Если Windsurf или Antigravity порождают `python.exe` для внешних API-вызовов — трафик шёл напрямую, минуя прокси.

### КРИТИЧЕСКАЯ: Windsurf/Antigravity через прокси только «по остаточному принципу»

Правило "Bypass-Direct" (#1) содержит и `<Applications>`, и `<Targets>`.
В Proxifier при наличии обоих условий правило срабатывает **только если оба истинны одновременно** (логическое И).
Поэтому `windsurf.exe → api.openai.com` **не совпадало** с правилом #1 (target не localhost) и проваливалось до Default (#12).
Это работало, но было **хрупко** — любое новое правило Direct выше Default могло случайно перехватить чувствительный трафик.

### КРИТИЧЕСКАЯ: Firefox полностью сломан (fake IP)

Обнаружено в логах. DNS Leak Prevention создаёт fake IP из диапазона `127.108.0.x`.
Правило "Firefox Direct" отправляло firefox.exe напрямую, но Proxifier не мог разрешить fake IP обратно в реальный при Direct-соединении.
Результат: массовые ошибки `Cannot connect to placeholder (fake) IP address`.

### СРЕДНЯЯ: UDP-соединения блокируются для чувствительных приложений

В логах зафиксировано:
```
windsurf.exe - [2001:4860:4860::8888]:443 (UDP connect) (IPv6) matching Sensitive-Apps-Proxied rule : connection blocked
antigravity.exe - [2001:4860:4860::8888]:443 (UDP connect) (IPv6) matching Sensitive-Apps-Proxied rule : connection blocked
msedgewebview2.exe - [2603:1020:201:10::10f]:443 (UDP connect) (IPv6) matching Default rule : connection blocked
```
Это QUIC (HTTP/3) соединения. SOCKS5 через SSH не поддерживает UDP → блокировка.
Не критично: приложения автоматически переключаются на TCP. Но генерирует шум в логах.

### ЗАМЕЧАНИЕ: msedgewebview2.exe не в списке чувствительных

Windsurf использует Edge WebView2 внутри. `msedgewebview2.exe` подключался к `127.0.0.1:50551` (порт Psiphon) — вероятно, проверка доступности прокси.
Внешний трафик msedgewebview2.exe шёл через Default → Proxy, что корректно, но неявно.

## Принятые решения

### Подход: неинвертированный (Default → Proxy)

Рассматривались два подхода:

1. **Инвертированный** (Default → Direct, только чувствительные → Proxy) — отклонён, т.к. неизвестные процессы могут быть чувствительными и должны идти через прокси по умолчанию.
2. **Неинвертированный** (Default → Proxy, нечувствительные → Direct) — принят. Обеспечивает безопасность для неизвестных процессов при явной разгрузке Psiphon через Direct-правила для тяжёлых нечувствительных приложений.

### Структура правил: блочная организация

Правила организованы в 7 логических блоков с чётким порядком приоритетов.

## Итоговая конфигурация

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<ProxifierProfile version="102" platform="Windows" product_id="0" product_minver="400">
    <Options>
        <Resolve>
            <AutoModeDetection enabled="false" />
            <ViaProxy enabled="true" />
            <BlockNonATypes enabled="true" />
            <ExclusionList OnlyFromListMode="false">%ComputerName%; localhost; *.local; *.superetka.com; superetka.com</ExclusionList>
            <DnsUdpMode>0</DnsUdpMode>
        </Resolve>
        <Encryption mode="basic" />
        <ConnectionLoopDetection enabled="true" resolve="true" />
        <Udp mode="mode_bypass" />
        <LeakPreventionMode enabled="true" />
        <ProcessOtherUsers enabled="true" />
        <ProcessServices enabled="true" />
        <HandleDirectConnections enabled="true" />
        <HttpProxiesSupport enabled="false" />
    </Options>
    <ProxyList>
        <Proxy id="100" type="SOCKS5">
            <Options>48</Options>
            <Port>50551</Port>
            <Address>127.0.0.1</Address>
        </Proxy>
    </ProxyList>
    <ChainList />
    <RuleList>

        <!-- ═══ БЛОК 1: Защита от петель ═══ -->
        <Rule enabled="true">
            <Action type="Direct" />
            <Applications>psiphon-tunnel-core.exe; psiphon3.exe</Applications>
            <Name>Proxy_Client</Name>
        </Rule>

        <!-- ═══ БЛОК 2: Локальный трафик — Direct для ВСЕХ ═══ -->
        <Rule enabled="true">
            <Action type="Direct" />
            <Targets>localhost; 127.0.0.1; %ComputerName%; ::1</Targets>
            <Name>Localhost</Name>
        </Rule>
        <Rule enabled="true">
            <Action type="Direct" />
            <Targets>192.168.1.*</Targets>
            <Name>Home-LAN</Name>
        </Rule>
        <Rule enabled="true">
            <Action type="Direct" />
            <Targets>superetka.com; *.superetka.com</Targets>
            <Name>SuperEtka-Direct</Name>
        </Rule>

        <!-- ═══ БЛОК 3: Чувствительные приложения — ЯВНО через Proxy ═══ -->
        <Rule enabled="true">
            <Action type="Proxy">100</Action>
            <Applications>windsurf.exe; antigravity.exe; language_server_windows_x64.exe</Applications>
            <Name>Sensitive-Apps-Proxied</Name>
        </Rule>

        <!-- ═══ БЛОК 4: Чувствительные домены — Proxy для ЛЮБОГО приложения ═══ -->
        <Rule enabled="true">
            <Action type="Proxy">100</Action>
            <Targets>auth.openai.com; chatgpt.com; *.chatgpt.com; *.openai.com; *.oaistatic.com; *.oaiusercontent.com</Targets>
            <Name>OpenAI-Proxied</Name>
        </Rule>
        <Rule enabled="true">
            <Action type="Proxy">100</Action>
            <Targets>google.com; *.google.com; google.by; *.google.by; google.ru; *.google.ru; googleapis.com; *.googleapis.com; gstatic.com; *.gstatic.com; googleusercontent.com; *.googleusercontent.com; gmail.com; *.gmail.com; google.org; *.google.org</Targets>
            <Name>Google-Core-Proxied</Name>
        </Rule>
        <Rule enabled="true">
            <Action type="Proxy">100</Action>
            <Targets>googletagmanager.com; *.googletagmanager.com; google-analytics.com; *.google-analytics.com; googleadservices.com; *.googleadservices.com; doubleclick.net; *.doubleclick.net; gvt1.com; *.gvt1.com; gvt2.com; *.gvt2.com; gvt3.com; *.gvt3.com; appspot.com; *.appspot.com; withgoogle.com; *.withgoogle.com; firebase.google.com; *.firebaseio.com; *.firebaseapp.com</Targets>
            <Name>Google-Extended-Proxied</Name>
        </Rule>
        <Rule enabled="true">
            <Action type="Proxy">100</Action>
            <Targets>youtube.com; *.youtube.com; youtu.be; *.youtu.be; ytimg.com; *.ytimg.com; googlevideo.com; *.googlevideo.com; ggpht.com; *.ggpht.com</Targets>
            <Name>YouTube-Proxied</Name>
        </Rule>

        <!-- ═══ БЛОК 5: Docker/WSL — через Proxy ═══ -->
        <Rule enabled="true">
            <Action type="Proxy">100</Action>
            <Applications>com.docker.backend.exe; com.docker.build.exe; com.docker.proxy.exe; docker-sandbox.exe; vmcompute.exe; wsl.exe; wslhost.exe; wslrelay.exe; wslservice.exe</Applications>
            <Name>Docker-WSL-Proxied</Name>
        </Rule>

        <!-- ═══ БЛОК 6: Нечувствительные тяжёлые приложения — Direct ═══ -->
        <Rule enabled="true">
            <Action type="Direct" />
            <Applications>firefox.exe</Applications>
            <Name>Firefox-Direct</Name>
        </Rule>
        <Rule enabled="true">
            <Action type="Direct" />
            <Applications>thebat64.exe; thebat.exe</Applications>
            <Name>TheBat-Direct</Name>
        </Rule>
        <Rule enabled="true">
            <Action type="Direct" />
            <Applications>rutserv.exe; winserv.exe; rman.exe; rfusclient.exe; rutview.exe</Applications>
            <Name>RMS-Direct</Name>
        </Rule>
        <Rule enabled="true">
            <Action type="Direct" />
            <Applications>searchapp.exe; ollama.exe</Applications>
            <Name>LocalServices-Direct</Name>
        </Rule>

        <!-- ═══ БЛОК 7: Default — Proxy (неизвестные процессы защищены) ═══ -->
        <Rule enabled="true">
            <Action type="Proxy">100</Action>
            <Name>Default</Name>
        </Rule>

    </RuleList>
</ProxifierProfile>
```

## Блочная структура правил

| Блок | Назначение | Action | Правила |
|---|---|---|---|
| 1 | Защита от петель | Direct | Proxy_Client |
| 2 | Локальный трафик | Direct | Localhost, Home-LAN, SuperEtka-Direct |
| 3 | Чувствительные приложения | **Proxy 100** | Sensitive-Apps-Proxied |
| 4 | Чувствительные домены | **Proxy 100** | OpenAI-Proxied, Google-Core-Proxied, Google-Extended-Proxied, YouTube-Proxied |
| 5 | Docker/WSL | **Proxy 100** | Docker-WSL-Proxied |
| 6 | Нечувствительные тяжёлые приложения | Direct | Firefox-Direct, TheBat-Direct, RMS-Direct, LocalServices-Direct |
| 7 | Default | **Proxy 100** | Default |

## Логика прохождения трафика

### windsurf.exe → 127.0.0.1 (локальный)

```
Proxy_Client? нет → Localhost? ДА (target=127.0.0.1) → Direct ✓
```

### windsurf.exe → api.openai.com (внешний)

```
Proxy_Client? нет → Localhost? нет → Home-LAN? нет → SuperEtka? нет
→ Sensitive-Apps-Proxied? ДА (app=windsurf.exe) → Proxy 100 ✓
```

### unknown.exe → some-site.com (неизвестный процесс)

```
...все правила не совпали...
→ Default → Proxy 100 ✓ (неизвестный процесс защищён)
```

### firefox.exe → любой сайт

```
...блоки 1-5 не совпали...
→ Firefox-Direct? ДА (app=firefox.exe) → Direct ✓
```

## Ключевые изменения относительно исходной конфигурации

| Что изменилось | Было | Стало | Причина |
|---|---|---|---|
| Windsurf/Antigravity | Неявно через Default (хрупко) | Явное правило Sensitive-Apps-Proxied | Устранение хрупкости |
| python.exe | Правило "Python Direct" → Direct | Удалено. Идёт через Default → Proxy | Устранение утечки трафика |
| Правило "Bypass-Direct" | Applications + Targets (ложная защита) | Удалено. Localhost перехватывается общим правилом | Упрощение, устранение путаницы |
| Google-домены | Отсутствовали | Добавлены Google-Core, Google-Extended, YouTube | Маршрутизация через прокси |
| Порядок правил | Перемешаны Direct и Proxy | Чёткие блоки 1-7 | Читаемость, предсказуемость |

## Анализ логов (2026-04-24 16:41–16:42)

### Подтверждённое корректное поведение

- `windsurf.exe → 127.0.0.1` → Localhost → Direct — ОК
- `windsurf.exe → 127.0.0.1:61448` (health-check polling ~1/сек) — ОК
- Правило Sensitive-Apps-Proxied срабатывает для windsurf/antigravity (видно по UDP-блокировке) — ОК
- Psiphon не зациклен — ОК

### Обнаруженные проблемы в логах

#### Firefox — fake IP (критично)

```
firefox.exe (15096) - 127.108.0.4:443 error: Cannot connect to placeholder (fake) IP address.
firefox.exe (15096) - 127.108.0.12:443 error: Cannot connect to placeholder (fake) IP address.
```

**Механизм:** DNS Leak Prevention возвращает fake IP (127.108.0.x) → Firefox-Direct отправляет напрямую → Proxifier не может разрешить fake IP при Direct → ошибка.

**Решения:**
- **Вариант A:** Удалить Firefox-Direct → Firefox через Default → Proxy (нагрузка на Psiphon)
- **Вариант B (рекомендуется):** Включить DNS-over-HTTPS в Firefox (Settings → Privacy → DNS over HTTPS, например Cloudflare 1.1.1.1). Firefox сам резолвит DNS, Proxifier не подставляет fake IP, правило Firefox-Direct работает.
- **Вариант C:** Исключить firefox.exe из Proxifier полностью

#### UDP QUIC блокировка (некритично)

```
windsurf.exe - [2001:4860:4860::8888]:443 (UDP) → Sensitive-Apps-Proxied → blocked
antigravity.exe - [2001:4860:4860::8888]:443 (UDP) → Sensitive-Apps-Proxied → blocked
msedgewebview2.exe - [2603:1020:201:10::10f]:443 (UDP) → Default → blocked
```

QUIC/HTTP3 через UDP не поддерживается SOCKS5/SSH. Приложения автоматически переключаются на TCP. Шум в логах, но не влияет на функциональность.

#### msedgewebview2.exe — подключение к порту прокси

```
msedgewebview2.exe - 127.0.0.1:50551 → Localhost → direct (9 bytes sent, 8 received)
```

Windsurf использует Edge WebView2 внутри. Крошечные соединения к порту Psiphon — вероятно, проверка доступности. Рекомендуется рассмотреть добавление `msedgewebview2.exe` в Sensitive-Apps-Proxied.

## Рекомендации по эксплуатации

### Разгрузка Psiphon

Если Psiphon падает под нагрузкой:
1. Первый кандидат на отключение: правило **YouTube-Proxied** (`enabled="false"`)
2. Смотреть логи Proxifier, находить тяжёлые нечувствительные процессы, добавлять в блок 6 (Direct)
3. Рассмотреть `node.exe`: если добавить в блок 6 (Direct) — снизит нагрузку, но node.exe от Windsurf не пойдёт через прокси. Компромисс: правила блока 4 (домены) перехватят node.exe при обращении к OpenAI/Google.

### node.exe — компромисс

`node.exe` используется многими приложениями, не только Windsurf. Варианты:
- **Не добавлять в Sensitive-Apps-Proxied** → идёт через Default → Proxy (нагрузка)
- **Добавить в блок 6 (Direct)** → снижает нагрузку, но трафик node.exe к внешним API идёт напрямую (кроме доменов из блока 4)
- **Добавить в Sensitive-Apps-Proxied** → весь трафик node.exe через прокси (максимальная нагрузка)

### Мониторинг

Периодически проверять логи Proxifier на:
- Новые ошибки fake IP (признак конфликта Direct + DNS Leak Prevention)
- Новые неизвестные процессы, генерирующие много трафика через Default → Proxy
- Блокировки UDP (информационно)

### Добавление региональных Google-доменов

При необходимости добавить в Google-Core-Proxied:
```
google.de; *.google.de; google.pl; *.google.pl; ...
```

## Связанные документы

- `docs/INCIDENT_2026-03-29_TELEGRAM_DNS_LOOPBACK.md` — инцидент с DNS loopback для Telegram API (связан с Proxifier/DNS)
- `docs/RUNTIME_RELIABILITY_RUNBOOK_WINDOWS.md` — запуск бота на Windows (контекст: бот работает через тот же Proxifier)
- `DEPLOYMENT_TARGET.md` — целевая платформа (Windows + Docker Desktop)

## Ключевые термины

| Термин | Значение в контексте |
|---|---|
| Proxy 100 | SOCKS5 прокси на 127.0.0.1:50551 (Psiphon tunnel) |
| Fake IP / Placeholder IP | Внутренний IP из диапазона 127.108.0.x, который Proxifier подставляет при DNS Leak Prevention вместо реального IP |
| QUIC | HTTP/3 протокол поверх UDP, не поддерживается SOCKS5/SSH |
| Блок 1-7 | Логические группы правил в конфигурации Proxifier |
| Логическое И | Поведение Proxifier при наличии и Applications, и Targets в одном правиле — оба условия должны совпасть |
