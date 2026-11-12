# Sovereign AI Gateway (EU AI Act & GDPR Compliance Proxy) 

<p align="left">
  <img src="https://img.shields.io/badge/Compliance-EU%20AI%20Act%20Article%2012%20%26%2015-10B981?style=flat-square" alt="EU AI Act">
  <img src="https://img.shields.io/badge/Privacy-GDPR%20by%20Design-0EA5E9?style=flat-square" alt="GDPR">
  <a href="EU_AI_ACT_TECHNICAL_DOCUMENTATION.md"><img src="https://img.shields.io/badge/Documentation-Annex%20IV-8B5CF6?style=flat-square" alt="Annex IV"></a>
  <a href="docs/adr/"><img src="https://img.shields.io/badge/Architecture-ADRs-F59E0B?style=flat-square" alt="ADRs"></a>
  <img src="https://img.shields.io/badge/Standard-OpenAI%20%2F%20vLLM%20Compatible-blue?style=flat-square" alt="OpenAI Compatible">
</p>

An enterprise-grade reverse proxy and guardrails gateway that sits between client applications and Large Language Models (LLMs). Automatically enforces **GDPR PII pseudonymization**, **EU AI Act Article 12 tamper-evident audit logging**, and **data residency controls** across European cloud regions.

---

## Table of Contents
- [Why an EU Sovereign AI Gateway?](#why-an-eu-sovereign-ai-gateway)
- [Architecture](#architecture)
- [Key Features](#key-features)
- [Quick Start](#quick-start)
- [API Usage](#api-usage)
- [Architecture Decision Records (ADRs)](#architecture-decision-records)
- [License](#license)

---

## Why an EU Sovereign AI Gateway?

Under **Regulation (EU) 2024/1689 (EU AI Act)** and the **GDPR**, European companies cannot send raw customer personal data (IBANs, emails, passports) to unvetted cloud models without risk of massive non-compliance fines (up to €35M or 7% of global annual turnover).

The Sovereign AI Gateway solves this by acting as an in-region privacy buffer:
1. **GDPR PII Anonymization**: Automatically redacts European personal identifiers into tokens before the prompt leaves the secure boundary.
2. **EU AI Act Article 12 Logging**: Records every interaction with SHA-256 cryptographic verification hashes to immutable storage.
3. **OpenAI / vLLM Drop-In Compatibility**: Acts as a transparent drop-in replacement (`/v1/chat/completions`) for existing client applications.

---

## Architecture

```
Client Application (Web / Backend / Agent)
                     │
                     ▼
       ┌───────────────────────────┐
       │   Sovereign AI Gateway    │
       │  (AWS Frankfurt VPC)      │
       ├───────────────────────────┤
       │ 1. GDPR PII Scrubbing     │ ──▶ Replaces IBANs, Emails with Tokens
       │ 2. Audit Trail Hashing    │ ──▶ Generates SHA-256 Event Record
       │ 3. Region Guardrails      │ ──▶ Restricts egress outside EEA
       └───────────────────────────┘
                     │
                     ▼ (Sanitized Prompt)
       ┌───────────────────────────┐
       │ European Model Inference  │
       │ (Mistral AI Paris / vLLM) │
       └───────────────────────────┘
                     │
                     ▼ (Sanitized Response)
       ┌───────────────────────────┐
       │   Response Deanonymizer   │ ──▶ Restores PII inside customer boundary
       └───────────────────────────┘
                     │
                     ▼
               Final Response
```

---

## Quick Start

1. **Clone & Run with Docker**:
   ```bash
   git clone https://github.com/FirdowsRahaman/sovereign-ai-gateway.git
   cd sovereign-ai-gateway
   docker build -t sovereign-ai-gateway .
   docker run -p 8000:8000 sovereign-ai-gateway
   ```

2. **Or Run Locally with Python**:
   ```bash
   pip install -r requirements.txt
   python -m uvicorn src.gateway.server:app --port 8000
   ```

---

## API Usage

Because the gateway exposes the standard `/v1/chat/completions` route, point any OpenAI SDK client directly to it:

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="sovereign-internal-token"
)

response = client.chat.completions.create(
    model="mistralai/Mistral-Large-2407",
    messages=[
        {"role": "user", "content": "Please review invoice for user max.mustermann@berlin.de, IBAN DE89370400440532013000."}
    ]
)

print(response.choices[0].message.content)
```

---

## License
This project is licensed under the MIT License.
