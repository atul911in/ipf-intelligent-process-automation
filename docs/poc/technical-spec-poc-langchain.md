# PoC Technical Specification: LangChain/LangGraph Stack

## Document Control

| Item | Detail |
|------|--------|
| Version | 1.0 |
| Date | July 2026 |
| Scope | PoC - Orchestrator + Document Extraction Agent |
| Classification | CONFIDENTIAL - Internal Working Draft |
| Prepared by | Mastek AI CoE |

---

## 1. Overview

This specification defines the technical design for the IPF IPA Proof of Concept using LangChain/LangGraph. The PoC scope is limited to: (1) the Orchestrator Agent built on LangGraph, and (2) the Document Extraction Agent. The architecture validates the multi-agent pattern before scaling to additional agents in Wave 1.

---

## 2. Architecture

`
                    +-------------------+
                    |   FastAPI Gateway  |
                    |   (REST + WebSocket)|
                    +---------+---------+
                              |
                    +---------v---------+
                    |  LANGGRAPH         |
                    |  ORCHESTRATOR      |
                    |                    |
                    |  - Workflow Graph   |
                    |  - State Manager   |
                    |  - Policy Gate     |
                    |  - Human Checkpoint|
                    +---------+---------+
                              |
              +---------------+---------------+
              |                               |
    +---------v---------+           +---------v---------+
    |  DOCUMENT AGENT   |           |  HUMAN REVIEW     |
    |                   |           |  SERVICE           |
    |  - OCR Tool       |           |  (WebSocket queue) |
    |  - NLP Extractor  |           |                    |
    |  - Validator      |           +--------------------+
    |  - Confidence     |
    +---------+---------+
              |
    +---------v---------+
    |  TOOLS LAYER      |
    |                   |
    |  - Unstructured.io|
    |  - Tesseract      |
    |  - LLM (GPT-4o)   |
    |  - FOCUS Mock API |
    +---------+---------+
              |
    +---------v---------+
    |  DATA LAYER       |
    |                   |
    |  - PostgreSQL     |
    |  - Redis          |
    |  - MinIO (S3)     |
    +-------------------+
`

---

## 3. LangGraph Orchestrator

### 3.1 Workflow Graph Definition

`python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from typing import TypedDict, Optional, List

class DocumentWorkflowState(TypedDict):
    workflow_id: str
    document_ids: List[str]
    market: str
    language: str
    extraction_results: List[dict]
    validation_results: List[dict]
    fields_needing_review: List[dict]
    human_corrections: List[dict]
    recommendation: Optional[dict]
    credit_assessor_decision: Optional[dict]
    policy_decisions: List[dict]
    status: str
    error: Optional[str]

# Build the workflow graph
workflow = StateGraph(DocumentWorkflowState)

# Nodes
workflow.add_node("extract_documents", extract_documents_node)
workflow.add_node("validate_fields", validate_fields_node)
workflow.add_node("policy_check", policy_gate_node)
workflow.add_node("human_review", human_review_node)        # interrupt_before
workflow.add_node("generate_recommendation", recommendation_node)
workflow.add_node("credit_assessor", credit_assessor_node)  # interrupt_before
workflow.add_node("record_decision", record_decision_node)
workflow.add_node("handle_failure", failure_handler_node)

# Edges
workflow.set_entry_point("extract_documents")
workflow.add_edge("extract_documents", "validate_fields")
workflow.add_edge("validate_fields", "policy_check")
workflow.add_conditional_edges("policy_check", route_after_policy, {
    "needs_human_review": "human_review",
    "all_clear": "generate_recommendation",
    "blocked": "handle_failure"
})
workflow.add_edge("human_review", "validate_fields")  # Re-validate after correction
workflow.add_edge("generate_recommendation", "credit_assessor")
workflow.add_edge("credit_assessor", "record_decision")
workflow.add_edge("record_decision", END)

# Compile with checkpointer
checkpointer = PostgresSaver(conn_string=POSTGRES_URL)
app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_review", "credit_assessor"]
)
`

### 3.2 State Persistence

| Attribute | Specification |
|-----------|--------------|
| Checkpointer | PostgresSaver (LangGraph native) |
| Database | PostgreSQL 16 |
| Recovery | Automatic resume from last checkpoint on failure |
| Concurrency | 100+ concurrent workflows via connection pooling (pgbouncer) |
| State TTL | 90 days active; archived to cold storage after completion |

### 3.3 Human-in-the-Loop Pattern

`python
# Interrupt pattern for mandatory human checkpoints
# The workflow pauses at interrupt_before nodes and resumes
# only when external input is provided via the resume API

@app.post("/workflow/{workflow_id}/resume")
async def resume_workflow(workflow_id: str, human_input: HumanInput):
    """Resume a paused workflow with human input."""
    config = {"configurable": {"thread_id": workflow_id}}
    # Update state with human input
    app.update_state(config, human_input.dict())
    # Resume execution
    result = app.invoke(None, config)
    return result
`

---

## 4. Document Extraction Agent

### 4.1 Agent Definition

`python
from langchain.agents import AgentExecutor
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

# LLM for reasoning and extraction
llm = ChatOpenAI(model="gpt-4o", temperature=0)

# Tools available to the Document Agent
tools = [
    ocr_extract_tool,        # Unstructured.io / Tesseract
    language_detect_tool,     # fastText-based
    field_extract_tool,       # LLM-based structured extraction
    format_validate_tool,     # Regex/rule validation
    cross_reference_tool,     # Check against FOCUS mock
    confidence_score_tool,    # Compute per-field confidence
]

document_agent = create_react_agent(llm, tools)
`

### 4.2 OCR Pipeline

| Stage | Tool | Detail |
|-------|------|--------|
| 1. Ingest | MinIO S3 | Accept JPEG, PNG, PDF, TIFF |
| 2. Partition | Unstructured.io | Split multi-page docs; detect layout |
| 3. OCR | Tesseract 5 + Unstructured | Text extraction; confidence per word |
| 4. Language | fastText | Detect Polish/Romanian/English |
| 5. Extract | GPT-4o (structured output) | Field extraction using market schema |
| 6. Validate | Custom rules | Format, date logic, cross-reference |
| 7. Score | Composite | OCR confidence x NLP confidence |

### 4.3 Market Document Schemas

`python
# Example: Polish National ID Card (Dowod Osobisty)
POLISH_ID_SCHEMA = {
    "document_type": "national_id",
    "market": "PL",
    "required_fields": [
        {"name": "first_name", "type": "string", "validation": "alpha_polish"},
        {"name": "last_name", "type": "string", "validation": "alpha_polish"},
        {"name": "pesel", "type": "string", "validation": "pesel_checksum"},
        {"name": "document_number", "type": "string", "validation": "regex:^[A-Z]{3}\\d{6}$"},
        {"name": "expiry_date", "type": "date", "validation": "future_date"},
        {"name": "birth_date", "type": "date", "validation": "age_minimum_18"},
    ]
}

# Example: Romanian CNP
ROMANIAN_ID_SCHEMA = {
    "document_type": "national_id",
    "market": "RO",
    "required_fields": [
        {"name": "first_name", "type": "string", "validation": "alpha_romanian"},
        {"name": "last_name", "type": "string", "validation": "alpha_romanian"},
        {"name": "cnp", "type": "string", "validation": "cnp_checksum_13_digits"},
        {"name": "document_number", "type": "string", "validation": "regex:^\\d{9}$"},
        {"name": "expiry_date", "type": "date", "validation": "future_date"},
    ]
}
`

### 4.4 Confidence Scoring Algorithm

`python
def compute_field_confidence(ocr_confidence: float, nlp_confidence: float) -> int:
    """
    Composite confidence score (0-100).
    OCR confidence: from Tesseract word-level confidence
    NLP confidence: from LLM extraction certainty (logprobs or self-assessment)
    """
    # Weighted: OCR matters more for raw text, NLP for semantic extraction
    composite = (ocr_confidence * 0.6) + (nlp_confidence * 0.4)
    return int(composite * 100)

# Policy gate threshold: 85
# Below 85 -> route to human review
`

---

## 5. Policy Gate Implementation

`python
class PolicyGate:
    def __init__(self, redis_client, postgres_client):
        self.cache = redis_client      # Hot policy rules
        self.store = postgres_client   # Versioned policy store

    async def evaluate(self, agent_id: str, action: dict, market: str) -> PolicyDecision:
        """Evaluate an agent action against market rules."""
        rules = await self._load_rules(market, action["type"])
        
        for rule in rules:
            result = rule.evaluate(action)
            if not result.permitted:
                await self._log_decision(agent_id, action, rule, "BLOCKED")
                return PolicyDecision(
                    permitted=False,
                    rule_id=rule.id,
                    reason=result.reason,
                    escalation=rule.escalation_path
                )
        
        await self._log_decision(agent_id, action, None, "PERMITTED")
        return PolicyDecision(permitted=True)

# PoC Policy Rules
POC_RULES = [
    ConfidenceThresholdRule(threshold=85, action="flag_for_review"),
    MandatoryHumanReviewRule(decision_type="loan_approval"),
    FieldValidationRule(field="pesel", validator="pesel_checksum"),
    DocumentExpiryRule(reject_if_expired=True),
]
`

---

## 6. Infrastructure (PoC)

### 6.1 Deployment (Docker Compose for PoC)

`yaml
services:
  orchestrator:
    build: ./orchestrator
    ports: ["8000:8000"]
    environment:
      - POSTGRES_URL=postgresql://ipa:secret@postgres:5432/ipa
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=
    depends_on: [postgres, redis, minio]

  document-agent:
    build: ./agents/document
    ports: ["8001:8001"]
    environment:
      - OPENAI_API_KEY=
      - MINIO_ENDPOINT=minio:9000

  human-review-ui:
    build: ./ui/human-review
    ports: ["3000:3000"]

  focus-mock:
    build: ./mocks/focus
    ports: ["8080:8080"]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ipa
      POSTGRES_USER: ipa
      POSTGRES_PASSWORD: secret
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin

volumes:
  pgdata:
`

### 6.2 Technology Versions

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.12 | Runtime |
| LangGraph | 0.3+ | Orchestrator framework |
| LangChain | 0.2+ | Agent framework |
| langchain-openai | latest | GPT-4o integration |
| Unstructured | latest | Document parsing + OCR |
| Tesseract | 5.x | OCR engine |
| fastText | latest | Language detection |
| FastAPI | 0.110+ | API gateway |
| PostgreSQL | 16 | State + audit store |
| Redis | 7 | Policy cache |
| MinIO | latest | S3-compatible object store |
| LangSmith | latest | Observability (optional for PoC) |

### 6.3 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/workflow/start | POST | Submit documents and start workflow |
| /api/v1/workflow/{id}/status | GET | Get workflow current state |
| /api/v1/workflow/{id}/resume | POST | Provide human input to resume |
| /api/v1/documents/upload | POST | Upload document images |
| /api/v1/review/queue | GET | Get pending human review items |
| /api/v1/review/{id}/submit | POST | Submit human review corrections |
| /api/v1/decision/{id}/submit | POST | Submit credit assessor decision |
| /api/v1/agents/health | GET | Agent registry health check |
| /api/v1/audit/workflow/{id} | GET | Get full audit trail |

---

## 7. Observability (PoC)

| Concern | Tool | Detail |
|---------|------|--------|
| Agent tracing | LangSmith (or stdout for PoC) | Every LLM call, tool invocation traced |
| Workflow state | PostgreSQL queries | Dashboard reads from checkpoint table |
| Metrics | Prometheus + Grafana (optional) | Latency, throughput, error rates |
| Logs | Structured JSON to stdout | Docker Compose log aggregation |

---

## 8. Testing Strategy

| Test Type | Scope | Tool |
|-----------|-------|------|
| Unit tests | Individual tools, validators, policy rules | pytest |
| Integration tests | Agent-to-orchestrator workflow | pytest + TestClient |
| Document accuracy | OCR + extraction on test corpus | Custom eval harness |
| End-to-end | Full workflow with human simulation | Playwright (UI) + API tests |
| Load test | 100 concurrent workflows | Locust |

### Test Dataset Requirements
- 200+ sample documents (ID cards, utility bills, payslips)
- Target market language (Polish or Romanian)
- Mix of high-quality scans and mobile photos
- Known ground-truth annotations for accuracy measurement

---

## 9. PoC Timeline

| Week | Deliverable |
|------|-------------|
| 1-2 | Infrastructure setup; LangGraph orchestrator skeleton; FOCUS mock API |
| 3-4 | Document Agent: OCR pipeline + Polish/Romanian schema extraction |
| 5-6 | Policy gate; validation logic; confidence scoring |
| 7-8 | Human review UI; human-in-the-loop workflow integration |
| 9-10 | End-to-end testing; accuracy evaluation on test dataset |
| 11-12 | Performance testing; documentation; PoC exit criteria assessment |

---

## 10. PoC Cost Estimate

| Component | Monthly Cost (GBP) |
|-----------|-------------------|
| OpenAI GPT-4o API (200 docs x test iterations) | 200-500 |
| Cloud VM (dev/test, 2x m5.xlarge equivalent) | 300-500 |
| MinIO / Storage | included (local) |
| LangSmith (optional) | 0-100 |
| Developer licenses / tools | 0 |
| **Total PoC monthly run** | **500-1,100** |

---

## 11. Exit Criteria (Maps to Requirement 10)

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Extraction accuracy | 90 percent+ field-level | Automated eval vs ground truth |
| Workflow reliability | Less than 1 percent failure | Error count / total runs |
| End-to-end latency | Under 3 minutes (p95) | Timestamp tracking |
| Concurrent workflows | 100+ without degradation | Load test results |
| Human-in-the-loop | Demonstrated working | Manual QA walkthrough |
| Cost per document | Documented estimate | API usage / doc count |

---

## Addendum: UI and Event Architecture (Requirements 11-13)

### A1. Updated Architecture with UI Layer

`
+------------------+                  +------------------+
|  ADMIN UI        |                  |  REVIEWER UI     |
|  (React/Next.js) |                  |  (React/Next.js) |
|                  |                  |                  |
|  - Auth (Admin)  |                  |  - Auth (Reviewer|
|  - Multi-upload  |                  |    /Assessor)    |
|  - App ID link   |                  |  - Work queue    |
|  - Upload history|                  |  - Doc viewer    |
+--------+---------+                  |  - Field editor  |
         |                            |  - Approve/Decline
         | POST /api/v1/upload        +--------+---------+
         |                                     |
+--------v---------+              GET/POST /api/v1/review/*
|  API GATEWAY     |<------------------------------+
|  (FastAPI)       |
+--------+---------+
         |
    +----v----+
    |  MinIO  |--- upload event ---> Redis Pub/Sub
    | (S3)    |                           |
    +---------+                     +-----v------+
                                    | LANGGRAPH  |
                                    | ORCHESTRATOR|
                                    +-----+------+
                                          |
                               +----------+----------+
                               |                     |
                        +------v------+       +------v------+
                        | DOC AGENT   |       | HUMAN REVIEW|
                        | (Extract +  |       | (WebSocket  |
                        |  Validate)  |       |  to UI)     |
                        +-------------+       +-------------+
`

### A2. Admin UI — Document Upload Portal

#### Technology Stack
| Component | Choice | Rationale |
|-----------|--------|-----------|
| Framework | Next.js 14 (React) | Server-side rendering for auth, App Router |
| Styling | Tailwind CSS | Rapid UI development for PoC |
| Upload library | react-dropzone + tus-js-client | Resumable uploads for large files |
| Auth | NextAuth.js with Keycloak/Auth0 | Role-based (admin vs reviewer) |
| State management | React Query (TanStack Query) | Server state + upload progress tracking |
| Deployment | Docker container | Consistent with PoC stack |

#### Key UI Components

`
Admin Portal
+-------------------------------------------------------+
| IPF Document Upload Portal          [Admin: jan.k]    |
+-------------------------------------------------------+
| Application ID: [APP-PL-001    ] v                    |
| Market:         [Poland        ] v                    |
+-------------------------------------------------------+
| +---------------------------------------------------+ |
| |                                                   | |
| |     Drag and drop files here                      | |
| |     or click to browse                            | |
| |                                                   | |
| |     Accepted: JPEG, PNG, PDF, TIFF (max 25MB)    | |
| |     Up to 20 files per submission                 | |
| +---------------------------------------------------+ |
|                                                       |
| Queued Files:                                         |
| +------+-------------+----------------+--------+---+ |
| | File | Type        | Size           | Status | X | |
| +------+-------------+----------------+--------+---+ |
| | id_front.jpg  | [Identity Card v] | 2.1 MB | OK | |
| | bill_pge.pdf  | [Utility Bill  v] | 1.5 MB | OK | |
| | payslip.jpg   | [Income Stmt   v] | 3.2 MB | OK | |
| +------+-------------+----------------+--------+---+ |
|                                                       |
|                              [Cancel] [Submit All]    |
+-------------------------------------------------------+
| Upload History                          [Filter v]    |
| +---------------------------------------------------+ |
| | Date       | App ID     | Files | Status          | |
| | 2026-07-08 | APP-PL-001 | 3     | Processing...   | |
| | 2026-07-07 | APP-RO-002 | 2     | Verified        | |
| | 2026-07-07 | APP-PL-003 | 3     | Needs Review    | |
| +---------------------------------------------------+ |
+-------------------------------------------------------+
`

#### API Endpoints (Admin)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/upload/presign | POST | Get presigned URLs for direct S3 upload |
| /api/v1/upload/confirm | POST | Confirm upload batch + emit processing event |
| /api/v1/upload/history | GET | List upload history for current admin |
| /api/v1/applications/search | GET | Search applications for linking |

### A3. Event-Driven Processing Trigger

#### LangChain/LangGraph Implementation

`python
import redis.asyncio as redis
import json
from datetime import datetime

# Event publisher (called after upload confirmation)
async def publish_upload_event(redis_client, batch):
    event = {
        "event_type": "documents.uploaded",
        "event_id": str(uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "payload": {
            "application_id": batch.application_id,
            "market": batch.market,
            "operator_id": batch.operator_id,
            "documents": [
                {
                    "document_id": doc.id,
                    "document_type": doc.type,
                    "storage_key": doc.storage_key,
                    "filename": doc.original_filename
                }
                for doc in batch.documents
            ]
        }
    }
    await redis_client.publish("ipf:documents:uploaded", json.dumps(event))

# Event subscriber (orchestrator startup)
async def listen_for_uploads(redis_client, orchestrator):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("ipf:documents:uploaded")
    
    async for message in pubsub.listen():
        if message["type"] == "message":
            event = json.loads(message["data"])
            
            # Idempotency check
            if await is_already_processed(event["event_id"]):
                continue
            
            # Start workflow
            workflow_id = f"wf-{event['payload']['application_id']}-{event['event_id'][:8]}"
            await orchestrator.start_workflow(
                workflow_id=workflow_id,
                initial_state={
                    "application_id": event["payload"]["application_id"],
                    "market": event["payload"]["market"],
                    "documents": event["payload"]["documents"],
                    "status": "PROCESSING"
                }
            )
            
            # Mark as processed (idempotency)
            await mark_processed(event["event_id"], workflow_id)
`

#### Dead Letter Queue Pattern

`python
# If workflow fails to start within 30 seconds
async def handle_failed_trigger(event, error):
    await dead_letter_queue.push({
        "original_event": event,
        "error": str(error),
        "failed_at": datetime.utcnow().isoformat(),
        "retry_count": 0
    })
    await alert_operations(
        f"Document processing failed to start for {event['payload']['application_id']}: {error}"
    )
`

### A4. Reviewer UI — Document Review Portal

#### Key UI Components

`
Reviewer Portal
+-------------------------------------------------------+
| IPF Document Review Portal      [Reviewer: anna.n]    |
+-------------------------------------------------------+
| Work Queue (3 pending)                    [Filters v] |
+-------------------------------------------------------+
| +---------------------------------------------------+ |
| | App ID     | Type     | Market | Status  | Conf.  | |
| +---------------------------------------------------+ |
| | APP-PL-001 | ID Card  | PL     | Verified| 96%    | |
| | APP-PL-001 | Bill     | PL     | Verified| 94%    | |
| | APP-PL-001 | Payslip  | PL     | Review  | 72% !! | |
| +---------------------------------------------------+ |
| Overall: 2/3 verified | 1 needs review                |
+-------------------------------------------------------+

[Click on APP-PL-001 Payslip row]

+-------------------------------------------------------+
| Document Review: APP-PL-001 - Payslip (PL-INC-004)   |
+-------------------------------------------------------+
| +-------------------------+ +-------------------------+|
| |                         | | Extracted Fields:       ||
| |  [Original Document    ]| |                         ||
| |  [Image / PDF Viewer   ]| | Employer:               ||
| |                         | | GHI Budownictwo S.A.    ||
| |                         | | Confidence: 92% [green] ||
| |                         | |                         ||
| |                         | | Employee Name:           ||
| |                         | | Malgorzata Wojc[...]    ||
| |                         | | Confidence: 68% [red]   ||
| |                         | | [Edit: ______________ ] ||
| |                         | |                         ||
| |                         | | Gross Salary:           ||
| |                         | | 7,200.00 PLN            ||
| |                         | | Confidence: 71% [red]   ||
| |                         | | [Edit: ______________ ] ||
| |                         | |                         ||
| |                         | | Net Salary:             ||
| |                         | | 5,230.00 PLN            ||
| |                         | | Confidence: 73% [amber] ||
| |                         | | [Edit: ______________ ] ||
| +-------------------------+ +-------------------------+|
|                                                       |
| Validation Issues:                                    |
| ! Employee name confidence below threshold (68%)      |
| ! Gross salary confidence below threshold (71%)       |
|                                                       |
|               [Reject Document] [Confirm Corrections] |
+-------------------------------------------------------+

[After all documents verified - Credit Assessor view]

+-------------------------------------------------------+
| Loan Decision: APP-PL-001                             |
+-------------------------------------------------------+
| AI Recommendation: APPROVE                            |
| Risk Score: LOW                                       |
|                                                       |
| Supporting Data:                                      |
| - All 3 documents verified (2 auto + 1 human review) |
| - Income verified: 5,230 PLN net (within threshold)   |
| - Address confirmed via utility bill                  |
| - ID valid until 2032                                 |
|                                                       |
| Reason Codes (optional): [_________________________ ] |
|                                                       |
|                        [DECLINE]  [APPROVE]           |
+-------------------------------------------------------+
`

#### WebSocket for Real-Time Updates

`python
# WebSocket connection for live status updates to Reviewer UI
from fastapi import WebSocket

@app.websocket("/ws/review/{application_id}")
async def review_websocket(websocket: WebSocket, application_id: str):
    await websocket.accept()
    
    # Subscribe to workflow state changes for this application
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"ipf:workflow:{application_id}:state")
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                state = json.loads(message["data"])
                await websocket.send_json({
                    "type": "state_update",
                    "application_id": application_id,
                    "status": state["status"],
                    "documents": state["documents"],
                    "recommendation": state.get("recommendation")
                })
    except WebSocketDisconnect:
        await pubsub.unsubscribe()
`

#### API Endpoints (Reviewer)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/v1/review/queue | GET | Get pending review items (filterable) |
| /api/v1/review/{doc_id} | GET | Get full extraction result for a document |
| /api/v1/review/{doc_id}/correct | POST | Submit field corrections |
| /api/v1/review/{doc_id}/confirm | POST | Confirm all fields correct |
| /api/v1/decision/{app_id} | GET | Get recommendation package |
| /api/v1/decision/{app_id}/submit | POST | Submit approve/decline decision |
| /api/v1/application/{app_id}/status | GET | Get overall application status |
| /ws/review/{app_id} | WS | Real-time status updates |

### A5. Updated Docker Compose (with UI services)

`yaml
services:
  # --- Existing services ---
  orchestrator:
    build: ./orchestrator
    ports: ["8000:8000"]
    environment:
      - POSTGRES_URL=postgresql://ipa:secret@postgres:5432/ipa
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - OPENAI_API_KEY=
    depends_on: [postgres, redis, minio]

  document-agent:
    build: ./agents/document
    ports: ["8001:8001"]
    environment:
      - OPENAI_API_KEY=
      - MINIO_ENDPOINT=minio:9000

  # --- NEW: UI Services ---
  admin-ui:
    build: ./ui/admin-portal
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXTAUTH_URL=http://localhost:3000
      - NEXTAUTH_SECRET=
    depends_on: [orchestrator]

  reviewer-ui:
    build: ./ui/reviewer-portal
    ports: ["3001:3001"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_WS_URL=ws://localhost:8000
      - NEXTAUTH_URL=http://localhost:3001
      - NEXTAUTH_SECRET=
    depends_on: [orchestrator]

  # --- Supporting ---
  focus-mock:
    build: ./mocks/focus
    ports: ["8080:8080"]

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ipa
      POSTGRES_USER: ipa
      POSTGRES_PASSWORD: secret
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin

volumes:
  pgdata:
`

### A6. Authentication and Role Separation

| Role | Portal | Capabilities |
|------|--------|-------------|
| back_office_admin | Admin UI (port 3000) | Upload documents, link to applications, view upload history |
| document_reviewer | Reviewer UI (port 3001) | View extractions, edit fields, confirm corrections |
| credit_assessor | Reviewer UI (port 3001) | All reviewer capabilities + approve/decline loan decisions |
| operations | Both (read-only dashboards) | View processing metrics, alerts, audit logs |

### A7. Updated PoC Timeline (with UI work)

| Week | Deliverable |
|------|-------------|
| 1-2 | Infrastructure; LangGraph orchestrator; FOCUS mock; Auth setup (Keycloak/NextAuth) |
| 3-4 | Document Agent: OCR + extraction pipeline |
| 5-6 | Admin UI: upload portal with batch upload + event trigger |
| 7-8 | Policy gate; validation; confidence scoring; event-driven workflow start |
| 9-10 | Reviewer UI: work queue, document viewer, field editor, correction workflow |
| 11-12 | Credit assessor flow; WebSocket live updates; end-to-end testing |
| 13-14 | Performance testing; accuracy evaluation; PoC exit criteria assessment |

Note: Timeline extended by 2 weeks (12 to 14 weeks) to accommodate the two UI portals.

---

## 12. UI and Event Architecture (Requirements 11-13)

### 12.1 Architecture with UI Layer

`
+------------------+                  +--------------------+
|  ADMIN UI        |                  |  REVIEWER UI       |
|  (React/Next.js) |                  |  (React/Next.js)   |
|                  |                  |                    |
|  - Doc upload    |                  |  - Work queue      |
|  - Batch submit  |                  |  - Doc viewer      |
|  - Upload history|                  |  - Field editor    |
+--------+---------+                  |  - Confidence view |
         |                            |  - Approve/Decline |
         | POST /upload               +--------+-----------+
         v                                     |
+------------------+            GET /queue      | POST /review
|  FastAPI Gateway |<--------------------------+
+--------+---------+
         |
         | Store docs
         v
+------------------+     Event emitted     +-------------------+
|  MinIO (S3)      |--------------------->| Redis PubSub /     |
|  Persistent Store|  (on upload success)  | Event Bus          |
+------------------+                       +--------+----------+
                                                    |
                                           Subscribe|
                                                    v
                                           +--------+----------+
                                           | LANGGRAPH         |
                                           | ORCHESTRATOR      |
                                           | (auto-starts      |
                                           |  workflow)         |
                                           +-------------------+
`

### 12.2 Admin UI (Document Upload Portal)

| Attribute | Specification |
|-----------|--------------|
| Framework | React 18 + Next.js 14 (App Router) |
| Auth | Keycloak OIDC (role: back-office-admin) |
| Upload | react-dropzone + chunked upload via tus protocol |
| Max batch | 20 files per submission |
| Formats | JPEG, PNG, PDF, TIFF (validated client-side + server-side) |
| Max file size | 25 MB per file |
| Storage | MinIO (S3-compatible) - permanent retention |
| State | Upload progress via WebSocket; status polling via REST |

**Key Pages:**
- /upload - Drag-and-drop upload area with application ID input and document type selector per file
- /history - Searchable table of past uploads with filters (date, app ID, status)
- /history/:batchId - Detail view of a specific submission showing per-file status

**Upload API:**

`python
@app.post("/api/v1/documents/upload")
async def upload_documents(
    application_id: str = Form(...),
    market: str = Form(...),
    files: List[UploadFile] = File(...),
    document_types: List[str] = Form(...),  # per-file type
    current_user: User = Depends(require_role("back-office-admin"))
):
    batch_id = str(uuid4())
    results = []
    
    for file, doc_type in zip(files, document_types):
        # Validate format and size
        validate_file(file)
        
        # Store to MinIO permanently
        object_key = f"{application_id}/{batch_id}/{file.filename}"
        await minio_client.put_object(BUCKET, object_key, file)
        
        # Write metadata to PostgreSQL
        doc_record = await db.create_document(
            document_id=str(uuid4()),
            batch_id=batch_id,
            application_id=application_id,
            document_type=doc_type,
            market=market,
            storage_key=object_key,
            uploaded_by=current_user.id,
            uploaded_at=datetime.utcnow(),
            status="UPLOADED"
        )
        results.append(doc_record)
    
    # Emit event to trigger processing
    await event_bus.publish("document.batch.uploaded", {
        "batch_id": batch_id,
        "application_id": application_id,
        "market": market,
        "document_ids": [r.document_id for r in results],
        "document_types": document_types
    })
    
    return {"batch_id": batch_id, "documents": results}
`

### 12.3 Event-Driven Processing Trigger

| Attribute | Specification |
|-----------|--------------|
| Event bus | Redis Streams (PoC) or Kafka (production) |
| Event name | document.batch.uploaded |
| Payload | batch_id, application_id, market, document_ids, document_types |
| Latency | Event emitted within 5 seconds of successful storage |
| Guarantee | At-least-once delivery; idempotent consumer (checks workflow exists before creating) |
| DLQ | Failed events stored in document.batch.uploaded.dlq stream |
| Alert | If event not consumed within 30 seconds, log error + alert ops |

**Event Consumer (starts LangGraph workflow):**

`python
async def document_event_consumer():
    """Subscribes to upload events and initiates LangGraph workflows."""
    async for event in event_bus.subscribe("document.batch.uploaded"):
        batch_id = event["batch_id"]
        
        # Idempotency check
        if await workflow_exists(batch_id):
            logger.info(f"Workflow already exists for batch {batch_id}, skipping")
            continue
        
        # Initiate LangGraph workflow
        config = {"configurable": {"thread_id": batch_id}}
        initial_state = {
            "workflow_id": batch_id,
            "application_id": event["application_id"],
            "market": event["market"],
            "document_ids": event["document_ids"],
            "document_types": event["document_types"],
            "status": "PROCESSING"
        }
        
        try:
            await app.ainvoke(initial_state, config)
        except Exception as e:
            await event_bus.publish("document.batch.uploaded.dlq", {
                **event, "error": str(e)
            })
            raise_alert(f"Workflow failed to start for batch {batch_id}")
`

### 12.4 Reviewer UI (Document Review Portal)

| Attribute | Specification |
|-----------|--------------|
| Framework | React 18 + Next.js 14 (App Router) |
| Auth | Keycloak OIDC (roles: document-reviewer, credit-assessor) |
| Real-time | WebSocket for live status updates as documents process |
| Image viewer | react-image-magnify (zoom into document areas) |
| Confidence display | Colour-coded: green (85%+), amber (70-84%), red (<70%) |

**Key Pages:**
- /queue - Work queue table with filters and sort (pending review items first)
- /review/:applicationId - Full application review with all documents
- /review/:applicationId/:documentId - Side-by-side: original image + extracted fields
- /decision/:applicationId - Credit assessor decision page (post all docs verified)

**Work Queue API:**

`python
@app.get("/api/v1/review/queue")
async def get_review_queue(
    status: Optional[str] = Query(None),  # PENDING_REVIEW, VERIFIED, NEEDS_CORRECTION
    market: Optional[str] = Query(None),
    min_confidence: Optional[int] = Query(None),
    current_user: User = Depends(require_role("document-reviewer", "credit-assessor"))
):
    items = await db.get_review_queue(
        status=status, market=market, min_confidence=min_confidence
    )
    return {"items": items, "total": len(items)}

@app.get("/api/v1/review/{application_id}/{document_id}")
async def get_document_review(
    application_id: str,
    document_id: str,
    current_user: User = Depends(require_role("document-reviewer", "credit-assessor"))
):
    # Get extraction results + original document URL
    extraction = await db.get_extraction_result(document_id)
    doc_url = minio_client.presigned_get_url(extraction.storage_key, expires=3600)
    
    return {
        "document_id": document_id,
        "application_id": application_id,
        "original_document_url": doc_url,
        "extracted_fields": extraction.fields,  # Each with value + confidence
        "validation_results": extraction.validations,
        "overall_confidence": extraction.overall_confidence,
        "status": extraction.status
    }
`

**Field Correction and Workflow Resume:**

`python
@app.post("/api/v1/review/{application_id}/{document_id}/correct")
async def submit_corrections(
    application_id: str,
    document_id: str,
    corrections: List[FieldCorrection],
    current_user: User = Depends(require_role("document-reviewer"))
):
    # Save corrections
    for correction in corrections:
        await db.save_correction(
            document_id=document_id,
            field_name=correction.field_name,
            original_value=correction.original_value,
            corrected_value=correction.corrected_value,
            corrected_by=current_user.id,
            corrected_at=datetime.utcnow()
        )
    
    # Resume LangGraph workflow with corrections
    batch_id = await db.get_batch_id(application_id)
    config = {"configurable": {"thread_id": batch_id}}
    
    await app.aupdate_state(config, {
        "human_corrections": [c.dict() for c in corrections],
        "status": "REVALIDATING"
    })
    
    # Resume (re-validates with corrected data)
    await app.ainvoke(None, config)
    
    # Log audit event
    await audit_log.record(
        action="FIELD_CORRECTION",
        user=current_user.id,
        document_id=document_id,
        details=corrections
    )
    
    return {"status": "corrections_applied", "workflow_resumed": True}

@app.post("/api/v1/decision/{application_id}")
async def submit_loan_decision(
    application_id: str,
    decision: LoanDecision,  # approve/decline + reason codes
    current_user: User = Depends(require_role("credit-assessor"))
):
    batch_id = await db.get_batch_id(application_id)
    config = {"configurable": {"thread_id": batch_id}}
    
    await app.aupdate_state(config, {
        "credit_assessor_decision": {
            "decision": decision.decision,
            "reason_codes": decision.reason_codes,
            "assessor_id": current_user.id,
            "timestamp": datetime.utcnow().isoformat()
        }
    })
    
    await app.ainvoke(None, config)
    
    return {"status": "decision_recorded", "decision": decision.decision}
`

### 12.5 Updated Docker Compose (with UI services)

`yaml
services:
  # Backend
  orchestrator:
    build: ./orchestrator
    ports: ["8000:8000"]
    environment:
      - POSTGRES_URL=postgresql://ipa:secret@postgres:5432/ipa
      - REDIS_URL=redis://redis:6379
      - MINIO_ENDPOINT=minio:9000
      - OPENAI_API_KEY=
      - KEYCLOAK_URL=http://keycloak:8080
    depends_on: [postgres, redis, minio, keycloak]

  document-agent:
    build: ./agents/document
    ports: ["8001:8001"]
    environment:
      - OPENAI_API_KEY=
      - MINIO_ENDPOINT=minio:9000

  event-consumer:
    build: ./orchestrator
    command: python -m event_consumer
    environment:
      - REDIS_URL=redis://redis:6379
      - POSTGRES_URL=postgresql://ipa:secret@postgres:5432/ipa
    depends_on: [redis, postgres, orchestrator]

  # UI Applications
  admin-ui:
    build: ./ui/admin
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080

  reviewer-ui:
    build: ./ui/reviewer
    ports: ["3001:3001"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
      - NEXT_PUBLIC_KEYCLOAK_URL=http://localhost:8080

  # Infrastructure
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: ipa
      POSTGRES_USER: ipa
      POSTGRES_PASSWORD: secret
    volumes: ["pgdata:/var/lib/postgresql/data"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    ports: ["9000:9000", "9001:9001"]
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes: ["minio-data:/data"]

  keycloak:
    image: quay.io/keycloak/keycloak:24.0
    command: start-dev
    ports: ["8080:8080"]
    environment:
      KEYCLOAK_ADMIN: admin
      KEYCLOAK_ADMIN_PASSWORD: admin

  focus-mock:
    build: ./mocks/focus
    ports: ["8090:8090"]

volumes:
  pgdata:
  minio-data:
`

### 12.6 Authentication and Roles (Keycloak)

| Role | Portal Access | Permissions |
|------|--------------|-------------|
| back-office-admin | Admin UI (port 3000) | Upload documents, view upload history |
| document-reviewer | Reviewer UI (port 3001) | View queue, review docs, correct fields |
| credit-assessor | Reviewer UI (port 3001) | All reviewer permissions + approve/decline loans |
| operations | Both (read-only dashboards) | View audit trails, monitoring |

### 12.7 Updated PoC Timeline (with UI)

| Week | Deliverable |
|------|-------------|
| 1-2 | Infrastructure (Docker Compose, Keycloak, MinIO, PostgreSQL schema) |
| 3-4 | Document Agent: OCR + extraction pipeline |
| 5-6 | Orchestrator: LangGraph workflow + event consumer + policy gate |
| 7-8 | Admin UI: upload portal with batch upload and history |
| 9-10 | Reviewer UI: work queue, document viewer, field editor, decision page |
| 11-12 | Integration testing, accuracy eval, human-in-the-loop walkthrough |
| 13-14 | Performance testing, documentation, PoC exit criteria assessment |

Note: Timeline extends from 12 to 14 weeks to accommodate the two UI applications.

---

## 13. Change Log — Implemented vs Spec

### v1.1 Changes (July 2026)

#### UI Layer Change: React/Next.js → Streamlit
The original spec defined React/Next.js UIs. The implementation uses **Streamlit** for both portals:
- Admin Portal: src/admin_ui/app.py on port 8501
- Reviewer Portal: src/reviewer_ui/reviewer_app.py on port 8502
- Authentication: password-based via st.secrets / env vars (not Keycloak)

#### Database: Supabase → SQLite fallback
- Primary: Supabase PostgreSQL (when SUPABASE_URL configured)
- Fallback: SQLite at data/ipf_poc.db with local file storage at data/documents/
- Auto-detection via src/backend/core/db_factory.py

#### Event Trigger: Redis Pub/Sub → Background Threading
- Upload events trigger processing via 	hreading.Thread(daemon=True) in FastAPI
- No Redis required for PoC; Redis can be added for production scale

#### OCR Pipeline: pypdf primary, Tesseract secondary
- **pypdf**: Extracts text directly from text-based PDFs (primary, no Poppler needed)
- **pytesseract**: Image-based OCR for JPEG/PNG/TIFF (requires Tesseract installed)
- **pdf2image**: PDF-to-image conversion (optional, requires Poppler)
- Language pack: pol+ron+hun+ces+eng

#### New: Mock Credit Scoring Agent
- src/backend/agents/credit_score_agent.py
- 5-factor scoring: Income (300pts) + Employment (200pts) + Identity (200pts) + Consistency (200pts) + Age (100pts)
- Risk bands: EXCELLENT/GOOD/FAIR/POOR/HIGH RISK
- Market-specific bureau names: BIK (PL), Biroul de Credit (RO), BISZ/KHR (HU), CBCB (CZ)
- Exposed via GET /api/credit-score/{application_id}

#### New: PDF Preview Endpoint
- GET /api/document/{document_id}/preview returns PNG of first page
- Primary: pdf2image at 150 DPI
- Fallback: pypdf text extraction + Pillow canvas rendering

#### New: LangSmith Observability
- Enabled via LANGCHAIN_TRACING_V2=true + LANGCHAIN_API_KEY + LANGCHAIN_PROJECT
- Traces all LangGraph node executions and LLM calls
- Graceful no-op when not configured

#### Market Expansion
- Original scope: PL + RO
- Implemented scope: PL + RO + HU + CZ
- Test data generated for all 4 markets across all document sub-types
- 46 mock PDF documents in 	est-data/{market}/{category}/generated/

#### Updated API Endpoints (full list)
| Endpoint | Method | Purpose |
|----------|--------|---------|
| /api/upload | POST | Upload docs, store, trigger workflow |
| /api/status/{app_id} | GET | Get workflow + document status |
| /api/upload/history | GET | List recent workflow submissions |
| /api/queue | GET | Get documents pending review |
| /api/review/{doc_id} | GET | Get extractions + base64 image |
| /api/review/{doc_id}/correct | POST | Submit field corrections |
| /api/review/{doc_id}/confirm | POST | Confirm all fields correct |
| /api/decision/{app_id} | POST | Record assessor decision |
| /api/audit/{app_id} | GET | Full audit trail |
| /api/credit-score/{app_id} | GET | Mock bureau credit score |
| /api/document/{doc_id}/preview | GET | PDF first page as PNG |
| /api/health | GET | Health + OCR + DB mode status |

---

## 14. Final Implementation State (v1.2 — July 2026)

### Source Files

| File | Purpose | Status |
|------|---------|--------|
| src/admin_ui/app.py | Admin upload portal (Streamlit, port 8501) | Complete |
| src/reviewer_ui/reviewer_app.py | Document reviewer portal (Streamlit, port 8502) | Complete |
| src/assessor_ui/assessor_app.py | Credit assessor portal (Streamlit, port 8503) | Complete |
| src/backend/api/main.py | FastAPI REST API (14 endpoints) | Complete |
| src/backend/agents/orchestrator.py | LangGraph 6-node workflow | Complete |
| src/backend/agents/document_agent.py | LLM extraction (GPT-4o-mini) | Complete |
| src/backend/agents/loan_application_agent.py | Loan form declared field extraction | Complete |
| src/backend/agents/cross_reference_agent.py | 5-rule cross-reference engine | Complete |
| src/backend/agents/credit_score_agent.py | Mock bureau scoring (0-1000) | Complete |
| src/backend/agents/validator.py | Market-specific validation rules | Complete |
| src/backend/agents/ocr_utils.py | pypdf + Tesseract OCR pipeline | Complete |
| src/backend/core/config.py | Settings from .env | Complete |
| src/backend/core/sqlite_database.py | SQLite fallback (7 tables) | Complete |
| src/backend/core/db_factory.py | Auto-detect Supabase vs SQLite | Complete |

### LangGraph Workflow (6 nodes)

`
START
  |
  v
[1] extract_loan_app  -- LoanApplicationAgent extracts declared fields
  |
  v
[2] extract           -- DocumentAgent: OCR + LLM per supporting document (loops)
  |
  v
[3] validate          -- Validator: PESEL/CNP/dates/confidence threshold 85%
  |
  v
[4] cross_reference   -- CrossReferenceAgent: 5 field comparisons
  |
  +--(issues)-->  [5] pause_review  --> END (PENDING_REVIEW)
  |
  +--(clear)-->   [6] recommend     --> END (PENDING_DECISION)
`

### Database Tables (SQLite)

| Table | Records per application |
|-------|------------------------|
| documents | 1 per uploaded file |
| extractions | 1 per extracted field per document |
| workflow_state | 1 per batch |
| loan_applications | 1 per application |
| discrepancies | 1 per cross-reference check (5 per application) |
| decisions | 1 per assessor decision |
| audit_log | Multiple (one per workflow event) |

### Three-Portal Architecture

| Portal | Port | Role | Key Pages |
|--------|------|------|-----------|
| Admin | 8501 | Back-office admin | Upload (2-step), History, Status |
| Reviewer | 8502 | Document reviewer | Work Queue, Application Review (3 panels), Audit Trail with flowchart |
| Assessor | 8503 | Credit assessor | Decision Queue, App Summary, Loan Decision, History |

### Known Constraints / Future Work

| Item | Current State | Production Path |
|------|--------------|-----------------|
| LLM | GPT-4o-mini via OpenAI API | Replace with Bedrock or Azure OpenAI |
| OCR | pypdf text extraction (mock PDFs) | Add Poppler for real scanned PDFs |
| Credit scoring | Mock bureau (rule-based) | Replace with live BIK/CBCB/BISZ API |
| Authentication | Password-based | Keycloak OIDC / Cognito |
| Database | SQLite local | Supabase PostgreSQL + S3 storage |
| Event trigger | Python threading | Kafka / Redis Streams |
| LangGraph checkpointer | In-memory | PostgresSaver (needs psycopg2-binary) |
| Deployment | Local Streamlit | Streamlit Cloud + Railway.app |
