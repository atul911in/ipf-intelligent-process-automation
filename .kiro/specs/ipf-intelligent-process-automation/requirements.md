# Requirements Document

## Introduction

This document defines the requirements for the IPF Intelligent Process Automation programme. The PoC phase validates the multi-agent architecture, AI-powered document processing, and NBFI decisioning engine across four European home credit markets: Poland (PL), Romania (RO), Hungary (HU), and Czech Republic (CZ).

The PoC is built as a production-ready demonstration system with:
- FastAPI backend (port 8000) with 14 REST endpoints
- LangGraph orchestrator with 5 AI agents
- React/Next.js UI (port 3000) with IPF branding
- SQLite persistence with db_factory abstraction
- 5-stage NBFI decisioning engine (Polish market)

## Glossary

- **IPA_Platform**: The Intelligent Process Automation platform orchestrating 5 AI agents
- **Loan_Origination_Engine**: The automated document verification and loan processing subsystem
- **Document_Agent**: OCR + LLM extraction agent for supporting documents
- **LoanApplication_Agent**: Extracts declared fields from the loan application form
- **Validator_Agent**: Applies market-specific field validation rules
- **CrossReference_Agent**: Compares loan application declarations against document extractions
- **CreditScore_Agent**: Runs the 5-stage NBFI decisioning engine
- **Admin_Portal**: React portal at /admin for document upload
- **Reviewer_Portal**: React portal at /reviewer for document review
- **Assessor_Portal**: React portal at /assessor for credit decisions
- **NBFI_Engine**: 5-stage Non-Bank Financial Institution decisioning pipeline
- **FOCUS_System**: IPF legacy core banking system (mock in PoC)
- **Market**: PL (Poland), RO (Romania), HU (Hungary), CZ (Czech Republic)
- **Credit_Assessor**: Human decision-maker who records final APPROVE/DECLINE
- **OCR**: Optical Character Recognition
- **SQLite_DB**: Local SQLite database (data/ipf_poc.db)
- **BIK**: Biuro Informacji Kredytowej (Polish credit bureau)
- **BIG**: Biuro Informacji Gospodarczej (Polish debt registry)

## Requirements

### Requirement 1: Multi-Language Document Extraction

**User Story:** As a loan processing team member, I want documents submitted by customers to be automatically extracted and structured, so that manual data entry is eliminated.

#### Acceptance Criteria

1. THE Document_Agent SHALL extract text using OCR (pypdf for PDFs, pytesseract for images) with languages: pol, ron, hun, ces, eng
2. THE Document_Agent SHALL invoke GPT-4o-mini to extract structured fields from OCR text with a confidence score (0-100) per field
3. IF confidence < 85% for any field, THE Document_Agent SHALL flag that field for manual review
4. THE Document_Agent SHALL return structured JSON within 30 seconds of document submission
5. THE Document_Agent SHALL support: JPEG, PNG, PDF, TIFF formats up to 25 MB

### Requirement 2: Automated Document Verification

**User Story:** As a credit assessment officer, I want extracted fields validated automatically, so that fraudulent or invalid documents are detected before review.

#### Acceptance Criteria

1. THE Validator_Agent SHALL validate: PESEL checksum (PL), CNP format (RO), rodne_cislo mod-11 (CZ), document expiry (from extracted date string), age 18+, name fuzzy match (85% threshold), income variance >10%
2. WHEN validation fails, THE Validator_Agent SHALL set validation_status=FAIL with reason text
3. Documents with any FAIL SHALL have status PENDING_REVIEW

### Requirement 3: Human-Verified Loan Approval

**User Story:** As a credit assessor, I want AI to prepare a recommendation, while I make the final decision.

#### Acceptance Criteria

1. THE IPA_Platform SHALL never auto-approve any loan without explicit Credit_Assessor confirmation
2. THE Assessor_Portal SHALL display AI recommendation (APPROVE/DECLINE/REFER) as advisory only
3. WHEN an assessor records a decision, THE IPA_Platform SHALL POST to /api/decision/{application_id} with decision, assessor_id, reason_codes
4. ALL decisions SHALL be logged in audit_log with assessor identity and timestamp

### Requirement 4: 5-Stage NBFI Decisioning Engine

**User Story:** As a credit assessor, I want a decisioning engine calibrated to Polish NBFI regulatory requirements, so that decisions are explainable and auditable.

#### Acceptance Criteria

1. THE CreditScore_Agent SHALL implement 5 sequential stages:
   - Stage 0: Regulatory Gateway (age, PESEL, ID expiry direct from string, AML/PEP)
   - Stage 1: Fraud & Identity (name consistency, Open Banking simulation)
   - Stage 2: Bureau Routing (mock BIK 1-100, mock BIG debt registry)
   - Stage 3: Legal Caps & DTI (MPKK formula, 40%/50% DTI by income)
   - Stage 4: Decision Matrix (product route)
2. Stage 0 SHALL short-circuit on hard rejection — no bureau API cost incurred
3. THE engine SHALL return stage_results with per-stage checks for UI display
4. Expiry_date SHALL be validated from extracted string directly, not from validation record

### Requirement 5: React/Next.js UI with IPF Branding

**User Story:** As a product owner, I want the PoC to look customer-ready with IPF branding.

#### Acceptance Criteria

1. THE UI SHALL use Next.js 14 with Tailwind CSS at port 3000
2. ALL portals SHALL use IPF colours: #00544E (dark teal), #7DC242 (green)
3. THE landing page SHALL show portal hub with 3 cards
4. ALL login screens SHALL have IPF badge and dark teal gradient

### Requirement 6: Admin Portal — Two-Step Document Upload

**User Story:** As a back-office administrator, I want to upload the loan application form and supporting documents separately.

#### Acceptance Criteria

1. THE Admin_Portal SHALL present Step 1 for loan_application document upload
2. THE Admin_Portal SHALL present Step 2 for multiple supporting documents with per-file type selector
3. WHEN submitted, THE Admin_Portal SHALL POST to /api/upload with all files
4. THE Admin_Portal SHALL provide Upload History and Processing Status pages

### Requirement 7: Reviewer Portal — Application Review

**User Story:** As a reviewer, I want to see loan application, supporting documents, and discrepancies in one view.

#### Acceptance Criteria

1. THE Reviewer_Portal Application Review tab SHALL display 3 panels:
   - Panel A: Document Preview (LEFT) + Declared Fields (RIGHT)
   - Panel B: Supporting documents with expandable OCR extractions
   - Panel C: Cross-reference discrepancy report
2. EACH document SHALL have a Review Document button navigating to document review with correct document_id
3. THE Review Document page SHALL show: Confidence Summary (3 tiles), document preview, extracted fields, Approve/Reject buttons

### Requirement 8: VERIFIED Status Persistence

**User Story:** As a reviewer, I want documents I approve to remain verified after AI re-runs.

#### Acceptance Criteria

1. THE Orchestrator validate_extractions step SHALL check document status before updating
2. IF status == VERIFIED, THE Orchestrator SHALL skip that document (continue)
3. Only reviewer Approve/Reject SHALL set or change VERIFIED status

### Requirement 9: Cross-Reference Discrepancy Detection

**User Story:** As a compliance officer, I want automatic comparison of loan application declarations against supporting documents.

#### Acceptance Criteria

1. THE CrossReference_Agent SHALL compare: name, DOB, address, income, bank_account
2. EACH comparison SHALL produce: status (MATCH/MISMATCH/WARNING/UNVERIFIABLE), severity (HIGH/MEDIUM/LOW)
3. Discrepancies SHALL be accessible via GET /api/discrepancies/{application_id}
4. Reviewers SHALL be able to override discrepancies with explanation text

### Requirement 10: Consolidated Application Review

**User Story:** As a credit assessor, I want a single view showing all relevant information.

#### Acceptance Criteria

1. THE Reviewer_Portal Application Review tab SHALL show summary metrics (doc count, verified, mismatches, high risk)
2. Panel A SHALL show loan application with document preview on left and declared fields on right
3. Panel C SHALL show discrepancy report with severity indicators and override capability

### Requirement 11: Document Upload Portal (Admin)

**User Story:** As a back-office administrator, I want a web interface for document upload.

#### Acceptance Criteria

1. THE Admin_Portal SHALL require password authentication (ADMIN_PASSWORD env var)
2. THE Admin_Portal SHALL support batch upload up to 20 files, 25 MB each
3. Document types SHALL be market-specific dropdowns (PL: identity_card, proof_of_address, income_proof, bank_statement; RO/HU/CZ variants)
4. THE Admin_Portal SHALL show Upload History via GET /api/upload/history

### Requirement 12: Event-Driven Processing Trigger

**User Story:** As a platform engineer, I want uploads to trigger processing automatically.

#### Acceptance Criteria

1. WHEN upload succeeds, THE IPA_Platform SHALL launch LangGraph workflow in daemon thread within 5 seconds
2. THE upload HTTP response SHALL return immediately (not blocked by processing)
3. IF workflow fails, THE IPA_Platform SHALL set status FAILED and log traceback to audit_log

### Requirement 13: Data Persistence (SQLite)

**User Story:** As a developer, I want all data in SQLite with clean factory abstraction.

#### Acceptance Criteria

1. THE db_factory.py SHALL return SQLiteDatabase when USE_SQLITE=true
2. ALL data SHALL persist in: documents, extractions, workflow_state, loan_applications, discrepancies, decisions, audit_log, file_storage
3. File BLOBs SHALL be stored in file_storage table
4. THE config.py SHALL load .env via load_dotenv() at import time to ensure OPENAI_API_KEY availability

### Requirement 14: Mock Credit Scoring

**User Story:** As a credit assessor, I want a bureau-style credit score from extracted data.

#### Acceptance Criteria

1. THE CreditScore_Agent SHALL return: score (0-1000), risk_band, recommendation, breakdown per factor, flags, bureau_name, product_route
2. Risk bands: EXCELLENT (800-1000), GOOD (650-799), FAIR (500-649), POOR (350-499), HIGH RISK (0-349) — superseded by NBFI engine 5-stage route
3. Bureau names: BIK (Mock) for PL, Biroul de Credit (Mock) for RO, BISZ/KHR (Mock) for HU, CBCB (Mock) for CZ
4. ALL outputs SHALL include mock disclaimer

### Requirement 15: PDF Document Preview

**User Story:** As a document reviewer, I want to see rendered PDF previews inline.

#### Acceptance Criteria

1. GET /api/document/{document_id}/preview SHALL return PNG of PDF first page
2. Primary method: pdf2image at 150 DPI
3. Fallback: pypdf text + Pillow canvas render
4. Non-PDF images SHALL be returned directly

### Requirement 16: Audit Trail

**User Story:** As a compliance officer, I want every action logged immutably.

#### Acceptance Criteria

1. THE audit_log SHALL capture all events: UPLOAD, EXTRACT_LOAN_APP, EXTRACT, CROSS_REFERENCE, PAUSE_FOR_REVIEW, CORRECT, CONFIRM, RECOMMEND, APPROVE, DECLINE, WORKFLOW_FAILED, DISCREPANCY_OVERRIDE
2. EACH event SHALL include: action, actor, application_id, document_id, timestamp, details JSON
3. THE Reviewer_Portal SHALL display audit events with processing flow diagram

### Requirement 17: Loan Application Form Upload

**User Story:** As an administrator, I want the loan application form extracted as the reference document.

#### Acceptance Criteria

1. THE Admin_Portal SHALL provide Step 1 dedicated to loan_application document
2. THE LoanApplication_Agent SHALL extract 11 declared fields
3. Extracted fields SHALL be stored and accessible via GET /api/loan-application/{application_id}

### Requirement 18: Cross-Reference Agent

**User Story:** As a compliance officer, I want automated detection of inconsistencies.

#### Acceptance Criteria

1. THE CrossReference_Agent SHALL run after all documents are extracted
2. Results SHALL include: field_pair, declared_value, extracted_value, status, severity, detail
3. Reviewers SHALL be able to override with explanation text logged to audit

### Requirement 19: Mock Credit Scoring (NBFI v2)

**User Story:** As a credit assessor, I want a bureau-style score with NBFI decisioning.

#### Acceptance Criteria

1. THE CreditScore_Agent SHALL use 5-stage NBFI pipeline (replaces simple scoring model)
2. Stage results SHALL be returned in stage_results array for UI accordion display
3. Product routes SHALL map to BIK bands: Prime, Mid-Market, Subprime, Thin File
4. Expiry date validation SHALL use extracted string directly

### Requirement 20: Observability

**User Story:** As a platform engineer, I want agent tracing via LangSmith.

#### Acceptance Criteria

1. THE IPA_Platform SHALL enable LangSmith tracing when LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, LANGCHAIN_PROJECT are set
2. THE IPA_Platform SHALL operate normally without LangSmith credentials

### Requirement 21: Loan Application as Reference Document

**User Story:** As a reviewer, I want the loan application to be the authoritative reference.

#### Acceptance Criteria

1. THE LoanApplication_Agent SHALL extract: applicant_full_name, date_of_birth, residential_address, declared_net_monthly_income, declared_income_currency, requested_loan_amount, loan_term_weeks, employment_status, employer_name, bank_account_number, purpose_of_loan
2. Fields SHALL be stored via save_loan_application() and accessible via GET /api/loan-application/{id}

### Requirement 22: Discrepancy Detection

**User Story:** As a compliance officer, I want automatic cross-reference checking.

#### Acceptance Criteria

1. Discrepancy statuses: MATCH, MISMATCH (RED), WARNING (AMBER), UNVERIFIABLE (GREY)
2. Severity: HIGH for name/identity, MEDIUM for address, LOW for financial variance
3. HIGH severity triggers prominent display in Reviewer Portal Panel C

### Requirement 23: Consolidated Review Interface

**User Story:** As a reviewer, I want one screen with loan app, supporting docs, and discrepancies.

#### Acceptance Criteria

1. Panel A: Document Preview (left) + Declared Fields (right) — swapped from original implementation
2. Panel B: Supporting docs with Review Document button per doc
3. Panel C: Discrepancy report with override form

### Requirement 24: Credit Assessor Portal (React)

**User Story:** As an assessor, I want a dedicated portal for credit decisions.

#### Acceptance Criteria

1. THE Assessor_Portal SHALL provide: Decision Queue, Application Summary, Loan Decision, Decision History tabs
2. THE Application Summary SHALL show 5-stage NBFI engine as expandable accordion
3. THE Loan Decision tab SHALL provide APPROVE/DECLINE buttons with reason codes

### Requirement 25: IPF Branding

**User Story:** As a product owner, I want IPF brand identity across all portals.

#### Acceptance Criteria

1. Primary: #00544E (dark teal), Accent: #7DC242 (green)
2. IPF logo badge on all login screens
3. Dark teal gradient headers on all portals
4. Green approve states, teal primary buttons

### Requirement 26: NBFI 5-Stage Engine (React UI Display)

**User Story:** As an assessor, I want the 5-stage engine results visible in the UI.

#### Acceptance Criteria

1. THE Assessor_Portal Application Summary SHALL show DecisioningStagesDisplay component
2. EACH stage SHALL be expandable showing: stage name, description, pass/fail, rejection reason, per-rule checks
3. Stage 0 blocking SHALL show which rule caused rejection
4. All 5 stages passing SHALL show PASS badges with product route

### Requirement 27: Document Review Buttons

**User Story:** As a reviewer, I want direct access to document review from application review.

#### Acceptance Criteria

1. THE Reviewer_Portal Panel A SHALL have Review This Document button under loan app preview
2. THE Reviewer_Portal Panel B SHALL have Review Document button on each supporting doc row
3. CLICKING Review Document SHALL navigate to Review Document tab with correct document_id pre-loaded
4. THE Review Document tab SHALL show Approve Document (teal) and Reject Document (red) buttons

### Requirement 28: Confidence Summary

**User Story:** As a reviewer, I want a confidence overview before reviewing fields.

#### Acceptance Criteria

1. THE Review Document page SHALL show 3 tiles: High (85%+), Medium (70-84%), Low (<70%)
2. EACH tile SHALL show count of fields in that band
3. Low-confidence fields SHALL be highlighted in the field list

### Requirement 29: Deployment Readiness

**User Story:** As an IT engineer, I want the PoC to be deployable to a shared environment.

#### Acceptance Criteria

1. THE backend SHALL be startable via: uvicorn src.backend.api.main:app --port 8000
2. THE React UI SHALL be buildable via: npm run build (no TypeScript errors)
3. THE .env SHALL be excluded from git via .gitignore
4. THE .env.example SHALL document all required variables
5. Deployment options: Railway (backend) + Vercel (UI)

### Requirement 30: Test Data Library

**User Story:** As a demo presenter, I want pre-built test cases to demonstrate different outcomes.

#### Acceptance Criteria

1. THE test-data/demo-cases/generated/ folder SHALL contain 4 complete test cases
2. DEMO-PL-BAD-001: Karolina Mazurek — expired ID, expect DECLINE at Stage 0
3. DEMO-PL-GOOD-001: Tomasz Wisnewski — all clean, expect APPROVE
4. DEMO-PL-PRIME-001: Piotr Nowak — Prime BIK, 5500 PLN income, expect APPROVE & UPSELL with all 5 stages visible
5. DEMO-PL-PRIME-002: Anna Wojcik — Mid-market BIK, 4200 PLN income, expect APPROVE STANDARD with all 5 stages visible
6. EACH test case SHALL have 5 PDFs: loan_application, dowod_osobisty, pasek_wynagrodzen, faktura_adresowa, wyciag_bankowy
