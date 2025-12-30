# Messaging

Sync/async паттерны, события, топики.

## Протоколы

### Sync

**Client → BFF (REST)** — пользователь ждёт ответа. REST потому что браузер, OpenAPI spec, HTTP cache.

**BFF → Wallet (HTTP)** — reserve должен завершиться до продолжения, иначе двойное списание.

**BFF → Query (HTTP)** — пользователь ждёт статус платежа.

**Payment → Anti-Fraud (gRPC)** — блокируем платёж при fraud. gRPC потому что скорость критична.

**Payment → Provider (HTTP)** — ждём providerTxnId для дальнейшей обработки.

### Async (Kafka)

**Wallet → Payment** — `PaymentInitiated` после резервирования.

**Callback Service → Payment** — `ProviderCallbackReceived` после получения callback от провайдера.

**Payment → Wallet** — `PaymentCompleted`/`PaymentFailed` для commit/release.

**Payment → Query** — все payment events для read model.

**Payment → Notification** — `PaymentCompleted`/`PaymentFailed`. Скорость не критична, SMS/push могут тормозить.

**Payment → Merchant Callback** — `PaymentCompleted`/`PaymentFailed`. Мерчант может быть недоступен, платёж не должен от него зависеть.

**Payment → Core Banking** — `PaymentCompleted` для бухучёта.

**Payment → Anti-Fraud** — все payment events для ML и velocity checks.

**Payment → DWH** — все события для аналитики.

**Customer → Wallet** — `CustomerCreated` для создания кошелька при регистрации.

Почему Kafka, а не sync с 202: при сбое консьюмера событие подождёт в Kafka. При sync — потеряем.

## Топики

| Топик             | Partition Key   | События                                           | Консьюмеры                                                                             |
| ----------------- | --------------- | ------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `payment-events`  | payment_id      | PaymentInitiated, PaymentCompleted, PaymentFailed | Payment, Query, Wallet, Notification, Merchant Callback, Core Banking, Anti-Fraud, DWH |
| `callback-events` | provider_txn_id | ProviderCallbackReceived                          | Payment                                                                                |
| `customer-events` | user_id         | CustomerCreated                                   | Wallet                                                                                 |

Kafka отправляет сообщения с одинаковым ключом в одну партицию. Внутри партиции порядок гарантирован.

**Обработка ошибок в консьюмере**

Если консьюмер упал при обработке `PaymentInitiated`, но успешно обработал `PaymentCompleted` — при retry первого события запись уже существует.

Решение: upsert с проверкой timestamp — см. [Idempotency](payment/idempotency.md#query-service).

## События

См. [ADR-006](../adr/006-kafka.md) — почему Kafka.

### PaymentInitiated

Публикует: Wallet Service (после резервирования)

| Поле                    | Тип    | Описание                     |
| ----------------------- | ------ | ---------------------------- |
| paymentId               | string | ID платежа                   |
| walletId                | string | ID кошелька                  |
| userId                  | string | ID пользователя              |
| amount                  | number | Сумма в минимальных единицах |
| currency                | string | Код валюты                   |
| recipient.accountNumber | string | Номер счёта                  |
| recipient.bankBic       | string | БИК банка                    |
| recipient.name          | string | ФИО получателя               |
| createdAt               | string | Время создания               |

### PaymentCompleted

Публикует: Payment Service (после успешного callback)

| Поле          | Тип    | Описание                    |
| ------------- | ------ | --------------------------- |
| paymentId     | string | ID платежа                  |
| providerTxnId | string | ID транзакции от провайдера |
| completedAt   | string | Время завершения            |

### PaymentFailed

Публикует: Payment Service (после неуспешного callback или таймаута)

| Поле          | Тип    | Описание                         |
| ------------- | ------ | -------------------------------- |
| paymentId     | string | ID платежа                       |
| providerTxnId | string | ID транзакции (null при timeout) |
| errorCode     | string | Код ошибки                       |
| completedAt   | string | Время завершения                 |

### ProviderCallbackReceived

Публикует: Callback Service (после получения callback)

| Поле          | Тип    | Описание                    |
| ------------- | ------ | --------------------------- |
| providerTxnId | string | ID транзакции от провайдера |
| status        | string | SUCCESS, FAILED             |
| receivedAt    | string | Время получения             |

### CustomerCreated

Публикует: Customer Service (после регистрации)

| Поле      | Тип    | Описание            |
| --------- | ------ | ------------------- |
| userId    | string | ID пользователя     |
| currency  | string | Валюта по умолчанию |
| createdAt | string | Время регистрации   |
