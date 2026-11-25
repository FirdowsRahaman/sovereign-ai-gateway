"""Sovereign Policy Engine & Rate Limiter (EU AI Act Art. 15 & Schrems II).

Enforces:
1. Sovereign model & data-residency allowlisting (zero-egress EU routing)
2. Deterministic prompt-injection / jailbreak pattern detection
3. Per-caller sliding-window request rate limiting
"""

from __future__ import annotations

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass(frozen=True)
class PolicyDecision:
    """Result of evaluating an incoming gateway request against sovereign policies."""

    allowed: bool
    reason: str
    policy_code: str


class SovereignPolicyEngine:
    """Enforces EU data residency, approved model routing, and prompt-injection guards."""

    APPROVED_SOVEREIGN_MODELS = frozenset(
        {
            "mistralai/Mistral-Large-2407",
            "mistralai/Mistral-Small-24B-Instruct-2501",
            "meta-llama/Llama-3.3-70B-Instruct-EU",
            "vllm/qwen2.5-72b-sovereign",
        }
    )

    APPROVED_EU_REGIONS = frozenset(
        {
            "eu-central-1",
            "eu-west-3",
            "europe-west3",
            "europe-west6",
        }
    )

    INJECTION_PATTERNS = (
        re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
        re.compile(r"reveal\s+(the\s+)?system\s+prompt", re.IGNORECASE),
        re.compile(r"exfiltrate\s+.*(secret|token|key|pii)", re.IGNORECASE),
    )

    @classmethod
    def evaluate(cls, model: str, combined_prompt: str, region: str) -> PolicyDecision:
        """Validate region residency, model allowlist, and prompt-injection rules."""
        normalized_region = region.split(" ", maxsplit=1)[0].strip()
        if normalized_region not in cls.APPROVED_EU_REGIONS:
            return PolicyDecision(
                allowed=False,
                reason=f"Region '{region}' violates EU zero-egress residency policy.",
                policy_code="SCHREMS_II_REGION_BLOCK",
            )

        if model not in cls.APPROVED_SOVEREIGN_MODELS:
            return PolicyDecision(
                allowed=False,
                reason=f"Model '{model}' is not on the approved sovereign EU model allowlist.",
                policy_code="UNAPPROVED_MODEL_EGRESS",
            )

        for pattern in cls.INJECTION_PATTERNS:
            if pattern.search(combined_prompt):
                return PolicyDecision(
                    allowed=False,
                    reason="Prompt blocked by EU AI Act Art. 15 prompt-injection firewall.",
                    policy_code="PROMPT_INJECTION_DETECTED",
                )

        return PolicyDecision(
            allowed=True,
            reason="Request complies with EU AI Act & GDPR sovereign routing policy.",
            policy_code="COMPLIANT",
        )


@dataclass
class SlidingWindowRateLimiter:
    """In-memory per-caller sliding-window rate limiter."""

    max_requests: int = 60
    window_seconds: float = 60.0
    _requests: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def allow(self, caller_id: str, now: float | None = None) -> bool:
        """Return True if caller is within quota, False if rate-limited."""
        current = now if now is not None else time.monotonic()
        cutoff = current - self.window_seconds
        recent = [ts for ts in self._requests[caller_id] if ts > cutoff]
        if len(recent) >= self.max_requests:
            self._requests[caller_id] = recent
            return False
        recent.append(current)
        self._requests[caller_id] = recent
        return True
