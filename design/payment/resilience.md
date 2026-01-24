# Resilience

Паттерны отказоустойчивости платёжной системы.

## SLI/SLO

| SLI                                                         | SLO                | Где измеряем                    | Error Budget                     |
| ----------------------------------------------------------- | ------------------ | ------------------------------- | -------------------------------- |
| Доступность: % запросов createPayment без 5xx               | ≥ 99.9% за 30 дней | API Gateway (HTTP status codes) | 43 мин/мес даунтайма             |
| Латентность: p99 времени ответа createPayment               | ≤ 3с               | API Gateway (request duration)  | 1% запросов могут быть медленнее |
| Корректность: % платежей где Wallet.status = Payment.status | 100%               | Query Service metrics           | 0 — любое расхождение = инцидент |

## Паттерны

Таймауты sync-вызовов выводятся из SLO латентности (p99 ≤ 3с).

**Предпосылки:**

Нагрузка:

- Ожидаемый RPS payment flow: 1000

Внешние SLA:

- Платёжный провайдер: ответ до 30с, rate limit 1000 rps по контракту
- Провайдеры уведомлений (SMS/Push/Email): ответ до 10с

Ожидаемая средняя latency:

- Внутренние сервисы (Wallet, Payment, Callback, Query): 100ms
- Anti-Fraud (ML scoring): 50ms
- DB query: 10ms

Kafka партиции: 12 (основные топики), 6 (callbacks) — см. [scaling.md](scaling.md#масштабирование-kafka)

Rate limits:

- API Gateway (Kong + Redis): 10k RPS global, 100 RPS per customer_id из `X-Customer-ID` header (ставит BFF после auth), для неаутентифицированных — per IP

| Взаимодействие                | Таймаут | Повторы                            | Circuit Breaker  | Bulkhead           | Rate Limit | Fallback             |
| ----------------------------- | ------- | ---------------------------------- | ---------------- | ------------------ | ---------- | -------------------- |
| BFF → Wallet                  | 2с      | 2 sync (100ms)                     | нет              | HTTP pool: 100     | —          | нет                  |
| BFF → Query                   | 2с      | 2 sync (100ms)                     | нет              | HTTP pool: 60      | —          | stale cache (TTL 5м) |
| Payment → Anti-Fraud          | 500ms   | 1 sync                             | 50% err / 10 req | gRPC pool: 50      | —          | ALLOW (fail-open)    |
| Payment → Provider            | 30с     | 3 sync (1-2-4с) + 3 async (1-2-4м) | 50% err / 10 req | HTTP pool: 200     | 1000 rps   | DLQ                  |
| Callback → Payment            | 2с      | 3 sync (exp backoff)               | нет              | —                  | —          | DLQ                  |
| Notification → SMS/Email/Push | 10с     | 3 sync + 3 async (5м)              | 50% err / 10 req | HTTP pool: 100 × 3 | 500 rps    | DLQ                  |

## Обоснования

**BFF → Wallet (резерв средств)**

Синхронный HTTP POST запрос из BFF в Wallet Service для создания резерва.

1. Timeout: 2с
   Потому что SLO 3с на весь запрос. BFF делает один вызов к Wallet. оставляет 1с на запас.

2. Retry: 2, 100ms + jitter
   Потому что защищает от кратковременных сбоев сети. Worst case (все 3 попытки по таймауту): 3 × 2с = 6с > SLO. Но таймаут — редкость (< 0.1%), обычно ответ за 100ms. Retry нужен для transient errors (connection reset, 503), не для таймаутов.

3. Circuit Breaker: нет
   Потому что CB полезен когда есть fallback. Здесь fallback нет — без резерва платёж невозможен. Если Wallet упал, CB только добавит 30-60с задержки на восстановление, а платежи всё равно не пройдут.

4. Bulkhead: HTTP pool 100
   Отдельный HTTP-пул в BFF для вызовов Wallet: RPS 1000 × latency 100ms = 100 соединений.
   Изолирован от пула Query — если Wallet тормозит, Query продолжает работать.

5. Rate Limit: нет (на уровне BFF)
   Потому что rate limit уже применён на API Gateway (10k RPS global, 100 RPS per customer). BFF доверяет трафику, прошедшему через Gateway. Дополнительный rate limit здесь избыточен.

6. Fallback: нет
   Потому что резерв средств — обязательный шаг платежа. Без него нельзя продолжить: клиент может не иметь денег, или они уже зарезервированы другим платежом.

**BFF → Query (чтение истории платежей)**

Синхронный HTTP GET из BFF в Query Service для получения списка/статуса платежей.

1. Timeout: 2с
   Потому что SLO 3с, аналогично Wallet. Query делает SELECT из read-модели — должно быть быстро (~50ms). 2с — запас на сложные запросы (фильтры, пагинация).

2. Retry: 2 sync (100ms)
   Потому что read-запросы идемпотентны, retry безопасен. При таймауте — сразу fallback на cache, retry только для transient errors (503, connection reset).

3. Circuit Breaker: нет
   Потому что есть fallback на кэш. CB избыточен — при сбое Query сразу отдаём из кэша, не нужно ждать открытия CB.

4. Bulkhead: HTTP pool 60
   Отдельный HTTP-пул в BFF для вызовов Query: ~600 RPS × latency 100ms = 60 соединений.
   Изолирован от пула Wallet — если Query тормозит, Wallet-вызовы не страдают.

5. Rate Limit: нет (на уровне BFF)
   Потому что rate limit уже применён на API Gateway. Query — read-only сервис, легко масштабируется горизонтально. Дополнительный rate limit избыточен.

6. Fallback: stale cache (Redis, TTL 5м)
   Потому что история платежей — не real-time данные. Если Query недоступен, отдаём последние закэшированные данные. Пользователь видит историю 5-минутной давности — лучше, чем ошибку. Свежий платёж может не отобразиться сразу — приемлемо.

**Payment → Anti-Fraud**

Синхронный gRPC вызов из Payment Service в Anti-Fraud Service для проверки платежа на мошенничество перед отправкой провайдеру.

1. Timeout: 500ms
   Потому что Anti-Fraud — внутренний сервис, ML-модель должна отвечать быстро. 500ms — запас на пики нагрузки.

2. Retry: 1
   Потому что есть fallback (ALLOW). Один retry для кратковременных сбоев. При повторной ошибке — сразу fallback, платёж не должен зависать.

3. Circuit Breaker: 50% ошибок за последние 10 запросов, открыт 30с
   Потому что если 5 из 10 запросов упали — сервис болеет. CB переходит в Open: запросы сразу получают fallback (ALLOW). Через 30с — Half-Open: пропускаем 3 пробных запроса.

4. Bulkhead: gRPC pool 50
   Отдельный gRPC-пул для Anti-Fraud: RPS 1000 × latency 50ms = 50 соединений.
   Изолирован от HTTP-пула Provider — если Anti-Fraud тормозит, Provider-вызовы не страдают.

5. Rate Limit: нет
   Потому что Anti-Fraud — внутренний сервис, масштабируется вместе с Payment. Нагрузка на Anti-Fraud = нагрузка на Payment (1:1). Rate limit на входе в Payment уже защищает Anti-Fraud.

6. Fallback: ALLOW
   Потому что бизнес-решение: риск пропустить fraudulent платёж при сбое Anti-Fraud меньше, чем потерять 100% платежей.

**Payment → Provider**

Синхронный HTTP POST запрос из Payment Service во внешний платёжный провайдер для авторизации и списания средств с карты/счёта клиента.

1. Timeout: 30с
   Потому что по SLA провайдера ответ может занять до 30с (см. Предпосылки). Если поставить меньше — будем обрывать запросы, которые провайдер ещё обрабатывает.

2. Retry: 3 sync (1с → 2с → 4с) + 3 async (1м → 2м → 4м)
   **Sync retries (in-memory):** провайдеры могут возвращать 503 или connection timeout при кратковременных проблемах. Exponential backoff даёт провайдеру время восстановиться.
   **Async retries (Kafka):** если sync не помогли — платёж уходит в `payments.retry` топик. Payment Service читает и пробует снова через 1м, 2м, 4м. Интервалы привязаны к CB cooldown (60с).

3. Circuit Breaker: 50% ошибок за последние 10 запросов, открыт 60с
   Потому что если 5 из 10 запросов упали — провайдер болеет. CB открывается: новые платежи сразу уходят на async retry (без HTTP к провайдеру). Через 60с — Half-Open, пробуем 3 запроса.

4. Bulkhead: HTTP pool 200
   Отдельный HTTP-пул для Provider: ограничен 200 соединениями (запас для retry при latency spikes).
   Изолирован от gRPC-пула Anti-Fraud.

5. Rate Limit: 1000 rps (Resilience4j RateLimiter, in-memory)
   Потому что провайдер принимает максимум 1000 rps по контракту (см. Предпосылки). 6 инстансов × ~167 rps = 1000 rps суммарно.

6. Fallback: DLQ
   Потому что платёж нельзя терять. После всех retry (3 sync + 3 async, ~9 минут суммарно) — сообщение уходит в `payments.retry.dlq`. Алерт, manual review. См. [queues.md](queues.md#dlq-dead-letter-queue).

**Callback → Payment**

Синхронный HTTP POST из Callback Service в Payment Service для передачи результата платежа от провайдера.

1. Timeout: 2с
   Потому что Payment — внутренний сервис, должен отвечать быстро. 2с — запас на пики нагрузки.

2. Retry: 3, exponential backoff (100ms → 200ms → 400ms)
   Потому что callback — критичные данные (результат платежа). Терять нельзя.

3. Circuit Breaker: нет
   Потому что Payment — критичный внутренний сервис. Если упал — это инцидент, CB не поможет. Fallback (DLQ) сработает после retry.

4. Bulkhead: нет
   Callback Service вызывает только Payment — нечего изолировать.

5. Rate Limit: нет
   Потому что callback'и приходят от провайдера в ответ на наши платежи. Количество callback'ов ≤ количество отправленных платежей. Rate limit на Payment → Provider (1000 rps) косвенно ограничивает и callback'и.

6. Fallback: DLQ
   Потому что если Payment недоступен после retry — callback нельзя потерять. Сохраняем в `callbacks.received.dlq` для переотправки.

**Notification → SMS/Email/push**

Синхронный HTTP POST из Notification Service во внешние провайдеры для отправки уведомления клиенту о результате платежа.

1. Timeout: 10с
   Потому что по SLA провайдеров уведомлений ответ может занять до 10с (см. Предпосылки).

2. Retry: 3 sync (1с → 2с → 4с) + 3 async (интервал 5м)
   **Sync retries (in-memory):** уведомления важны, но некритичны для платежа. Быстрый backoff для transient errors.
   **Async retries (Kafka):** если sync не помогли — уведомление уходит в `notifications.retry`. Cron-job пробует переотправить каждые 5 минут (3 попытки).

3. Circuit Breaker: 50% ошибок за последние 10 запросов, открыт 60с
   Потому что если провайдер sms/email/push лежит — не нужно долбить. CB открывается, уведомления сразу уходят на async retry.

4. Bulkhead: HTTP pool 100 × 3
   Три изолированных HTTP-пула по 100 соединений: SMS, Email, Push.
   Если SMS-провайдер лежит — Email и Push продолжают работать.

5. Rate Limit: 500 rps × 3 канала (golang.org/x/time/rate, in-memory)
   Потому что провайдеры уведомлений имеют лимиты по тарифу. Отдельный лимитер на SMS/Email/Push — если один канал исчерпал лимит, другие работают.

6. Fallback: DLQ
   После всех retry (3 sync + 3 async, ~15 минут) — уведомление уходит в `notifications.retry.dlq`. Алерт, manual review.

## Сценарий: провайдер недоступен

Timeout → Sync Retries → Circuit Breaker → Async Retries (retry queue) → DLQ.

### Circuit Breaker

CB — библиотека внутри сервиса (Resilience4j для Java/Kotlin, gobreaker для Go), защищает от каскадных отказов.

**Состояния:**

| Состояние | Поведение                               |
| --------- | --------------------------------------- |
| CLOSED    | Запросы идут к провайдеру нормально     |
| OPEN      | Запросы сразу reject, HTTP не делается  |
| HALF-OPEN | Пропускает 3 probe-запроса для проверки |

**Переходы:**

| Переход            | Условие                           |
| ------------------ | --------------------------------- |
| CLOSED → OPEN      | 50% ошибок в последних 10 вызовах |
| OPEN → HALF-OPEN   | Прошло 60с (cooldown)             |
| HALF-OPEN → CLOSED | Все 3 probe успешны               |
| HALF-OPEN → OPEN   | Любой probe failed                |

**Пример (Payment → Provider):**

1. Провайдер начал таймаутить
2. CB window заполняется ошибками: 8/10 = 80% > 50%
3. CB → OPEN: новые платежи сразу в retry queue (без HTTP к провайдеру)
4. Через 60с CB → HALF-OPEN: 3 платежа пробуют provider
5. Если 3/3 успешны → CB CLOSED, нормальная работа
6. Если хотя бы 1 failed → CB OPEN, ждём ещё 60с

![Sequence Diagram](../../diagrams/seq/seq-resilience.png)
