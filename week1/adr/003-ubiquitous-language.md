# ADR-003: Ubiquitous language for core domain terms

## Status

Accepted

## Context

Different teams and systems may use different terms for the same concepts (e.g., Account vs Wallet, Client vs Customer). This leads to confusion in communication and inconsistencies in code.

We need a single agreed-upon vocabulary across all bounded contexts.

## Decision

We adopt the following terms:

| Concept                    | Term         | NOT used                      |
| -------------------------- | ------------ | ----------------------------- |
| Bank's customer            | Customer     | Client, User                  |
| Customer's bank account    | Account      | Wallet                        |
| Temporary balance lock     | Hold         | Block, Reserve, Authorization |
| Final debit from account   | Capture      | Debit, Charge                 |
| Available money on account | Balance      | Amount, Funds                 |
| External payment receiver  | Merchant     | Seller, Vendor, Shop          |
| Message to customer        | Notification | Alert, Message                |

These terms are used consistently in:

- Code (class names, variables, API fields)
- Documentation
- Team communication

## Consequences

**Positive:**

- Clear communication between teams
- Consistent naming in codebase
- Easier onboarding for new team members

**Negative:**

- Requires discipline to enforce
- May conflict with legacy system naming
