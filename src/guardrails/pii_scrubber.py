"""GDPR PII Scrubbing Middleware
Detects European and global personal identifiers (IBANs, emails, phone numbers, tax IDs)
and replaces them with deterministic pseudonymization tokens.
"""

import re
from typing import Dict, Tuple, List

class GDPRPIIScrubber:
    """Scans prompts and tool arguments to redact personal data under GDPR Article 25 (Data Protection by Design).
    Preserves an isolated cryptographic mapping session to restore identifiers upon response delivery.
    """PATTERNS = {
        "EMAIL": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "EU_IBAN": r"[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}",
        "PHONE": r"(\+?[0-9]{1,4}[\s-]?)?(\(?[0-9]{2,4}\)?[\s-]?)?[0-9]{3,4}[\s-]?[0-9]{3,4}",
        "GERMAN_TAX_ID": r"\b\d{2}/\d{3}/\d{5}\b",
        "PASSPORT": r"\b[A-PR-WYa-pr-wy][1-9]\d\s?\d{4}[1-9]\b"
    }

    def __init__(self):
        self.compiled_patterns = {k: re.compile(v) for k, v in self.PATTERNS.items()}

    def anonymize(self, text: str) -> Tuple[str, Dict[str, str]]:
        mapping = {}
        sanitized = text
        token_counter = 1

        for pii_type, regex in self.compiled_patterns.items():
            for match in regex.finditer(sanitized):
                val = match.group(0)
                if len(val.strip()) < 4:
                    continue
                token = f"[{pii_type}_{token_counter}]"
                mapping[token] = val
                sanitized = sanitized.replace(val, token, 1)
                token_counter += 1

        return sanitized, mapping

    def deanonymize(self, text: str, mapping: Dict[str, str]) -> str:
        """Restores original PII safely within sovereign client perimeter."""
        result = text
        for token, original in mapping.items():
            result = result.replace(token, original)
        return result
