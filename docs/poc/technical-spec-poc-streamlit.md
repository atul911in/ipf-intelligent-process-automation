# IPF IPA PoC — Streamlit Edition: Complete Technical Specification

## Document Control

| Item | Detail |
|------|--------|
| Version | 1.0 |
| Date | July 2026 |
| Scope | PoC: Orchestrator + Document Extraction + Streamlit UIs |
| Stack | LangGraph + Streamlit + Supabase (all free except LLM API) |
| Classification | CONFIDENTIAL - Internal Working Draft |

---

## 1. End-to-End Flow

`
STEP 1: UPLOAD                    STEP 2: AUTO-PROCESS               STEP 3: REVIEW
+-------------------+            +------------------------+         +---------------------+
| ADMIN UI          |            | LANGGRAPH ORCHESTRATOR |         | REVIEWER UI         |
| (Streamlit App 1) |            | (Railway.app backend)  |         | (Streamlit App 2)   |
|                   |            |                        |         |                     |
| Admin logs in     |            |                        |         | Reviewer logs in    |
| Selects app ID    |   Event   | 1. Receive event       |         | Sees work queue     |
| Uploads docs      |---------->| 2. Classify docs       |         | Opens document      |
| Assigns types     |            | 3. OCR + Extract       |         | Views extraction    |
| Clicks Submit     |            | 4. Validate fields     |         | Sees confidence     |
|                   |            | 5. Policy gate check   |  Store  | Corrects if needed  |
| Sees confirmation |            | 6. Generate recommend  |-------->| Approves / Declines |
| Sees history      |            | 7. Wait for human      |         | Decision recorded   |
+-------------------+            +------------------------+         +---------------------+
         |                                  |                                 |
         |          +-------------------+   |                                 |
         +--------->| SUPABASE          |<--+---------------------------------+
                    | (Free Tier)       |
                    |                   |
                    | - PostgreSQL      |  All data persists permanently
                    |   (state, audit,  |
                    |    extractions)   |
                    |                   |
                    | - Storage (S3)    |
                    |   (doc images,    |
                    |    PDFs)          |
                    +-------------------+
`

---

## 2. Detailed Step-by-Step Flow

### Step 1: Admin Uploads Documents

`
1. Admin opens Streamlit App 1 (admin portal)
2. Enters password (simple auth via st.secrets)
3. Enters Loan Application ID (e.g., APP-PL-001)
4. Selects Market (PL or RO)
5. Drags/drops up to 20 files (JPEG, PNG, PDF, TIFF)
6. Selects document type per file (ID, Address, Income)
7. Clicks "Submit for Processing"
8. Files upload to Supabase Storage (permanent)
9. Metadata written to Supabase PostgreSQL
10. Event row inserted into "processing_queue" table
11. Admin sees confirmation with batch ID and status
`

### Step 2: Automatic Processing (LangGraph Backend)

`
1. Backend polls "processing_queue" table (every 5 seconds)
2. Picks up new batch -> marks as "PROCESSING"
3. For EACH document in batch:
   a. Download from Supabase Storage
   b. OCR extraction (Tesseract or Unstructured.io)
   c. Language detection (Polish/Romanian)
   d. LLM field extraction (GPT-4o or Ollama)
   e. Confidence scoring per field
   f. Field validation (format, date, cross-reference)
   g. Policy gate check (confidence threshold 85%)
4. If ALL fields pass: status -> "VERIFIED"
5. If ANY field below 85%: status -> "NEEDS_REVIEW"
6. Generate recommendation package (approve/decline/refer)
7. Status -> "AWAITING_DECISION"
8. Write all results to PostgreSQL
`

### Step 3: Reviewer Reviews and Decides

`
1. Reviewer opens Streamlit App 2 (review portal)
2. Enters password (different from admin)
3. Sees work queue: pending documents sorted by priority
4. Clicks on an application
5. Sees side-by-side: original document image + extracted fields
6. Each field shows:
   - Extracted value (editable text input)
   - Confidence score with colour (green/amber/red)
   - Validation status (pass/fail with reason)
7. If corrections needed: edits field, clicks "Submit Corrections"
   -> Re-validates -> Updates status
8. When all docs verified: sees AI recommendation
9. Clicks "Approve" or "Decline"
10. Decision recorded with assessor ID + timestamp
11. Status -> "COMPLETED" (loan approved/declined)
`

---

## 3. Architecture

`
+-------------------+     +-------------------+
| Streamlit App 1   |     | Streamlit App 2   |
| ADMIN UPLOAD      |     | REVIEWER PORTAL   |
| (streamlit.app)   |     | (streamlit.app)   |
+--------+----------+     +--------+----------+
         |                          |
         |  Supabase Python SDK     |
         |                          |
+--------v--------------------------v----------+
|              SUPABASE (Free Tier)             |
|                                              |
|  +------------------+  +------------------+  |
|  | PostgreSQL       |  | Storage (S3)     |  |
|  |                  |  |                  |  |
|  | - documents      |  | - /uploads/      |  |
|  | - extractions    |  |   {app_id}/      |  |
|  | - validations    |  |   {batch_id}/    |  |
|  | - decisions      |  |   {filename}     |  |
|  | - audit_log      |  |                  |  |
|  | - processing_queue|  |                  |  |
|  | - workflow_state  |  |                  |  |
|  +------------------+  +------------------+  |
+----------------------+-----------------------+
                       |
         +-------------v--------------+
         | BACKEND SERVICE            |
         | (Railway.app free tier)    |
         |                            |
         | FastAPI + LangGraph        |
         | - Workflow orchestrator    |
         | - Document extraction agent|
         | - Policy gate             |
         | - Validation engine       |
         |                            |
         | Polls processing_queue     |
         | Writes results to Supabase |
         +----------------------------+
                       |
         +-------------v--------------+
         | LLM API                    |
         | (OpenAI GPT-4o or Ollama)  |
         +----------------------------+
`

---

## 4. Technology Stack

| Component | Technology | Cost |
|-----------|-----------|------|
| Admin UI | Streamlit (Python) | Free (Streamlit Cloud) |
| Reviewer UI | Streamlit (Python) | Free (Streamlit Cloud) |
| Backend / Orchestrator | FastAPI + LangGraph (Python) | Free (Railway.app / Render) |
| Database | Supabase PostgreSQL | Free (500MB) |
| File Storage | Supabase Storage | Free (1GB) |
| OCR | Tesseract 5 (open-source) or Unstructured.io | Free |
| Language Detection | langdetect / fastText | Free |
| LLM (extraction) | OpenAI GPT-4o-mini API | ~5-15 GBP for 200 docs |
| LLM (zero cost option) | Ollama + Llama 3.1 8B (local) | Free (runs on your machine) |
| Event handling | Supabase Realtime / polling | Free |
| Auth | Streamlit secrets (simple password) | Free |

**Total infrastructure cost: 0 GBP**
**Only cost: LLM API calls (~5-15 GBP for full PoC test run)**

---

## 5. Database Schema (Supabase PostgreSQL)

`sql
-- Documents metadata
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL,
    application_id VARCHAR(50) NOT NULL,
    document_type VARCHAR(30) NOT NULL,  -- identity_card, proof_of_address, income_statement
    market VARCHAR(5) NOT NULL,          -- PL, RO
    storage_path TEXT NOT NULL,          -- Supabase Storage path
    original_filename TEXT NOT NULL,
    file_size_bytes INTEGER,
    uploaded_by VARCHAR(100) NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    status VARCHAR(30) DEFAULT 'UPLOADED',
    -- Status flow: UPLOADED -> PROCESSING -> VERIFIED / NEEDS_REVIEW -> CORRECTED -> AWAITING_DECISION -> COMPLETED
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Extraction results per document
CREATE TABLE extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    field_name VARCHAR(100) NOT NULL,
    extracted_value TEXT,
    confidence_score INTEGER,  -- 0-100
    validation_status VARCHAR(20),  -- PASS, FAIL, WARNING
    validation_reason TEXT,
    corrected_value TEXT,       -- NULL if no correction
    corrected_by VARCHAR(100),
    corrected_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Processing queue (event-driven trigger)
CREATE TABLE processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL,
    application_id VARCHAR(50) NOT NULL,
    market VARCHAR(5) NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING',  -- PENDING, PROCESSING, COMPLETED, FAILED
    picked_up_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- AI recommendations
CREATE TABLE recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id VARCHAR(50) NOT NULL,
    recommendation VARCHAR(20) NOT NULL,  -- APPROVE, DECLINE, REFER
    confidence_summary JSONB,             -- overall scores
    supporting_data JSONB,                -- extracted data summary
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Human decisions (loan approval)
CREATE TABLE decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id VARCHAR(50) NOT NULL,
    decision VARCHAR(20) NOT NULL,  -- APPROVE, DECLINE
    reason_codes TEXT[],
    decided_by VARCHAR(100) NOT NULL,
    ai_recommendation VARCHAR(20),  -- what AI suggested
    decided_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit trail (immutable)
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id VARCHAR(50),
    document_id UUID,
    action VARCHAR(50) NOT NULL,  -- UPLOAD, EXTRACT, VALIDATE, CORRECT, APPROVE, DECLINE
    actor VARCHAR(100) NOT NULL,
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Workflow state (LangGraph checkpoints)
CREATE TABLE workflow_state (
    thread_id VARCHAR(100) PRIMARY KEY,
    state JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'RUNNING',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
`

---

## 6. Streamlit App 1: Admin Upload Portal

### Pages

| Page | Route | Function |
|------|-------|----------|
| Upload | / (default) | Batch document upload |
| History | /History | View past submissions |

### Key Features

- Password-protected (st.secrets)
- Loan Application ID input
- Market selector (PL / RO)
- Multi-file drag-and-drop upload
- Document type selector per file
- Upload progress indicator
- Submission confirmation with batch ID
- History table with status tracking
- Filters: date range, application ID, status

### File Structure

`
admin-app/
  app.py              # Main upload page
  pages/
    History.py        # Upload history
  utils/
    supabase_client.py  # Supabase connection
    auth.py             # Simple password auth
  .streamlit/
    secrets.toml        # Passwords + Supabase keys (not in git)
  requirements.txt
`

---

## 7. Streamlit App 2: Reviewer Portal

### Pages

| Page | Route | Function |
|------|-------|----------|
| Queue | / (default) | Work queue of pending documents |
| Review | /Review | Document detail + field editor |
| Decisions | /Decisions | Loan approval history |

### Key Features

- Password-protected (different password from admin)
- Work queue table (sortable, filterable)
- Side-by-side: document image + extracted fields
- Confidence colour coding (green/amber/red)
- Editable fields with "Submit Corrections" button
- Overall application status view
- AI recommendation display
- Approve / Decline buttons
- Decision history with audit trail

### File Structure

`
reviewer-app/
  app.py              # Work queue page
  pages/
    Review.py         # Document review + corrections
    Decisions.py      # Decision history
  utils/
    supabase_client.py
    auth.py
  .streamlit/
    secrets.toml
  requirements.txt
`

---

## 8. Backend Service (FastAPI + LangGraph)

### Responsibilities

1. Poll processing_queue every 5 seconds
2. Download documents from Supabase Storage
3. Run OCR + LLM extraction pipeline
4. Validate fields against schemas
5. Apply policy gates (confidence thresholds)
6. Generate loan recommendation
7. Write all results to Supabase PostgreSQL
8. Update document status throughout

### File Structure

`
backend/
  main.py                 # FastAPI app + queue poller
  orchestrator/
    workflow.py           # LangGraph state graph
    state.py             # Workflow state definition
  agents/
    document_agent.py    # OCR + extraction logic
    validation_agent.py  # Field validation
    recommendation.py    # Generate recommendation
  tools/
    ocr.py              # Tesseract / Unstructured wrapper
    llm.py              # OpenAI / Ollama abstraction
    supabase_ops.py     # DB read/write operations
  policy/
    gate.py             # Policy rule evaluation
    rules.py            # Market-specific rules (PL, RO)
  schemas/
    poland.py           # Polish document schemas
    romania.py          # Romanian document schemas
  requirements.txt
  Dockerfile            # For Railway.app deployment
`

### LangGraph Workflow (Simplified)

`python
from langgraph.graph import StateGraph, END

workflow = StateGraph(WorkflowState)

workflow.add_node("download_docs", download_from_supabase)
workflow.add_node("extract_fields", run_ocr_and_llm)
workflow.add_node("validate_fields", validate_against_schema)
workflow.add_node("policy_check", apply_policy_gates)
workflow.add_node("generate_recommendation", create_recommendation)
workflow.add_node("update_status", write_results_to_supabase)

workflow.set_entry_point("download_docs")
workflow.add_edge("download_docs", "extract_fields")
workflow.add_edge("extract_fields", "validate_fields")
workflow.add_edge("validate_fields", "policy_check")
workflow.add_conditional_edges("policy_check", route_decision, {
    "all_pass": "generate_recommendation",
    "needs_review": "update_status",  # Status = NEEDS_REVIEW, wait for human
})
workflow.add_edge("generate_recommendation", "update_status")
workflow.add_edge("update_status", END)

app = workflow.compile()
`

---

## 9. Deployment

### Step-by-Step Deployment (All Free)

| Step | Action | Time |
|------|--------|------|
| 1 | Create Supabase project (supabase.com) | 5 min |
| 2 | Run SQL schema (Section 5) in Supabase SQL editor | 5 min |
| 3 | Create Supabase Storage bucket "documents" | 2 min |
| 4 | Push admin-app to GitHub | 5 min |
| 5 | Connect to Streamlit Cloud (share.streamlit.io) | 5 min |
| 6 | Push reviewer-app to GitHub | 5 min |
| 7 | Connect to Streamlit Cloud | 5 min |
| 8 | Push backend to GitHub | 5 min |
| 9 | Deploy backend on Railway.app (connect GitHub) | 10 min |
| 10 | Add secrets (Supabase URL, OpenAI key) to all services | 10 min |
| **Total** | **Everything live** | **~1 hour** |

### URLs After Deployment

`
Admin Portal:    https://ipf-admin.streamlit.app
Reviewer Portal: https://ipf-reviewer.streamlit.app
Backend API:     https://ipf-backend.up.railway.app
Supabase DB:     https://xxxx.supabase.co (managed)
`

---

## 10. Security (PoC Level)

| Concern | Implementation |
|---------|---------------|
| Admin auth | Password in st.secrets (not in code) |
| Reviewer auth | Different password in st.secrets |
| API keys | Stored in Streamlit secrets + Railway env vars |
| Supabase access | Row-level security (RLS) policies |
| Document access | Signed URLs (expire in 1 hour) |
| HTTPS | Automatic (Streamlit Cloud + Railway both enforce) |

---

## 11. Cost Summary

| Component | Monthly Cost |
|-----------|-------------|
| Streamlit Cloud (2 apps) | 0 GBP |
| Supabase (PostgreSQL + Storage) | 0 GBP |
| Railway.app (backend) | 0 GBP (5 USD free credit) |
| Tesseract OCR | 0 GBP |
| LangGraph / LangChain | 0 GBP |
| OpenAI GPT-4o-mini (200 docs) | 5-15 GBP |
| **TOTAL** | **5-15 GBP (LLM only)** |

Zero-cost option: Replace OpenAI with Ollama running on your laptop (backend points to localhost:11434 instead of api.openai.com).

---

## 12. Timeline

| Day | Deliverable |
|-----|-------------|
| 1-2 | Supabase setup, DB schema, storage bucket |
| 3-4 | Backend: OCR + LLM extraction pipeline |
| 5-6 | Backend: LangGraph workflow + validation + policy gate |
| 7-8 | Admin UI: Streamlit upload portal |
| 9-10 | Reviewer UI: work queue + document viewer + corrections |
| 11-12 | Integration: end-to-end flow, deploy to cloud |
| 13-14 | Testing with 200 sample documents, bug fixes |

**Total: 14 days (2 weeks) to working PoC**

---

## 13. Limitations (Honest)

| Limitation | Impact | Acceptable for PoC? |
|-----------|--------|---------------------|
| Streamlit sleeps after inactivity | 30s cold start on first visit | Yes |
| 1GB RAM on Streamlit Cloud | UI only, no heavy processing | Yes (backend is separate) |
| Basic password auth | Not enterprise RBAC | Yes for demo |
| Supabase 500MB DB limit | Enough for 200+ docs easily | Yes |
| Railway 5 USD free credit | ~500 compute hours | Yes for PoC duration |
| No real-time WebSocket | Polling-based updates (5s delay) | Yes for demo |

---

## 14. What Happens After PoC

When the PoC proves the concept and you get buy-in:

| PoC Component | Production Upgrade |
|---------------|-------------------|
| Streamlit UIs | React/Next.js professional UIs |
| Password auth | Keycloak / Cognito RBAC |
| Supabase free | Supabase Pro or self-hosted PostgreSQL |
| Railway.app | Kubernetes on AWS/Azure/GCP |
| Supabase Storage | S3 / MinIO with lifecycle policies |
| GPT-4o API | Bedrock / self-hosted models |
| Polling events | Kafka / Redis Streams |

The backend code (LangGraph, agents, schemas, policy gate) transfers directly - only hosting and UI change.
