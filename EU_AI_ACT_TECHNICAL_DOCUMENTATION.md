# EU AI Act Technical Documentation (Sovereign Gateway)

**Regulation Reference**: Regulation (EU) 2024/1689 of the European Parliament and of the Council  
**Classification**: AI System Security & Compliance Control Plane  
**System Name**: Sovereign AI Gateway & Reverse Proxy  
**Version**: 1.0.0  
**Data Residency**: European Economic Area (EEA) • `eu-central-1` (Frankfurt)  

---

## 1. System Description & Legal Mandate
The Sovereign AI Gateway sits between internal enterprise client applications and foundation model inference clusters. It operates as an enforcement boundary ensuring that interactions with Generative AI models comply with:
- **GDPR (Regulation (EU) 2016/679)**: Automatic PII detection and token pseudonymization (Articles 5 & 25).
- **EU AI Act (Regulation (EU) 2024/1689)**:
  - **Article 12**: Automated record-keeping, parameter tracking, and cryptographic integrity hashes.
  - **Article 13**: Transparent metadata attribution on every API response.
  - **Article 15**: Cybersecurity defenses preventing data exfiltration and prompt injection.

---

## 2. Technical Architecture
1. **PII Masking Layer**: Intercepts requests, extracts sensitive entities (IBAN, passport, emails, German tax IDs), replaces them with surrogate tokens, and decrypts responses only for authorized endpoints.
2. **Audit Telemetry**: Every payload produces a SHA-256 verification digest streamed to write-once storage.
3. **Data Residency**: Deployed exclusively inside European cloud regions (e.g., AWS Frankfurt `eu-central-1`) with zero telemetry egress.
