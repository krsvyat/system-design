# ADR-002: Choreography via Kafka for Payment Saga

## Status

Accepted

## Context

The payment platform requires coordination of payment flow across multiple services (Wallet, Transaction, Callback). Two approaches:

**Orchestration** — central coordinator (e.g., Temporal, Camunda) manages the flow, calls services in sequence, handles retries and compensation.

**Choreography** — services communicate via events through message broker (Kafka), each service reacts to events and publishes new ones.

### Task Contradiction

The task contains a contradiction:

- Section 2: "Orchestrator вызывает Wallet Service и Transaction Service по командам"
- Section 2: "Transaction Service: Получает событие PaymentInitiated из брокера"

These are mutually exclusive. We follow the second statement because:

1. Task explicitly requires Kafka/RabbitMQ events
2. Task requires Transactional Outbox pattern (events published to broker)
3. Most of the task describes event-driven flow

## Decision

We use **Choreography** via Kafka for the payment saga.

**BFF (Backend for Frontend)** service:

- Accepts client requests
- Calls `Wallet.reserveFunds()` — sync HTTP
- Reads payment status and history from Query Service (CQRS)
- Does NOT call Transaction Service directly

**Kafka** handles the rest.

### Why Choreography

- **Matches task requirements**: Task explicitly requires Kafka events and Transactional Outbox
- **Simpler infrastructure**: No Temporal/Camunda server + database

### Why Not Full Orchestration (Temporal, Camunda, etc.)

After BFF calls `reserveFunds()`, it returns response to client. The rest happens async via Kafka. BFF would be idle waiting — workflow engine is redundant.

| Option                 | Why Not                                                         |
| ---------------------- | --------------------------------------------------------------- |
| **Temporal**           | Additional infrastructure (server + DB), overkill for this flow |
| **Camunda**            | BPMN complexity, not required by task                           |
| **AWS Step Functions** | Workflows in JSON                                               |

## Consequences

**Positive:**

- No additional infrastructure for workflow engine
- Matches task requirements (Outbox, Kafka)

**Negative:**

- No central visibility of saga state (need good logging/tracing)
- Hard to debug
