# Integration Patterns

Выбор sync/async, REST/gRPC, eventual/strong consistency для каждого взаимодействия.

## Client -> API Gateway -> BFF -> Payments

| Критерий | Решение | Обоснование |
|----------|---------|-------------|
| sync/async | sync | Пользователь ждет ответа сразу |
| REST/gRPC | REST | Браузер и mobile лучше поддерживают HTTP, API Gateway работает с HTTP cache/firewalls, легче отдать OpenAPI spec |
| Consistency | strong | Данные только в Payments DB |

## Payments <-> Wallet (резервирование/коммит)

| Критерий | Решение | Обоснование |
|----------|---------|-------------|
| sync/async | sync | Reserve/commit должен быть синхронным, payments не может продолжить без ответа. Если нет денег — сразу отказ |
| REST/gRPC | gRPC | Внутренний сервис, скорость важна |
| Consistency | strong | Reserve должен быть записан в БД до продолжения платежа, иначе возможно двойное списание |

## Payments -> Anti-Fraud/Scoring

| Критерий | Решение | Обоснование |
|----------|---------|-------------|
| sync/async | sync | Payments должен сразу прекращать платеж при подозрении на мошенничество |
| REST/gRPC | gRPC | Внутренний сервис, скорость важна |
| Consistency | strong | Payments ждет решения от Anti-Fraud |

## Payments -> Core Banking ACL

| Критерий | Решение | Обоснование |
|----------|---------|-------------|
| sync/async | async | Запись в бухучет не требует скорости |
| REST/gRPC | async (Kafka) | - |
| Consistency | eventual | С гарантией доставки |

## Payments -> Notifications

| Критерий | Решение | Обоснование |
|----------|---------|-------------|
| sync/async | async | Не важна скорость доставки, нельзя гарантировать быстрый ответ от SMS/email/push. При sync можно потерять сообщение, если Notifications упадет |
| REST/gRPC | async (Kafka) | - |
| Consistency | eventual | - |

## Payments -> Callbacks (мерчантам)

| Критерий | Решение | Обоснование |
|----------|---------|-------------|
| sync/async | async | Мерчант — внешняя система, может быть недоступна, платеж не должен зависеть от мерчанта |
| REST/gRPC | async (Kafka) | - |
| Consistency | eventual | - |

## Payments -> DWH/Аналитика

| Критерий | Решение | Обоснование |
|----------|---------|-------------|
| sync/async | async | Отослать и забыть |
| REST/gRPC | async (Kafka) | - |
| Consistency | eventual | - |
