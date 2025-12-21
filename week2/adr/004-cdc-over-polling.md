# ADR-004: CDC (Debezium) for Transactional Outbox

## Status

Accepted

## Context

Transactional Outbox pattern requires publishing events from outbox table to Kafka. Two approaches:

**Polling** — scheduled job periodically reads outbox table, publishes to Kafka, marks as sent.

**CDC (Change Data Capture)** — Debezium reads PostgreSQL WAL, streams changes to Kafka automatically.

## Decision

We use **CDC via Debezium** for outbox publishing in both Wallet Service and Transaction Service.

### Why CDC

- **Low latency**: Events published within milliseconds (vs polling interval 100ms-1s)
- **No DB load from polling**: Reads WAL, not table
- **Performance**: Fast fund reservation and status updates

### Why Debezium over Self-built CDC

Alternative: read PostgreSQL replication slot directly without Debezium.

| Aspect           | Debezium                 | Self-built CDC |
| ---------------- | ------------------------ | -------------- |
| Offset tracking  | Kafka Connect manages    | Must implement |
| Failover         | Built-in                 | Must implement |
| Schema evolution | Supported                | Must implement |
| Infrastructure   | Kafka Connect + Debezium | Only Kafka     |

Self-built removes Kafka Connect dependency but requires implementing offset tracking, failover, and schema handling. Debezium is popular and battle-tested.

### Trade-offs

| Aspect         | CDC (Debezium)                       | Polling         |
| -------------- | ------------------------------------ | --------------- |
| Latency        | ~ms                                  | 100ms-1s        |
| Infrastructure | Kafka Connect (with Debezium plugin) | None            |
| Complexity     | Higher                               | Lower           |
| DB load        | Minimal (WAL)                        | Constant SELECT |

## Consequences

**Positive:**

- Near real-time event publishing
- No polling load on database

**Negative:**

- Additional infrastructure (Kafka Connect with Debezium plugin)
- More complex deployment and monitoring
