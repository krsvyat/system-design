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

**Reserve**

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

**Commit** — через Kafka event (PaymentCompleted)

**Release** — через Kafka event (PaymentFailed)

### Payment Service

Не имеет HTTP эндпоинтов. Подписан на события:
- `PaymentInitiated` → начать обработку
- `ProviderCallbackReceived` → обновить статус

### Query Service

**Get Payment**

```
GET /payments/{paymentId}
```

**Get Payment History**

```
GET /payments?walletId={walletId}&limit=20&offset=0
```

Read-only проекции из `payment_projections`.

### Anti-Fraud Service (gRPC)

```protobuf
service AntiFraud {
  rpc CheckPayment(CheckRequest) returns (CheckResponse);
}

message CheckRequest {
  string payment_id = 1;
  string user_id = 2;
  string wallet_id = 3;
  int64 amount = 4;
  string currency = 5;
}

message CheckResponse {
  Decision decision = 1;  // ALLOW, DENY
  string reason = 2;
}
```

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

## Provider API (External)

API внешних платёжных провайдеров, которые мы вызываем.

### Create Payment

```
POST /payments
```

Request:
```json
{
  "merchantId": "our-bank-id",
  "amount": 1000,
  "currency": "RUB",
  "recipient": {...},
  "callbackUrl": "https://api.bank.com/callbacks"
}
```

Response `202 Accepted`:
```json
{
  "providerTxnId": "provider-uuid",
  "status": "PENDING"
}
```

### Get Status

```
GET /transactions/{providerTxnId}/status
```

Response:
```json
{
  "providerTxnId": "provider-uuid",
  "status": "SUCCESS | FAILED | PENDING"
}
```

### Reversal

```
POST /reversals/{providerTxnId}
```

Response `200 OK` или `400 Bad Request` (cannot reverse)
