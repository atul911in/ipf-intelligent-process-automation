# Technical Specification: IPF IPA — LangChain/LangGraph Stack

## Document Control

| Item | Detail |
|------|--------|
| Version | 1.0 |
| Date | July 2026 |
| Classification | CONFIDENTIAL — Internal Working Draft |
| Prepared by | Mastek AI CoE |

---

## 1. Executive Summary

This specification defines the technical architecture for IPF's Intelligent Process Automation (IPA) programme using a **cloud-agnostic, open-source-first stack** centred on LangChain/LangGraph for multi-agent orchestration. The solution is deployable on any cloud provider or on-premises infrastructure, with no vendor lock-in on the AI layer.

---

## 2. Architecture Overview

### 2.1 Design Principles

1. **Cloud-agnostic** — No dependency on any single cloud provider's proprietary AI services
2. **Model-swappable** — LLM provider can be changed without rewriting agent logic
3. **Policy-first** — Every agent action passes through a policy gate before execution
4. **Human-in-the-loop native** — LangGraph interrupts enforce mandatory human checkpoints
5. **Audit-complete** — Every decision traced end-to-end via LangSmith
6. **Offline-resilient** — Field agents operate with cached plans when connectivity drops
7. **Multilingual-native** — Language handling is a shared service, not per-agent duplication

### 2.2 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (Kong / Traefik)                      │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                    LANGGRAPH ORCHESTRATOR SERVICE                         │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  State Graph: routing, conditional edges, human-in-the-loop       │   │
│  │  Checkpoint Store: PostgreSQL                                     │   │
│  │  Policy Gate Middleware: validates every agent action             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└────┬──────────┬──────────┬──────────┬──────────┬──────────┬────────────┘
     │          │          │          │          │          │
┌────▼───┐ ┌────▼───┐ ┌────▼───┐ ┌────▼───┐ ┌────▼───┐ ┌────▼───┐
│  Doc   │ │ Route  │ │Collect │ │Service │ │ Recon  │ │ Nudge  │
│ Agent  │ │ Agent  │ │ Agent  │ │ Desk   │ │ Agent  │ │ Agent  │
│        │ │        │ │        │ │ Agent  │ │        │ │        │
└────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘ └────┬───┘
     │          │          │          │          │          │
┌────▼──────────▼──────────▼──────────▼──────────▼──────────▼────────────┐
│                         TOOLS & SERVICES LAYER                           │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐  │
│  │Unstructd│ │OR-Tools │ │ Twilio  │ │ Vector  │ │ FOCUS Bridge    │  │
│  │OCR/NLP  │ │Solver   │ │Voice/SMS│ │   DB    │ │ (Kafka adapter) │  │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────────────┐
│                         DATA & INFRASTRUCTURE                            │
│  PostgreSQL │ Snowflake │ Kafka │ Redis │ Kubernetes │ MinIO/S3          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 LangGraph Orchestrator

| Attribute | Specification |
|-----------|--------------|
| Framework | LangGraph 0.3+ |
| State store | PostgreSQL (LangGraph checkpointer) |
| Graph type | StateGraph with conditional edges |
| Human-in-the-loop | `interrupt_before` nodes for loan approval, vulnerability escalation |
| Deployment | Containerised (Docker) on Kubernetes |
| Scaling | Horizontal pod autoscaling; async task execution via Redis queues |

**Graph Structure:**

```python
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

class IPFWorkflowState(TypedDict):
    documents: list[Document]
    extraction_result: ExtractionResult
    verification_result: VerificationResult
    recommendation: LoanRecommendation
    human_decision: Optional[HumanDecision]
    policy_context: PolicyContext
    market: str
    language: str

workflow = StateGraph(IPFWorkflowState)

# Loan origination flow
workflow.add_node("extract_documents", document_extraction_agent)
workflow.add_node("verify_documents", document_verification_agent)
workflow.add_node("generate_recommendation", recommendation_agent)
workflow.add_node("human_review", human_approval_checkpoint)  # ALWAYS interrupts
workflow.add_node("record_decision", write_to_focus)

# Edges
workflow.add_edge("extract_documents", "verify_documents")
workflow.add_conditional_edges("verify_documents", check_verification, {
    "passed": "generate_recommendation",
    "failed": "notify_agent_rejection"
})
workflow.add_edge("generate_recommendation", "human_review")  # NEVER skip
workflow.add_edge("human_review", "record_decision")
```

### 3.2 Domain Agents

#### Document Processing Agent

| Attribute | Specification |
|-----------|--------------|
| LLM | GPT-4o or Claude 3.5 Sonnet (via LangChain model abstraction) |
| Tools | `ocr_extract` (Unstructured.io), `language_detect`, `field_validate`, `schema_lookup` |
| Input | Document image/PDF + market context |
| Output | Structured extraction with confidence scores per field |
| Policy gate | If any field confidence < 85% → route to human operator |
| SLA | < 30 seconds per document |

**OCR Pipeline:**
```
Document Image → Unstructured.io (partition + OCR) 
    → LangChain LLM (field extraction + language-specific parsing)
    → Confidence scoring 
    → Structured output (Pydantic model)
```

#### Route Planning Agent

| Attribute | Specification |
|-----------|--------------|
| LLM | GPT-4o (for natural language plan explanations only) |
| Tools | `optimise_route` (OR-Tools VRP solver), `get_travel_matrix`, `get_customer_windows`, `get_safety_zones` |
| Input | Agent's agency book, customer availability predictions, constraints |
| Output | Ordered visit sequence with time windows and rationale |
| Solver | Google OR-Tools CVRPTW (Capacitated Vehicle Routing with Time Windows) |
| SLA | < 60 seconds per weekly plan |

#### Collections Contact Agent

| Attribute | Specification |
|-----------|--------------|
| LLM | GPT-4o or Claude (multilingual dialogue) |
| Tools | `send_sms` (Twilio), `initiate_call` (Twilio Voice), `record_arrangement`, `check_vulnerability`, `escalate_to_human` |
| Languages | Polish, Romanian, Hungarian, Spanish, Czech |
| Policy gate | Vulnerability flag → immediate human transfer; frequency caps enforced; conduct rules per market |
| Voice | Deepgram (STT) + ElevenLabs (TTS) for natural multilingual speech |
| SLA | Escalation to human < 30 seconds |

#### Service Desk Agent

| Attribute | Specification |
|-----------|--------------|
| LLM | GPT-4o or Claude |
| Tools | `classify_ticket`, `search_knowledge_base` (RAG), `execute_resolution`, `route_to_group`, `request_confirmation` |
| RAG stack | LangChain Retriever → pgvector (PostgreSQL) or Weaviate |
| Confidence threshold | ≥ 90% for auto-resolution; below → route to human |
| Languages | Polish, Romanian, Hungarian, Spanish, Czech, English |
| SLA | Classification < 10 seconds |

#### Reconciliation Agent

| Attribute | Specification |
|-----------|--------------|
| LLM | GPT-4o (for exception narrative generation) |
| Tools | `auto_match_transactions`, `compute_anomaly_score`, `flag_exception`, `clear_benign`, `escalate_to_integrity` |
| ML models | Anomaly detection (Isolation Forest / custom) served via BentoML |
| Input | Expected vs actual collections per agent/branch |
| Output | Matched transactions, exception list with severity scores |

### 3.3 Shared Services

#### Policy Gate Middleware

```python
class PolicyGate:
    """
    Validates every agent action against market-specific rules.
    Loaded from policy catalogue (PostgreSQL/Redis).
    """
    def check(self, action: AgentAction, market: str) -> PolicyDecision:
        rules = self.load_rules(market, action.type)
        for rule in rules:
            if rule.violated_by(action):
                return PolicyDecision(
                    permitted=False,
                    reason=rule.violation_reason,
                    action="escalate" if rule.escalation else "block"
                )
        return PolicyDecision(permitted=True)
```

| Attribute | Specification |
|-----------|--------------|
| Store | PostgreSQL with Redis cache (< 5ms lookup) |
| Versioning | Every policy version immutable; decision records which version applied |
| Markets | Poland, Romania, Hungary, Spain, Czech Republic (extensible) |
| Update mechanism | Admin API; blue/green deployment; no agent restart required |

#### Language Services

| Attribute | Specification |
|-----------|--------------|
| Detection | LangChain + fastText language detection |
| Translation | LLM-based (contextual) or DeepL API for document translation |
| Speech-to-text | Deepgram (supports PL, RO, HU, ES, CS) |
| Text-to-speech | ElevenLabs multilingual v2 |
| Conversation | LLM prompts with market/language-specific system messages |

#### Observability (LangSmith)

| Attribute | Specification |
|-----------|--------------|
| Tracing | Every agent invocation, tool call, and LLM call traced |
| Evaluation | Automated evals for classification accuracy, extraction quality |
| Cost tracking | Per-agent, per-market token usage and cost |
| Alerting | Error rate > 5% triggers ops alert via webhook |
| Retention | 90 days hot (LangSmith), 7 years cold (compliance archive) |

---

## 4. Data Architecture

### 4.1 Data Stores

| Store | Technology | Purpose |
|-------|-----------|---------|
| Operational DB | PostgreSQL 16 | Agent state, workflow checkpoints, policy catalogue, service cases |
| Analytical warehouse | Snowflake | SDS equivalent; visit history, collections, metrics, reporting |
| Vector store | pgvector (PostgreSQL extension) | Knowledge base embeddings for Service Desk RAG |
| Cache | Redis Cluster | Policy rules cache, session state, rate limiting |
| Object store | MinIO (on-prem) or S3-compatible | Document images, audio recordings, model artefacts |
| Event stream | Apache Kafka | FOCUS integration events, agent-to-agent messages, audit events |

### 4.2 FOCUS System Integration

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│ IPA Agents  │────▶│ Kafka Topics │────▶│ FOCUS Bridge │────▶ FOCUS
│             │◀────│              │◀────│ (Adapter)    │◀──── System
└─────────────┘     └──────────────┘     └──────────────┘
```

| Pattern | Detail |
|---------|--------|
| Write to FOCUS | Agents publish events to Kafka → FOCUS Bridge validates against schema → writes to FOCUS |
| Read from FOCUS | Batch extract (daily) + CDC (change data capture) into Snowflake/SDS |
| Failure handling | Dead letter queue; exponential backoff; ops alert after 5 retries |
| Audit | Every exchange logged with timestamp, payload hash, outcome |

---

## 5. ML & Prediction Services

| Model | Purpose | Framework | Serving |
|-------|---------|-----------|---------|
| Visit-window predictor | Best time to visit each customer | scikit-learn / XGBoost | BentoML on Kubernetes |
| Collection propensity | Likelihood of payment per visit | XGBoost | BentoML |
| Cure probability | Likelihood of arrears resolution | LightGBM | BentoML |
| Anomaly detection | Reconciliation exception scoring | Isolation Forest | BentoML |
| Document classifier | ID vs proof-of-address vs income | Fine-tuned LayoutLM | BentoML |

| Concern | Approach |
|---------|----------|
| Feature store | Feast (open-source) on Snowflake/PostgreSQL |
| Experiment tracking | MLflow |
| Model registry | MLflow Model Registry |
| Drift monitoring | Evidently AI (open-source) |
| Fairness monitoring | Fairlearn; per-market demographic parity checks |

---

## 6. Infrastructure & Deployment

### 6.1 Kubernetes Architecture

```
Namespace: ipf-ipa
├── Deployment: orchestrator (LangGraph service) — 3 replicas, HPA
├── Deployment: doc-agent — 5 replicas, HPA
├── Deployment: route-agent — 3 replicas
├── Deployment: collections-agent — 5 replicas, HPA
├── Deployment: service-desk-agent — 3 replicas, HPA
├── Deployment: recon-agent — 2 replicas
├── Deployment: policy-service — 3 replicas
├── StatefulSet: postgresql — 3 nodes (HA)
├── StatefulSet: kafka — 3 brokers
├── StatefulSet: redis-cluster — 6 nodes
├── CronJob: model-retraining (weekly)
├── CronJob: route-plan-generation (weekly per market)
└── Job: focus-batch-sync (daily)
```

### 6.2 Non-Functional Requirements

| Requirement | Target |
|-------------|--------|
| Availability | 99.9% for customer-facing agents; 99.5% for back-office |
| Latency (doc extraction) | < 30 seconds p95 |
| Latency (ticket classification) | < 10 seconds p95 |
| Latency (route generation) | < 60 seconds p95 |
| Throughput | 10,000 documents/day; 50,000 ticket classifications/day |
| Data residency | EU region for all personal data (GDPR) |
| Encryption | AES-256 at rest; TLS 1.3 in transit |
| Backup | RPO 1 hour; RTO 4 hours |
| Disaster recovery | Active-passive across availability zones |

---

## 7. Security & Compliance

| Concern | Implementation |
|---------|---------------|
| Authentication | OAuth 2.0 / OIDC via Keycloak |
| Authorisation | Role-based (RBAC) per market, per agent type |
| API security | mTLS between services; API key + rate limiting at gateway |
| Data encryption | PostgreSQL TDE; Kafka encryption; MinIO server-side encryption |
| GDPR | Data residency in EU; right-to-delete via purge pipeline; consent tracking |
| Audit trail | Immutable event log in Kafka + cold archive; 7-year retention |
| EU AI Act | Model registry with classification, human oversight documentation, bias reports |
| PCI considerations | No card data stored; tokenisation via payment provider |

---

## 8. Cost Estimate (Annual Run Rate at Scale)

| Component | Estimated Annual Cost |
|-----------|----------------------|
| LLM API calls (OpenAI/Anthropic) | £150k–250k (volume-dependent) |
| Kubernetes cluster (3 cloud regions) | £80k–120k |
| Snowflake (data warehouse) | £60k–100k |
| Twilio (voice + SMS, 5 markets) | £100k–180k |
| Deepgram + ElevenLabs (speech) | £40k–80k |
| LangSmith (observability) | £20k–40k |
| Kafka (managed) | £30k–50k |
| Other (Redis, DNS, monitoring, etc.) | £20k–40k |
| **Total estimated run cost** | **£500k–860k p.a.** |

*Note: Against £15–32m annual benefit, this represents a 2–6% cost-to-benefit ratio.*

---

## 9. Delivery Phases

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 0 | 6–8 weeks | LangGraph skeleton; policy gate; FOCUS bridge prototype; data audit |
| Wave 1 MVP-A | 3–4 months | Document Agent live in one EU market |
| Wave 1 MVP-B | 3–4 months | Route Agent pilot in Mexico branches |
| Wave 2 | Months 5–9 | Service Desk Agent; Reconciliation Agent; Nudge Agent |
| Wave 3 | Months 9–18 | Collections Agent (policy-gated, champion/challenger) |

---

## 10. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| LangChain breaking changes | Medium | Medium | Pin versions; abstract behind internal interfaces; integration tests |
| LLM cost escalation | Medium | Medium | Token budgets per agent; model downgrades for simple tasks; caching |
| Multilingual voice quality | Medium | High | Extensive UAT per market; fallback to human for low-quality interactions |
| FOCUS integration complexity | High | High | Thin async bridge; never depend on real-time FOCUS responses |
| Agent adoption resistance | High | High | Co-design; suggestions-not-mandates; commission transparency as quick win |
| Regulatory change (EU AI Act) | Medium | High | Model registry with classification; human oversight documentation pre-built |

