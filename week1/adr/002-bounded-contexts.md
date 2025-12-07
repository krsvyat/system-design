# ADR-002: Define bounded contexts for the bank system

## Status

Accepted

## Context

We are designing a payment system for a bank. We need to define clear boundaries between different parts of the domain to:

- Enable independent development by separate teams
- Reduce coupling between subsystems
- Establish clear ownership and responsibilities
- Define integration points

The bank has existing systems (Core Banking as legacy) and needs to integrate with external payment providers.

## Decision

We define the following bounded contexts:

| Context                  | Domain Type           | Responsibility                                  |
| ------------------------ | --------------------- | ----------------------------------------------- |
| **Customer**             | Supporting            | Customer identity and contractual relationships |
| **Account**               | Core                  | Account management, balances, holds             |
| **Payments**             | Core                  | Payment lifecycle from creation to final status |
| **Core Banking**         | Supporting (legacy)   | General ledger and accounting entries           |
| **Anti-Fraud / Scoring** | Core                  | Real-time fraud detection and risk assessment   |
| **Notifications**        | Generic               | Customer notifications (SMS/Push/Email)         |
| **Callbacks**            | Supporting (optional) | Notifying merchants about payment status        |

Detailed descriptions of each context are in `contexts/` folder.

## Consequences

**Positive:**

- Improved system flexibility and adaptability to change
- Independent scalability of individual contexts
- Reduced coupling between system components

**Negative:**

- Refactoring resources
