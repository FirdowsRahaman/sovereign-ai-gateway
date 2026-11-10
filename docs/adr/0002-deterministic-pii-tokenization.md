# 2. Deterministic Pseudonymization with Ephemeral Session Mapping

Date: 2026-02-12

## Status
Accepted

## Context
GDPR Article 25 requires Data Protection by Design. Simply blocking requests that contain PII causes high false-positive disruptions for customer service and billing workflows.

## Decision
We implement deterministic pseudonymization tokens (`[EMAIL_1]`, `[EU_IBAN_1]`). The raw PII is stripped before sending to the model, and replaced into the generated response within the internal perimeter before responding to the user.

## Consequences
- Complies with GDPR minimization while enabling the model to process contextual relationships.
- Guarantees third-party LLM providers never see European customer PII.
