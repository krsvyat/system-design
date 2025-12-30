# Idempotency

Идемпотентность на всех критичных шагах платёжного процесса.

## Wallet Service

### Reserve

- `payment_id` в таблице `reservations` имеет UNIQUE constraint
- При попытке создать вторую резервацию с тем же `payment_id` — БД откажет (duplicate key)
- Код ловит ошибку и возвращает существующую резервацию
- Результат: одна резервация на платёж

### Commit

- UPDATE только записей со статусом `RESERVED`
- Повторный commit → запись уже `COMMITTED`, UPDATE затронет 0 строк
- Баланс меняется только при успешном UPDATE

### Release

- Аналогично commit: UPDATE только для статуса `RESERVED`
- Повторный release → no-op

## Payment Service

### Создание платежа

- Получает `PaymentInitiated` из Kafka
- `payment_id` — Primary Key в таблице `payments` (PK гарантирует уникальность)
- Дубликат события → INSERT fails (duplicate key), платёж уже существует

### Обработка callback

- `provider_txn_id` в таблице `callbacks` имеет UNIQUE constraint
- При получении callback: INSERT в callbacks
- Если INSERT fails (duplicate key) → callback уже обработан → пропускаем
- Если INSERT ok → публикуем `ProviderCallbackReceived`

### Callback с неизвестным payment

- Ищем платёж по `provider_txn_id` в таблице `payments`
- Не нашли → callback пришёл раньше, чем мы сохранили `provider_txn_id` (race condition), или баг провайдера
- Решение: retry с backoff, если после N попыток не нашли → логируем и отбрасываем

### Обновление статуса

- UPDATE только если текущий статус = `PROCESSING`
- Если статус уже `COMPLETED` или `FAILED` → UPDATE затронет 0 строк
- Проверяем количество затронутых строк, не полагаемся на отсутствие ошибки

## Query Service

**Проблема:** при сбое обработки события может прийти retry после более нового события.

Без защиты: перезапишем COMPLETED → INITIATED (откат статуса).

**Решение:**

1. **Дедупликация по event_id** — таблица `processed_events` хранит ID обработанных событий. Перед обработкой проверяем: если event_id уже есть — пропускаем.

2. **Проверка timestamp при UPDATE** — если в БД уже есть запись с `updated_at: 10:00:05`, а мы пытаемся записать событие с `10:00:00` — UPDATE не произойдёт (WHERE updated_at < event_timestamp).

Таблица `processed_events` очищается по TTL (7 дней) — старые события уже не придут повторно.
