# API

## External API (BFF)

### Create Payment

```
POST /payments
```

Request:
```json
{
  "walletId": "uuid",
  "amount": 1000,
  "currency": "RUB",
  "recipient": {
    "accountNumber": "40817810099910004312",
    "bankBic": "044525225",
    "name": "Иванов Иван Иванович"
  }
}
```

Response `202 Accepted`:
```json
{
  "paymentId": "uuid",
  "status": "RESERVED"
}
```

### Get Payment Status

```
GET /payments/{paymentId}
```

Response `200 OK`:
```json
{
  "paymentId": "uuid",
  "walletId": "uuid",
  "userId": "uuid",
  "amount": 1000,
  "currency": "RUB",
  "status": "COMPLETED",
  "errorCode": null,
  "providerTxnId": "uuid",
  "createdAt": "2024-01-15T10:00:00Z",
  "completedAt": "2024-01-15T10:00:05Z"
}
```

Status values: `RESERVED`, `PROCESSING`, `COMPLETED`, `FAILED`

### Get Payment History

```
GET /payments?walletId={walletId}&limit=20&offset=0
```

Response `200 OK`:
```json
{
  "payments": [...],
  "total": 100,
  "limit": 20,
  "offset": 0
}
```

## Internal API

### Wallet Service

**Reserve Funds**

```
POST /wallets/{walletId}/reservations
```

Request:
```json
{
  "paymentId": "uuid",
  "amount": 1000,
  "currency": "RUB"
}
```

Response `201 Created`:
```json
{
  "reservationId": "uuid",
  "paymentId": "uuid",
  "status": "RESERVED"
}
```

**Commit Funds** — через Kafka event (PaymentCompleted)

**Release Funds** — через Kafka event (PaymentFailed)

### Payment Service

Не имеет HTTP эндпоинтов. Подписан на PaymentInitiated, ProviderCallbackReceived.

### Callback Service

```
POST /callbacks
```

Request (from Payment Provider):
```json
{
  "providerTxnId": "uuid",
  "status": "SUCCESS",
  "timestamp": "2024-01-15T10:00:05Z",
  "signature": "..."
}
```

Response `200 OK`:
```json
{
  "received": true
}
```
