# ADR-001: Use ADR format for architecture decisions

## Status

Accepted

## Context

We need a consistent way to document architecture decisions in the project. Decisions made without documentation are easily forgotten, misunderstood, or reversed without understanding the original reasoning.

Requirements:

- Lightweight format that lives in the repository
- Easy to write and read
- Captures the "why" behind decisions
- Tracks decision lifecycle (proposed → accepted → superseded)

## Decision

We will use Architecture Decision Records (ADR) in the format proposed by [Michael Nygard](https://www.cognitect.com/blog/2011/11/15/documenting-architecture-decisions).

### Format

Each ADR is a markdown file with the following structure:

| Section          | Purpose                                                               |
| ---------------- | --------------------------------------------------------------------- |
| **Title**        | `ADR-XXX: Short decision description`                                 |
| **Status**       | `Proposed` / `Accepted` / `Deprecated` / `Superseded by ADR-XXX`      |
| **Context**      | What is the issue? What forces are at play? Why do we need to decide? |
| **Decision**     | What is our decision? Be specific.                                    |
| **Consequences** | What are the results? Both positive and negative.                     |

### File naming

```
adr/
├── 001-adr-format.md
├── 002-bounded-context-boundaries.md
├── 003-event-driven-communication.md
└── ...
```

Format: `XXX-<short-name>.md` where XXX is a sequential number.

### Guidelines

- One decision per ADR
- 1-2 pages maximum
- Write for a future developer who doesn't know the context
- Numbers are never reused
- Old decisions are marked superseded, not deleted

## Consequences

**Positive:**

- Decisions are documented and searchable
- New team members understand historical context
- Prevents re-discussing already decided topics
- Lives with the code in version control

**Negative:**

- Overhead to write ADRs for every decision
- Risk of ADRs becoming outdated if not maintained

**Neutral:**

- Team needs to agree on what qualifies as an "architecture decision"
