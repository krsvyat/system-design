# Context: Payments

## Purpose

Orchestrates payment lifecycle:
- creation,
- fraud check (via Anti-Fraud context),
- reserve/commit (via Wallet context),
- provider routing, status management, and event publishing.
Handles retries and refunds.

## Domain Type

`core`
