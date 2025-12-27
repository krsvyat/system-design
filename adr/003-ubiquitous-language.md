# ADR-003: Ubiquitous language for core domain terms

## Status

Accepted

## Context

Different teams and systems may use different terms for the same concepts (e.g., Account vs Wallet, Client vs Customer). This leads to confusion in communication and inconsistencies in code.

We need a single agreed-upon vocabulary across all bounded contexts.

## Decision

### Domain Terms

| Concept                    | Term         | NOT used                      |
| -------------------------- | ------------ | ----------------------------- |
| Bank's customer            | Customer     | Client, User                  |
| Customer's money storage   | Wallet       | Account, Balance Account      |
| Temporary balance lock     | Reserve      | Hold, Block, Authorization    |
| Final debit from wallet    | Commit       | Capture, Debit, Charge        |
| Cancel reservation         | Release      | Rollback, Unblock             |
| Available money            | Balance      | Amount, Funds                 |
| External payment receiver  | Merchant     | Seller, Vendor, Shop          |
| Message to customer        | Notification | Alert, Message                |
| Payment processing unit    | Payment      | Transaction, Transfer         |

### Service Names

| Service              | Responsibility                              |
| -------------------- | ------------------------------------------- |
| Wallet Service       | Balances, reservations, commits, releases   |
| Payment Service      | Payment lifecycle, provider integration     |
| Callback Service     | Receiving callbacks from external providers |
| Query Service        | CQRS read model for payment status          |
| Notification Service | SMS, push, email to customers               |

These terms are used consistently in:

- Code (class names, variables, API fields)
- Diagrams (C4, sequence, ERD)
- Documentation
- Team communication

## Consequences

**Positive:**

- Clear communication between teams
- Consistent naming in codebase and diagrams
- Easier onboarding for new team members
- Single source of truth for terminology

**Negative:**

- Requires discipline to enforce
- May conflict with legacy system naming
