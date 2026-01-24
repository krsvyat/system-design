# Масштабирование и отказоустойчивость

## Горизонтальное масштабирование сервисов

Все сервисы stateless — масштабируются добавлением реплик: API Gateway, BFF, Wallet, Payment, Callback, Query, Notification.

## Масштабирование Kafka

Добавляем партиции → можем добавить больше реплик сервисов.

Ограничение: одну партицию читает одна реплика. 12 партиций = максимум 12 реплик, 13-я простаивает.

Топики и партиционирование: см. [messaging.md](../messaging.md#топики).

### Consumer Groups

Каждый сервис — отдельная consumer group. Это значит:

- Wallet и Query читают из одного топика независимо друг от друга
- Если Query отстаёт — это не блокирует Wallet

| Consumer Group       | Читает из                                                |
| -------------------- | -------------------------------------------------------- |
| payment-service      | payments.initiated, callbacks.received, payments.retry   |
| wallet-service       | payments.completed, payments.failed, customer-events     |
| query-service        | payments.initiated, payments.completed, payments.failed  |
| notification-service | payments.completed, payments.failed, notifications.retry |

## Отказоустойчивость

### Падение пода

**HTTP сервисы** — load balancer направляет трафик на живые поды.

**Kafka consumers** — rebalance:

1. Kafka обнаруживает что consumer не отвечает (~10 секунд)
2. Партиции упавшего пода автоматически перераспределяются между живыми репликами

### Недоступность провайдера

См. [Resilience](resilience.md#сценарий-провайдер-недоступен).

### Рост нагрузки на Query Service

| Защита     | Как работает               |
| ---------- | -------------------------- |
| Rate limit | Ограничение RPS на Gateway |
| Кэш        | Redis кэш истории платежей |
