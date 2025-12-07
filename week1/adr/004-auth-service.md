# ADR-004: Custom Auth Service instead of Keycloak

## Status

Accepted

## Context

We need authentication for mobile and web banking apps. Options:

1. **Keycloak** — open source IdP, OIDC/OAuth2 out of the box
2. **Custom Auth Service** — own implementation

## Decision

We build a custom Auth Service.

## Rationale

Banking has specific requirements that Keycloak doesn't handle well:

| Requirement                  | Keycloak          | Custom                     |
| ---------------------------- | ----------------- | -------------------------- |
| SMS OTP codes                | Plugin, limited   | Full control               |
| Push confirmation            | Hard to integrate | Native                     |
| ESIA (Gosuslugi) integration | Not supported     | Custom integration         |
| Central Bank requirements    | Workarounds       | Built for compliance       |
| Fraud checks on login        | Separate system   | Integrated with Anti-Fraud |
| Custom audit logging         | Standard format   | Our format                 |

Keycloak is designed for standard enterprise SSO. Banking requires:

- Phone number login (not email)
- Multiple MFA methods
- Integration with regulatory systems
- Custom session rules

Auth Service calls Anti-Fraud Context on every login (sync HTTP) to check for suspicious activity (new device, unusual location, etc.).

## Consequences

**Positive:**

- Full control over auth flow
- Easy integration with bank-specific systems
- No external product dependency

**Negative:**

- More development effort
- Security responsibility on us
- Need to implement token management ourselves
