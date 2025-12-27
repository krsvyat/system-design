# Payment Platform

Архитектура платёжной платформы.

## Диаграммы

### Context & C4

- [Context Map](diagrams/context/context.drawio.png)
- [C1 System Context](diagrams/c4/c1.png) | [source](diagrams/c4/c1.puml)
- [C2 Containers](diagrams/c4/c2.png) | [source](diagrams/c4/c2.puml)

### C3 Components

- [Wallet Service](diagrams/c4/c3-wallet.png) | [source](diagrams/c4/c3-wallet.puml)
- [Payment Service](diagrams/c4/c3-payment.png) | [source](diagrams/c4/c3-payment.puml)
- [Query Service](diagrams/c4/c3-query.png) | [source](diagrams/c4/c3-query.puml)

### Sequence

- [Success Flow](diagrams/seq/seq-success.png) | [source](diagrams/seq/seq-success.puml)
- [Failure Flow](diagrams/seq/seq-failure.png) | [source](diagrams/seq/seq-failure.puml)

### ERD

- [Wallet DB](diagrams/erd/erd-wallet.png)
- [Payment DB](diagrams/erd/erd-payment.png)
- [Callback DB](diagrams/erd/erd-callback.png)
- [Query DB](diagrams/erd/erd-query.png)

## Документация

- [Payment Flow](docs/payment-flow.md) — Saga, Outbox, CQRS, Idempotency
- [API](docs/api.md) — External и Internal API
- [Events](docs/events.md) — Kafka events schema
- [Database](docs/database.md) — ERD и схемы таблиц
- [Integration Patterns](docs/integration-patterns.md) — sync/async, REST/gRPC
- [Messaging](docs/messaging.md) — Kafka vs RabbitMQ
- [API Gateway](docs/api-gateway.md) — Kong
- [Identifiers](docs/identifiers.md) — UUIDv7

## ADR

- [001 ADR Format](adr/001-adr-format.md)
- [002 Bounded Contexts](adr/002-bounded-contexts.md)
- [003 Ubiquitous Language](adr/003-ubiquitous-language.md)
- [004 Auth Service](adr/004-auth-service.md)
- [005 Choreography over Orchestration](adr/005-choreography-over-orchestration.md)
- [006 Query Service Database](adr/006-query-service-database.md)
- [007 CDC over Polling](adr/007-cdc-over-polling.md)

## Прочее

- [Glossary](glossary.md)
- [Contexts](contexts/)
