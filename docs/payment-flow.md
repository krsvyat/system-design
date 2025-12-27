# Payment Flow

Система обработки платежей с eventual consistency, Saga, Transactional Outbox и CQRS.

## Bounded Contexts

| Context | Ответственность | Команды | Слушает | Публикует |
|---------|-----------------|---------|---------|-----------|
| Wallet | Управление балансом, резервирование | ReserveFunds, CommitFunds, ReleaseFunds | PaymentCompleted, PaymentFailed | PaymentInitiated |
| Transaction | Взаимодействие с провайдером | InitiatePayment | PaymentInitiated, ProviderCallbackReceived | PaymentCompleted, PaymentFailed |
| Callback | Приём callback от провайдера | HandleCallback | — | ProviderCallbackReceived |
| Query | Денормализованные проекции | — | PaymentInitiated, PaymentCompleted, PaymentFailed | — |

## Процесс исполнения

### Success

1. POST /payments -> API Gateway -> BFF (amount, walletId, currency, recipient)
2. POST /wallets/{walletId}/reservations -> Wallet Service
3. Wallet Service в одной транзакции:
   - увеличивает wallets.reserved
   - создаёт wallet_transactions (type=RESERVE, status=COMPLETED)
   - пишет в wallet_outbox событие PaymentInitiated
4. Kafka Connect читает WAL, отправляет PaymentInitiated в Kafka
5. Payment Service читает PaymentInitiated, создаёт payments (status=PROCESSING)
6. Payment Service вызывает External Provider, получает 202 Accepted с providerTxnId
7. Payment Service обновляет payments.provider_txn_id
8. External Provider делает callback -> API Gateway -> Callback Service (status=SUCCESS)
9. Callback Service сохраняет callback, пишет в outbox ProviderCallbackReceived
10. Kafka Connect отправляет ProviderCallbackReceived в Kafka
11. Payment Service обновляет payments (status=COMPLETED), пишет PaymentCompleted
12. Kafka Connect отправляет PaymentCompleted в Kafka
13. Wallet Service: уменьшает reserved, уменьшает balance, создаёт wallet_transactions (type=COMMIT)
14. Query Service обновляет payment_projections

### Failure

1-7. Аналогично Success

8. Provider callback с status=FAILED или timeout
9. ProviderCallbackReceived с status=FAILED. При timeout — Payment Service сам создаёт PaymentFailed
10-12. Аналогично Success, но PaymentFailed
13. Wallet Service: уменьшает reserved, создаёт wallet_transactions (type=RELEASE)
14. Query Service обновляет payment_projections

## Saga (Хореография)

Нет центрального оркестратора — сервисы слушают события и сами решают, что делать.

### Шаг 1: Reserve (Wallet Service)

- **Транзакция:** увеличить reserved, создать wallet_transactions (RESERVE), записать в outbox (PaymentInitiated)
- **Компенсация:** уменьшить reserved, создать wallet_transactions (RELEASE)

### Шаг 2: Process (Payment Service)

- **Транзакция:** создать payments (PROCESSING), вызвать провайдера, сохранить provider_txn_id
- **Компенсация:** нет. Провайдер сам возвращает SUCCESS или FAILED

### Завершение (Wallet Service)

- PaymentCompleted -> COMMIT: уменьшить reserved, уменьшить balance, создать wallet_transactions (COMMIT)
- PaymentFailed -> RELEASE: уменьшить reserved, создать wallet_transactions (RELEASE)

## Transactional Outbox

| Сервис | Outbox таблица |
|--------|----------------|
| Wallet Service | wallet_outbox |
| Payment Service | payment_outbox |
| Callback Service | callback_outbox |

**Зачем Callback Service использует outbox:**

Без outbox: получил callback, ответил 200 OK, упал до отправки в Kafka — событие потеряно.

С outbox: сохранение и запись в outbox в одной транзакции, CDC гарантирует доставку.

**Polling vs CDC:** см. [ADR-007](../adr/007-cdc-over-polling.md)

## CQRS

- **Write:** Wallet, Transaction, Callback — каждый пишет в свою БД
- **Read:** Query Service — читает из payment_projections

## Idempotency

Все проверки хранят состояние в PostgreSQL:

| Сервис | Механизм |
|--------|----------|
| Wallet | SELECT WHERE payment_id = ? AND type = 'RESERVE' перед созданием |
| Transaction | UNIQUE constraint на payment_id |
| Callback | UNIQUE constraint на provider_txn_id |
