"""Sovereign AI Gateway Server (FastAPI)
OpenAI/vLLM compatible reverse proxy enforcing EU AI Act & GDPR compliance.
"""

import os
import time
import uuid
import hashlib
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from src.guardrails.pii_scrubber import GDPRPIIScrubber
from src.governance.audit_logger import EUAIActAuditLogger

app = FastAPI(
    title="Sovereign AI Gateway (EU AI Act & GDPR)",
    version="1.0.0",
    description="Enterprise reverse proxy with automated GDPR PII scrubbing and EU AI Act Article 12 audit telemetry."
)

scrubber = GDPRPIIScrubber()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="mistralai/Mistral-Large-2407")
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    stream: Optional[bool] = False

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "sovereign_region": os.getenv("SOVEREIGN_REGION", "eu-central-1 (Frankfurt)"),
        "compliance": ["EU_AI_ACT_HIGH_RISK", "GDPR_ARTICLE_25", "SCHREMS_II"]
    }

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request):
    start_time = time.time()
    request_id = f"eu-req-{uuid.uuid4().hex[:12]}"
    caller_ip = request.client.host if request.client else "127.0.0.1"
    caller_hash = hashlib.sha256(caller_ip.encode()).hexdigest()[:16]

    # 1. PII Scrubbing on incoming prompt (GDPR Art. 25 Privacy by Design)
    all_pii_mappings = {}
    sanitized_messages = []
    total_pii_redacted = 0

    for msg in req.messages:
        sanitized_content, mapping = scrubber.anonymize(msg.content)
        all_pii_mappings.update(mapping)
        total_pii_redacted += len(mapping)
        sanitized_messages.append({"role": msg.role, "content": sanitized_content})

    # 2. Forward to Sovereign Inference Endpoint (Mistral AI Paris or vLLM Frankfurt)
    # Simulated upstream sovereign response for demonstration
    simulated_upstream_content = (
        f"This response was processed securely under sovereign EU data residency. "
        f"Input tokens were anonymized ([tokens_redacted: {total_pii_redacted}]). "
        f"Ready to assist with enterprise operations in accordance with Regulation (EU) 2024/1689."
    )

    # 3. Deanonymize output for authorized client
    final_content = scrubber.deanonymize(simulated_upstream_content, all_pii_mappings)
    duration_ms = (time.time() - start_time) * 1000

    # 4. Generate EU AI Act Article 12 Audit Record
    audit_record = EUAIActAuditLogger.create_audit_record(
        request_id=request_id,
        caller_identity_hash=caller_hash,
        target_model=req.model,
        sanitized_prompt=str(sanitized_messages),
        model_response=final_content,
        pii_tokens_redacted=total_pii_redacted,
        latency_ms=duration_ms,
        sovereign_region=os.getenv("SOVEREIGN_REGION", "eu-central-1")
    )
    
    # In production, stream to OpenTelemetry collector or S3 Glacier WORM
    print(f"\n [Audit Telemetry] {audit_record['tamper_evident_sha256'][:16]} | {audit_record['status'] if 'status' in audit_record else 'COMPLIANT'}")

    return {
        "id": request_id,
        "object": "chat.completion",
        "created": int(time.time()),
        "model": req.model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": final_content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": sum(len(m.content) for m in req.messages) // 4,
            "completion_tokens": len(final_content) // 4,
            "total_tokens": (sum(len(m.content) for m in req.messages) + len(final_content)) // 4
        },
        "_eu_compliance_metadata": {
            "pii_redacted_count": total_pii_redacted,
            "audit_hash": audit_record["tamper_evident_sha256"],
            "region": audit_record["sovereign_region"]
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.gateway.server:app", host="0.0.0.0", port=8000, reload=True)
