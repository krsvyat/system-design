# Payment Platform

Система обработки платежей с eventual consistency, Saga, Transactional Outbox и CQRS.

## Архитектура

### C2 Container Diagram

![C2 Container](diagrams/c2.puml)

### C3 Component Diagrams

#### Wallet Service

![C3 Wallet](diagrams/c3-wallet.puml)

#### Transaction Service

![C3 Transaction](diagrams/c3-transaction.puml)

#### Query Service

![C3 Query](diagrams/c3-query.puml)

## Sequence Diagrams

### Success Scenario

![Sequence Success](diagrams/seq-success.puml)

### Failure Scenario

![Sequence Failure](diagrams/seq-failure.puml)

```plantuml
!include diagrams/seq-failure.puml
```

Отличия от success:

- Provider callback со статусом FAILED
- Transaction пишет PaymentFailed в outbox
- Wallet делает компенсацию — release reserved funds
- Timeout обрабатывается аналогично — scheduler в Transaction Service создаёт PaymentFailed

### Callback Flow

Отдельная диаграмма для callback flow не создавалась, т.к. он полностью виден в seq-success и seq-failure.

