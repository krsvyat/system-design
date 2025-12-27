# Database

## Wallet DB

![ERD Wallet](../diagrams/erd/erd-wallet.png)

### wallets

| Field | Type | Описание |
|-------|------|----------|
| id | uuid | PK |
| user_id | uuid | Владелец кошелька |
| balance | bigint | Доступный баланс в минимальных единицах |
| reserved | bigint | Зарезервированная сумма |
| currency | text | Код валюты (RUB, USD, ...) |
| created_at | timestamptz | Время создания |

### wallet_transactions

| Field | Type | Описание |
|-------|------|----------|
| id | uuid | PK |
| wallet_id | uuid | FK -> wallets |
| payment_id | uuid | ID платежа (защита от повторного резервирования) |
| amount | bigint | Сумма |
| type | text | RESERVE, COMMIT, RELEASE |
| status | text | PENDING, COMPLETED, FAILED |
| created_at | timestamptz | Время создания |

### wallet_outbox

| Field | Type | Описание |
|-------|------|----------|
| id | uuid | PK |
| payment_id | uuid | ID платежа |
| event_type | text | PaymentInitiated |
| payload | jsonb | Данные события |
| created_at | timestamptz | Время создания |

## Payment DB

![ERD Payment](../diagrams/erd/erd-payment.png)

### payments

| Field | Type | Описание |
|-------|------|----------|
| id | uuid | PK |
| payment_id | uuid | ID платежа из Wallet (защита от дублей) |
| provider_txn_id | text | ID транзакции от провайдера |
| amount | bigint | Сумма |
| currency | text | Код валюты |
| status | text | PROCESSING, COMPLETED, FAILED |
| error_code | text | Код ошибки |
| created_at | timestamptz | Время создания |

### payment_outbox

| Field | Type | Описание |
|-------|------|----------|
| id | uuid | PK |
| payment_id | uuid | ID платежа |
| event_type | text | PaymentCompleted, PaymentFailed |
| payload | jsonb | Данные события |
| created_at | timestamptz | Время создания |

## Callback DB

![ERD Callback](../diagrams/erd/erd-callback.png)

### callbacks

| Field | Type | Описание |
|-------|------|----------|
| id | uuid | PK |
| provider_txn_id | text | ID транзакции от провайдера |
| status | text | SUCCESS, FAILED |
| raw_payload | jsonb | Сырой ответ от провайдера |
| received_at | timestamptz | Время получения |

### callback_outbox

| Field | Type | Описание |
|-------|------|----------|
| id | uuid | PK |
| provider_txn_id | text | ID транзакции от провайдера |
| event_type | text | ProviderCallbackReceived |
| payload | jsonb | Данные события |
| created_at | timestamptz | Время создания |

## Query DB

![ERD Query](../diagrams/erd/erd-query.png)

### payment_projections

| Field | Type | Описание |
|-------|------|----------|
| payment_id | uuid | PK |
| wallet_id | uuid | ID кошелька |
| user_id | uuid | ID пользователя |
| amount | bigint | Сумма |
| currency | text | Код валюты |
| status | text | RESERVED, PROCESSING, COMPLETED, FAILED |
| error_code | text | Код ошибки |
| provider_txn_id | text | ID транзакции от провайдера |
| created_at | timestamptz | Время создания |
| completed_at | timestamptz | Время завершения |

### Индексы

- `payment_id` — PK
- `CREATE INDEX idx_payment_projections_wallet_created ON payment_projections (wallet_id, created_at DESC);`

### Запросы

- `GET /payments/{paymentId}` -> `SELECT * FROM payment_projections WHERE payment_id = ?`
- `GET /payments?walletId={walletId}` -> `SELECT * FROM payment_projections WHERE wallet_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?`
