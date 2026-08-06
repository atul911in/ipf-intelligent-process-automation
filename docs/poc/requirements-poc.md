# PoC Requirements: IPF Intelligent Process Automation

## Document Control

| Item | Detail |
|------|--------|
| Version | 2.0 |
| Date | July 2026 |
| Classification | CONFIDENTIAL - Internal Working Draft |
| Scope | Proof of Concept - Full Stack: FastAPI backend, LangGraph orchestrator, 5 AI agents, React/Next.js UI, SQLite persistence, NBFI decisioning engine |
| Prepared by | Mastek AI CoE |
| Change summary | v2.0: Complete rewrite to reflect production-ready PoC. Added Requirements 24-30 covering: React/Next.js UI portals, 5-stage NBFI decisioning engine (Polish market), IPF branding, document approval/rejection workflow, VERIFIED status persistence, and deployment readiness. Removed Streamlit portal requirements (superseded). |

---

## Introduction

This document defines the requirements for the IPF Intelligent Process Automation Proof of Concept (PoC). The PoC demonstrates end-to-end AI-powered loan origination processing across four European home credit markets: Poland (PL), Romania (RO), Hungary (HU), and Czech Republic (CZ).

The system consists of:
- A **FastAPI backend** (port 8000) exposing 14 REST endpoints
- A **LangGraph orchestrator** coordinating 5 AI agents via a 6-node workflow graph
- A **React/Next.js UI** (port 3000) with three role-based portals
- A **SQLite database** for local persistence with db_factory abstraction
- A **5-stage NBFI decisioning engine** calibrated to Polish regulatory architecture

## Glossary

- **Orchestrator**: LangGraph StateGraph that coordinates the 5 AI agents and maintains WorkflowState
- **Document_Agent**: AI agent that extracts fields from supporting documents using OCR + GPT-4o-mini
- **LoanApplication_Agent**: AI agent that extracts declared fields from the loan application form
- **Validator_Agent**: Agent that applies market-specific validation rules to extracted fields
- **CrossReference_Agent**: Agent that compares loan application declarations against supporting document extractions
- **CreditScore_Agent**: Agent that runs the 5-stage NBFI decisioning engine and returns score, risk band, and product route
- **Admin_Portal**: React portal (port 3000/admin) for back-office document upload
- **Reviewer_Portal**: React portal (port 3000/reviewer) for document review, OCR verification, and discrepancy management
- **Assessor_Portal**: React portal (port 3000/assessor) for credit assessment and final loan decisions
- **SQLite_DB**: Primary local database (data/ipf_poc.db). Abstracted via db_factory.py
- **NBFI_Engine**: 5-stage non-bank financial institution decisioning pipeline (Stage 0-4)
- **Market**: PL (Poland), RO (Romania), HU (Hungary), CZ (Czech Republic)
- **Credit_Assessor**: Human decision-maker who reviews AI recommendations and records final APPROVE/DECLINE

---

## Requirements

### Requirement 1: Orchestrator Core Workflow Engine

**User Story:** As a platform engineer, I want a LangGraph orchestrator that manages AI agent execution through a defined workflow graph, so that processing is predictable, auditable, and recoverable.

#### Acceptance Criteria

1. THE Orchestrator SHALL implement a LangGraph StateGraph with nodes: extract_loan_app, extract (loop per document), validate, cross_reference, pause_for_review, recommend
2. THE Orchestrator SHALL maintain a typed WorkflowState (TypedDict) shared across all agents containing: batch_id, application_id, market, document_ids, extractions, validations, discrepancies, recommendation, status
3. WHEN a workflow step fails, THE Orchestrator SHALL catch the exception, set workflow status to FAILED, log full traceback to audit_log, and notify operations
4. THE Orchestrator SHALL process workflows in background daemon threads so that upload API responses are not blocked
5. WHEN a workflow completes, THE Orchestrator SHALL update workflow_state.status to PENDING_REVIEW or PENDING_DECISION and log RECOMMEND or PAUSE_FOR_REVIEW audit events

### Requirement 2: FastAPI Backend REST Endpoints

**User Story:** As a frontend developer, I want a FastAPI backend exposing standardised REST endpoints, so that the React UI can communicate with all AI agents via HTTP.

#### Acceptance Criteria

1. THE backend SHALL expose exactly 14 REST endpoints:
   - POST /api/upload (multipart form data, triggers workflow)
   - GET /api/status/{application_id}
   - GET /api/upload/history
   - GET /api/queue (with optional status filter)
   - GET /api/review/{document_id}
   - POST /api/review/{document_id}/correct
   - POST /api/review/{document_id}/confirm
   - POST /api/decision/{application_id}
   - GET /api/audit/{application_id}
   - GET /api/document/{document_id}/preview
   - GET /api/credit-score/{application_id}
   - GET /api/loan-application/{application_id}
   - GET /api/discrepancies/{application_id}
   - POST /api/discrepancies/{application_id}/override
   - GET /api/health
2. THE backend SHALL enable CORS for all origins to support the React frontend at localhost:3000
3. THE backend SHALL be launched via uvicorn on port 8000 with --reload flag for development

### Requirement 3: Document Upload (Two-Step Admin Portal)

**User Story:** As a back-office administrator, I want to upload a loan application form and supporting documents in two distinct steps, so that the system has the correct reference document and can enable cross-reference checking.

#### Acceptance Criteria

1. THE Admin_Portal SHALL present Step 1 for uploading the loan application form (single file, document type: loan_application)
2. THE Admin_Portal SHALL present Step 2 for uploading multiple supporting documents with per-file document type selection from a market-specific dropdown
3. THE Admin_Portal SHALL require a Loan Application ID and Market selection before submission
4. WHEN submitted, THE Admin_Portal SHALL POST to /api/upload with all files and metadata via multipart/form-data
5. THE Admin_Portal SHALL display success confirmation with batch_id when upload completes
6. THE Admin_Portal SHALL support Upload History and Processing Status pages using GET /api/upload/history and GET /api/status/{id}

### Requirement 4: LoanApplication Agent

**User Story:** As a credit reviewer, I want the loan application form to be extracted first so its declared fields are available as the reference for cross-checking.

#### Acceptance Criteria

1. THE LoanApplication_Agent SHALL extract: applicant_full_name, date_of_birth, residential_address, declared_net_monthly_income, declared_income_currency, requested_loan_amount, loan_term_weeks, employment_status, employer_name, bank_account_number, purpose_of_loan
2. Extracted fields SHALL be stored via db.save_loan_application() and accessible via GET /api/loan-application/{application_id}
3. THE agent SHALL use GPT-4o-mini via LangChain ChatOpenAI with structured JSON output
4. THE Orchestrator SHALL run this agent as the entry point node before any document extraction

### Requirement 5: Document Agent (OCR + LLM Extraction)

**User Story:** As a document reviewer, I want each supporting document to be extracted automatically with confidence scores per field.

#### Acceptance Criteria

1. THE Document_Agent SHALL process each document in sequence via the extract node loop
2. THE agent SHALL use the OCR pipeline: pypdf for text PDFs, pytesseract/Tesseract for images (TIFF, JPG, PNG)
3. THE agent SHALL support languages: pol, ron, hun, ces, eng
4. THE agent SHALL invoke GPT-4o-mini to extract structured fields from OCR text
5. EACH extracted field SHALL have a confidence score (0-100) stored via db.save_extraction()
6. THE agent SHALL set document status to EXTRACTED after processing

### Requirement 6: Validator Agent

**User Story:** As a compliance officer, I want extracted fields validated against market-specific rules before human review.

#### Acceptance Criteria

1. THE Validator SHALL apply rules for: PESEL checksum (PL), CNP format (RO), rodne_cislo mod-11 (CZ), document expiry, date of birth minimum age 18, name fuzzy match, address match, income discrepancy (>10% triggers FAIL)
2. EACH validation result SHALL be stored with status (PASS/FAIL/WARNING) and reason text
3. Documents with any FAIL validation SHALL be set to PENDING_REVIEW status
4. Documents with all PASS validations SHALL be set to VERIFIED status, unless confidence < 85% threshold

### Requirement 7: Cross-Reference Agent

**User Story:** As a compliance officer, I want the system to automatically compare loan application declarations against extracted document data to surface fraud indicators.

#### Acceptance Criteria

1. THE CrossReference_Agent SHALL compare: name, date_of_birth, residential_address, net_monthly_income, bank_account_number between loan application and supporting documents
2. EACH comparison SHALL produce a discrepancy record with: field_pair, declared_value, extracted_value, status (MATCH/MISMATCH/WARNING/UNVERIFIABLE), severity (HIGH/MEDIUM/LOW)
3. Income mismatches >10% SHALL be HIGH severity
4. Name mismatches SHALL be HIGH severity
5. Address mismatches SHALL be MEDIUM severity
6. Discrepancies SHALL be stored via db.save_discrepancies() and accessible via GET /api/discrepancies/{application_id}
7. HIGH severity discrepancies SHALL be visible in the Reviewer Portal Panel C

### Requirement 8: 5-Stage NBFI Decisioning Engine (Polish Market)

**User Story:** As a credit assessor, I want a decision engine calibrated to the Polish NBFI regulatory framework to run sequentially through 5 stages, so that every decisioning step is visible and auditable.

#### Acceptance Criteria

1. THE CreditScore_Agent SHALL implement 5 sequential stages with short-circuit on hard rejection:
   - Stage 0: Regulatory Gateway (age 18-75, PESEL checksum, ID expiry, AML/PEP filter)
   - Stage 1: Fraud & Identity (name consistency across documents, Open Banking simulation)
   - Stage 2: Bureau Routing (mock BIK score 1-100, mock BIG debt registry KRD/ERIF)
   - Stage 3: Legal Caps & Affordability (MPKK anti-usury formula, DTI: <3500 PLN = 40% cap, >=3500 PLN = 50% cap)
   - Stage 4: Decision Matrix (BIK band x BIG debt x DTI → product route)
2. BIK scoring SHALL use mock signals: validation failures reduce score, income/employer presence boost score
3. Stage 4 SHALL route to one of: REJECT, APPROVE_WITH_CAP (max 2000 PLN), APPROVE_STANDARD (max 5000 PLN), APPROVE_UPSELL, APPROVE_PROBATIONARY
4. THE engine SHALL return stage_results array with each stage's checks, pass/fail, and rejection_reason for UI display
5. Expiry_date validation SHALL be performed directly from the extracted date string, not from validation record status (PENDING shall not be treated as failure)

### Requirement 9: VERIFIED Status Persistence

**User Story:** As a reviewer, I want documents I have approved to remain VERIFIED even after the AI workflow re-runs, so that my decisions are not overwritten.

#### Acceptance Criteria

1. THE Orchestrator validate_extractions step SHALL check current document status before overwriting
2. IF a document status is already VERIFIED, THE Orchestrator SHALL skip the status update for that document
3. Only the reviewer's explicit Approve Document or Reject Document action SHALL be able to set or remove VERIFIED status
4. This rule SHALL apply in orchestrator.py validate_extractions() function

### Requirement 10: Document Review Portal

**User Story:** As a document reviewer, I want a dedicated portal to review OCR extractions, compare documents side-by-side, and approve or reject each document.

#### Acceptance Criteria

1. THE Reviewer_Portal SHALL provide 4 tabs: Work Queue, Application Review, Review Document, Audit Trail
2. THE Work Queue SHALL display all documents grouped by application_id with status badges
3. THE Application Review tab SHALL display 3 panels:
   - Panel A: Document Preview (LEFT) + Declared Fields (RIGHT) for loan application
   - Panel B: Supporting documents with expandable OCR extractions
   - Panel C: Cross-reference discrepancy report with override capability
4. EVERY document in Panel A and Panel B SHALL have a "Review Document" button that navigates to the Review Document tab pre-loaded with the correct document_id
5. THE Review Document tab SHALL display: confidence summary (High/Medium/Low field counts), document preview, extracted fields with confidence badges, correction inputs, Approve Document button (IPF teal), Reject Document button (red)
6. THE Audit Trail tab SHALL display all events with a vertical processing flow diagram

### Requirement 11: Credit Assessor Portal

**User Story:** As a credit assessor, I want a dedicated portal showing only the decision-relevant information with the 5-stage engine breakdown visible.

#### Acceptance Criteria

1. THE Assessor_Portal SHALL provide 4 tabs: Decision Queue, Application Summary, Loan Decision, Decision History
2. THE Application Summary SHALL display: applicant details, credit score gauge (SVG circular gauge), score breakdown, risk flags with expandable explanations, discrepancy summary
3. THE Application Summary SHALL display the 5-stage NBFI engine results as an expandable accordion, showing each stage with rule-by-rule breakdown
4. THE Loan Decision tab SHALL provide Approve/Decline buttons with reason code multiselect and notes field
5. THE Decision Queue SHALL show credit score and risk band for each application

### Requirement 12: IPF Branding

**User Story:** As a product owner, I want the UI to use IPF brand colours and identity so the demo looks professional for customer presentations.

#### Acceptance Criteria

1. ALL portals SHALL use IPF primary colour #00544E (dark teal) for headers and primary buttons
2. ALL portals SHALL use IPF accent colour #7DC242 (bright green) for the IPF logo badge and highlights
3. THE landing page SHALL show the IPF logo badge, dark teal gradient hero, and portal cards with green chevrons
4. ALL login screens SHALL have the IPF badge and dark teal gradient background

### Requirement 13: Data Persistence (SQLite)

**User Story:** As a developer, I want all data persisted in SQLite with a clean factory pattern so the database can be swapped to PostgreSQL in production.

#### Acceptance Criteria

1. THE db_factory.py SHALL return SQLiteDatabase when USE_SQLITE=true
2. ALL agents and API endpoints SHALL call db methods, never SQL directly
3. THE SQLite database SHALL persist: documents, extractions, workflow_state, loan_applications, discrepancies, decisions, audit_log, file_storage (BLOBs)
4. File BLOBs SHALL be stored in the file_storage table and retrieved via get_file_bytes()
5. THE config.py SHALL load .env via python-dotenv at import time (not at uvicorn startup) to ensure OPENAI_API_KEY is available to agents

### Requirement 14: Audit Trail

**User Story:** As a compliance officer, I want every system action logged immutably so decisions can be reconstructed for audit purposes.

#### Acceptance Criteria

1. THE audit_log SHALL capture: UPLOAD, EXTRACT_LOAN_APP, EXTRACT, CROSS_REFERENCE, PAUSE_FOR_REVIEW, CORRECT, CONFIRM, RECOMMEND, APPROVE, DECLINE, WORKFLOW_FAILED, DISCREPANCY_OVERRIDE
2. EACH event SHALL include: action, actor, application_id, document_id (where applicable), timestamp, details (JSON)
3. THE Audit Trail tab in the Reviewer Portal SHALL display all events with a processing flow diagram
4. Events SHALL be accessible via GET /api/audit/{application_id}