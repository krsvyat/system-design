# ADR-006: Use PostgreSQL for Query Service Read Model

## Status

Accepted

## Context

The Query Service implements the read side of CQRS pattern. It consumes events from Kafka (PaymentInitiated, PaymentCompleted, PaymentFailed) and builds denormalized projections for querying.

Requirements:

- Fast reads for payment status lookup by ID
- List payments by user with filtering and pagination
- Payment history with date range queries
- Consistency with event order (eventual consistency acceptable)

## Decision

We will use **PostgreSQL** for the Query Service read model.

### Why PostgreSQL

- **OLTP workload**: Our queries are lookups by ID and lists by user_id — PostgreSQL handles this perfectly with indexes
- **Team familiarity**: Already used for Wallet/Transaction DBs
- **Rich query capabilities**: SQL aggregates, joins if needed

### Options Considered

| Option            | Why Not                                                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Elasticsearch** | Designed for full-text search (e.g. "find payments by description"), overkill for simple lookups by ID/user_id. Also has eventual consistency (refresh interval ~1s) which complicates reasoning about read-after-write |
| **ClickHouse**    | OLAP database for analytics (aggregations over millions of rows), our queries are OLTP — simple lookups by ID and user_id |

## Consequences

**Positive:**

- Consistent technology stack (all services use PostgreSQL)
- Rich query capabilities out of the box
