# PoC Requirements: Agent Orchestrator + Document Extraction

## Document Control

| Item | Detail |
|------|--------|
| Version | 1.1 |
| Date | July 2026 |
| Classification | CONFIDENTIAL - Internal Working Draft |
| Scope | Proof of Concept - Orchestrator + Document Processing Agent + Credit Scoring + Observability |
| Prepared by | Mastek AI CoE |
| Change summary | v1.1: Updated Requirements 11-13 to reflect Streamlit UI and SQLite/threading implementation; added Requirements 14-16 for credit scoring, document preview, and LangSmith observability; expanded market scope to PL/RO/HU/CZ |

---

## Introduction

This document defines the requirements for the IPF Intelligent Process Automation Proof of Concept (PoC), scoped to two components: (1) the Agent Orchestrator that coordinates AI agent workflows, and (2) the Document Extraction Agent that processes loan application documents using OCR and NLP. This PoC validates the multi-agent architecture pattern and demonstrates document processing automation across four European home credit markets (Poland, Romania, Hungary, Czech Republic). Success here justifies Wave 1 full build.

## Glossary

- **Orchestrator**: The central coordination service that manages workflow state, routes tasks between agents, enforces policy gates, and provides human-in-the-loop checkpoints
- **Document_Agent**: The AI agent responsible for extracting structured data from customer documents (identity cards, proof of address, income statements) using OCR and NLP
- **Credit_Score_Agent**: The mock agent that computes a bureau-style credit score from extracted document data across all four PoC markets
- **Policy_Gate**: Middleware that validates every agent action against market-specific rules before permitting execution
- **Confidence_Score**: A numerical value (0-100) indicating the OCR/NLP extraction reliability for a given field
- **Market**: A country in which IPF operates; PoC targets four EU markets: Poland (PL), Romania (RO), Hungary (HU), and Czech Republic (CZ)
- **FOCUS_System**: IPF legacy core banking system; PoC uses mock API for integration testing
- **Credit_Assessor**: Human decision-maker who reviews AI-prepared loan recommendations
- **Admin_Portal**: Streamlit web application (port 8501) used by back-office administrators to upload documents
- **Reviewer_Portal**: Streamlit web application (port 8502) used by document reviewers and credit assessors
- **SQLite_DB**: Local SQLite database used as primary storage when Supabase is unavailable or not configured
- **SDS**: Strategic Data Store - IPF analytics and data platform

---

## Requirements

### Requirement 1: Orchestrator Core Workflow Engine

**User Story:** As a platform engineer, I want a central orchestrator that manages the execution flow of AI agents through defined workflow graphs, so that agent coordination is predictable, auditable, and supports both automated and human-in-the-loop steps.

#### Acceptance Criteria

1. THE Orchestrator SHALL execute workflow graphs defined as directed acyclic graphs (DAGs) with sequential, parallel, and conditional branching patterns
2. THE Orchestrator SHALL maintain persistent workflow state across all execution steps, enabling recovery from failures without data loss or duplicate processing
3. WHEN a workflow step fails, THE Orchestrator SHALL retry the step up to 3 times with exponential backoff before marking the workflow as failed and alerting operations
4. THE Orchestrator SHALL support human-in-the-loop checkpoints that pause workflow execution until a designated human actor provides input or approval
5. WHEN a workflow completes or fails, THE Orchestrator SHALL emit an event containing the workflow ID, final state, execution duration, and outcome summary
6. THE Orchestrator SHALL process at least 100 concurrent workflows with a median state-transition latency of under 500 milliseconds

### Requirement 2: Agent Registration and Discovery

**User Story:** As a solutions architect, I want AI agents to register their capabilities with the orchestrator dynamically, so that new agents can be added to the platform without modifying the orchestrator core code.

#### Acceptance Criteria

1. THE Orchestrator SHALL maintain an agent registry containing each agent's identifier, supported input/output schemas, health status, and version
2. WHEN a new agent is registered, THE Orchestrator SHALL validate the agent's interface contract (input schema, output schema, health endpoint) before accepting the registration
3. THE Orchestrator SHALL perform health checks on registered agents at intervals of no more than 30 seconds and mark unhealthy agents as unavailable for new task assignments
4. WHEN the Orchestrator routes a task to an agent, THE Orchestrator SHALL select the agent based on capability match and current health status
5. THE Orchestrator SHALL support versioned agent deployments, allowing a new version to be registered alongside an existing version for canary testing

### Requirement 3: Policy Gate Enforcement

**User Story:** As a compliance officer, I want every AI agent action to be validated against configurable policy rules before execution, so that no agent can operate outside its defined authority boundary.

#### Acceptance Criteria

1. THE Policy_Gate SHALL intercept every agent output before it is acted upon and validate it against the applicable market-specific policy rules
2. WHEN a policy rule is violated, THE Policy_Gate SHALL block the action and return a structured rejection containing the rule ID, violation reason, and suggested escalation path
3. THE Policy_Gate SHALL evaluate rules within 50 milliseconds to avoid impacting end-to-end workflow latency
4. THE Policy_Gate SHALL load rules from a versioned configuration store and apply the active version for the target market without requiring service restart
5. WHEN a policy decision is made (permit, block, or escalate), THE Policy_Gate SHALL log the decision with the rule version, agent ID, action details, and timestamp to an immutable audit store
6. THE Policy_Gate SHALL support at minimum these rule types for the PoC: confidence-threshold gates, mandatory-human-review gates, and field-validation gates

### Requirement 4: Multi-Language Document Extraction

**User Story:** As a loan processing team member, I want customer documents to be automatically extracted and structured regardless of the document language, so that manual data entry is eliminated and processing time is reduced.

#### Acceptance Criteria

1. WHEN a customer document image is submitted to the Document_Agent, THE Document_Agent SHALL extract text content using OCR with a minimum accuracy of 95 percent for printed text on standard-quality scans (300 DPI or higher)
2. WHEN extracted text is in a supported market language (Polish, Romanian, Hungarian, or Czech), THE Document_Agent SHALL identify the document language and apply language-specific extraction rules for field parsing
3. WHEN a document of type national identity card, proof of address (utility bill, bank statement), or income statement (payslip, employment contract) is submitted, THE Document_Agent SHALL extract all required fields defined in the market-specific document schema
4. THE Document_Agent SHALL return a confidence score (0-100) for each extracted field, calculated from OCR engine confidence and NLP parsing confidence
5. WHEN document extraction is complete, THE Document_Agent SHALL return structured data as a validated JSON payload conforming to the defined output schema within 30 seconds of submission
6. THE Document_Agent SHALL support processing of JPEG, PNG, PDF (single and multi-page), and TIFF document formats

### Requirement 5: Document Field Validation and Confidence Scoring

**User Story:** As a credit assessment officer, I want extracted document fields to be validated against known formats and cross-referenced against the loan application, so that data quality issues are caught before human review.

#### Acceptance Criteria

1. WHEN an identity document is extracted, THE Document_Agent SHALL validate the document number format against the market-specific pattern (e.g., Polish PESEL format, Romanian CNP format, Czech rodne cislo format)
2. WHEN a name is extracted from a document, THE Document_Agent SHALL fuzzy-match the name against the loan application name and flag discrepancies exceeding a configurable similarity threshold (default 85 percent match)
3. WHEN a date field is extracted (document expiry, issue date, birth date), THE Document_Agent SHALL validate the date is logically consistent (not expired, birth date results in age 18 or above)
4. IF any extracted field has a confidence score below 85 percent, THEN THE Document_Agent SHALL flag that field for manual review in the output payload
5. WHEN all fields pass validation and confidence thresholds, THE Document_Agent SHALL set the document status to verified in the output payload
6. THE Document_Agent SHALL produce a validation summary listing each field, its extracted value, confidence score, and pass/fail status

### Requirement 6: Human-in-the-Loop Document Review

**User Story:** As a document verification operator, I want to review and correct fields that the AI could not extract with sufficient confidence, so that no document proceeds with inaccurate data.

#### Acceptance Criteria

1. WHEN the Document_Agent flags one or more fields for manual review, THE Orchestrator SHALL route the document to a human review queue with the extraction results, confidence scores, and original document image
2. THE human review interface SHALL display the original document alongside extracted fields, highlighting low-confidence fields for attention
3. WHEN a human operator corrects or confirms a field value, THE Orchestrator SHALL update the extraction result and resume the workflow with the corrected data
4. IF a human operator has not acted on a queued document within 15 minutes, THE Orchestrator SHALL send a reminder notification and escalate to a team lead after 30 minutes
5. THE Orchestrator SHALL record all human corrections as training data for future model improvement, storing the original extraction, correction, and operator identity

### Requirement 7: Loan Recommendation Generation (AI-Assisted, Human-Decided)

**User Story:** As a credit assessor, I want the system to generate a recommendation with supporting data after documents are verified, so that I can make an informed approval decision efficiently while retaining full authority over every loan.

#### Acceptance Criteria

1. WHEN all documents for a loan application pass verification (automated or human-corrected), THE Orchestrator SHALL trigger the recommendation generation step
2. THE Document_Agent SHALL compile a recommendation package containing: extracted and verified data from all documents, validation results, confidence scores, and any anomalies detected
3. THE Orchestrator SHALL route the recommendation package to a human Credit_Assessor via the human-in-the-loop checkpoint; no loan SHALL be approved without explicit human confirmation
4. THE Orchestrator SHALL present the recommendation to the Credit_Assessor within 3 minutes of document verification completion
5. WHEN the Credit_Assessor records a decision (approve, decline, or refer), THE Orchestrator SHALL log the decision with assessor identity, timestamp, AI recommendation, and reason codes to the audit store
6. IF a Credit_Assessor has not acted within 30 minutes, THE Orchestrator SHALL send a reminder; after 60 minutes THE Orchestrator SHALL escalate to the team lead

### Requirement 8: Audit Trail and Observability

**User Story:** As an operations manager, I want complete visibility into every workflow execution, agent decision, and policy evaluation, so that I can monitor system health, debug issues, and produce compliance evidence.

#### Acceptance Criteria

1. THE Orchestrator SHALL record an immutable audit event for every workflow state transition containing: workflow ID, step name, agent ID, timestamp, input hash, output hash, and duration
2. THE Orchestrator SHALL provide end-to-end tracing across all agent invocations within a single workflow, enabling reconstruction of the complete decision path
3. THE IPA_Platform SHALL provide a dashboard showing: active workflows, completion rates, average processing times, agent error rates, and policy-gate rejection rates
4. WHEN any agent error rate exceeds 5 percent over a 10-minute window, THE Orchestrator SHALL raise an alert to the operations team
5. THE audit store SHALL retain all records for a minimum of 7 years to satisfy regulatory audit requirements
6. THE Orchestrator SHALL support export of audit records in a structured format (JSON or Parquet) for compliance reporting and model improvement analysis

### Requirement 9: FOCUS System Integration (Mock for PoC)

**User Story:** As a systems integrator, I want the PoC to demonstrate the FOCUS system integration pattern using a mock API, so that the integration approach is validated before connecting to the production system.

#### Acceptance Criteria

1. THE IPA_Platform SHALL communicate with a FOCUS mock API that replicates the expected FOCUS system interface for loan application data retrieval and status updates
2. WHEN the Document_Agent requires loan application reference data for cross-validation, THE Orchestrator SHALL retrieve the data from the FOCUS mock API
3. WHEN a Credit_Assessor records a loan decision, THE Orchestrator SHALL write the decision record to the FOCUS mock API including decision, assessor ID, timestamp, and audit trail reference
4. IF the FOCUS mock API is unavailable, THE Orchestrator SHALL queue the transaction and retry with exponential backoff, notifying operations after 5 failed attempts
5. THE FOCUS mock API SHALL be replaceable with the real FOCUS integration layer without changes to agent or orchestrator code

### Requirement 10: PoC Success Metrics and Exit Criteria

**User Story:** As a programme sponsor, I want clearly defined success metrics for the PoC, so that we can make an evidence-based decision on whether to proceed to full Wave 1 build.

#### Acceptance Criteria

1. THE PoC SHALL demonstrate end-to-end processing of at least 200 sample documents across identity, address, and income document types across all four supported market languages (PL, RO, HU, CZ)
2. THE Document_Agent SHALL achieve a field-level extraction accuracy of 90 percent or higher on the PoC test dataset
3. THE Orchestrator SHALL demonstrate less than 1 percent workflow failure rate (excluding intentional policy-gate blocks) across the test dataset
4. THE end-to-end processing time from document submission to recommendation presentation SHALL be under 3 minutes for 95 percent of submissions
5. THE PoC SHALL demonstrate successful human-in-the-loop interaction for both low-confidence review and loan decision approval workflows
6. THE PoC SHALL produce a documented cost-per-document estimate based on actual infrastructure usage during the test period

### Requirement 11: Document Upload Portal (Admin UI)

**User Story:** As a back-office administrator, I want to upload customer identity, address, and income documents through a web interface, so that documents are securely stored and automatically queued for AI processing without manual handoff.

#### Acceptance Criteria

1. THE Admin_Portal SHALL be implemented as a Streamlit application served on port 8501, accessible only after successful password authentication using the ADMIN_PASSWORD environment variable
2. THE Admin_Portal SHALL support batch upload of multiple documents (up to 20 files) in a single submission, accepting JPEG, PNG, PDF (single and multi-page), and TIFF formats with a maximum file size of 25 MB per file
3. WHEN uploading documents, THE Admin_Portal SHALL require the operator to specify a loan application ID, select the target market (PL, RO, HU, or CZ), and assign a document type to each file from a market-specific dropdown reflecting the full document taxonomy for the selected market
4. WHEN a batch upload is submitted, THE Admin_Portal SHALL POST all files and metadata to the backend REST API (POST /api/upload), which stores documents to the configured storage backend (local filesystem under data/documents/ in SQLite mode) with metadata including upload timestamp, operator ID, application ID, document type, market, and original filename, and returns a batch ID confirmation
5. THE Admin_Portal SHALL display upload progress and clearly indicate success or failure per file, allowing retry of failed uploads without re-uploading successful ones
6. THE Admin_Portal SHALL validate file format and size before submission and reject unsupported formats with a clear error message
7. THE Admin_Portal SHALL provide an Upload History page showing recent workflow submissions retrieved via GET /api/upload/history, and a Processing Status page allowing the operator to check the current status of any application by ID via GET /api/status/{application_id}

### Requirement 12: Event-Driven Document Processing Trigger

**User Story:** As a platform engineer, I want document uploads to automatically trigger the document processing workflow without manual intervention, so that processing begins immediately upon submission and no documents are left unprocessed.

#### Acceptance Criteria

1. WHEN documents are successfully stored by the upload handler, THE IPA_Platform SHALL initiate the document processing workflow within 5 seconds, passing the document IDs, application ID, document types, and market context
2. THE IPA_Platform SHALL launch the LangGraph orchestrator workflow in a background daemon thread immediately after the upload API response is returned, so that the upload HTTP request is not blocked by processing
3. WHEN a batch contains multiple documents for the same application, THE Orchestrator SHALL process all documents within a single workflow instance, extracting and validating each document before generating a combined recommendation
4. IF the document processing workflow raises an unhandled exception, THE IPA_Platform SHALL catch the error, set the workflow status to FAILED, and log a full traceback to the audit store so that the failure is visible in the Reviewer_Portal
5. THE IPA_Platform SHALL use SQLite_DB as the primary local database when Supabase is not configured or unavailable; THE IPA_Platform SHALL auto-detect Supabase availability at startup by testing connectivity and fall back to SQLite_DB without requiring a service restart; the active database mode SHALL be reported by the GET /api/health endpoint
6. THE IPA_Platform SHALL prevent duplicate processing of the same document if the upload event is delivered more than once (idempotent workflow initiation)

### Requirement 13: Document Review and Verification Portal (Reviewer UI)

**User Story:** As a document verification officer or credit assessor, I want to view the AI processing results for submitted documents including extraction outputs, confidence scores, validation flags, and overall status, so that I can review, correct, and approve documents efficiently from a single interface.

#### Acceptance Criteria

1. THE Reviewer_Portal SHALL be implemented as a Streamlit application served on port 8502 with separate password-protected login for the Document Reviewer role and the Credit Assessor role; the two roles SHALL have access to different portal pages appropriate to their responsibilities
2. THE Reviewer_Portal SHALL display a Work Queue page showing all documents retrieved via GET /api/queue, presented in a table layout with status-based filtering (All / PENDING_REVIEW / EXTRACTED / VERIFIED); each item SHALL provide an "Open for Review" button that navigates directly to the Review Document page pre-loaded with the selected document
3. FOR each processed document, THE Reviewer_Portal SHALL display: the original document image or PDF preview alongside all extracted fields with their values, a per-field confidence score colour-coded by icon (green circle for 85%+, yellow circle for 70-84%, red circle for below 70%), and the validation result (pass/fail icon with reason text)
4. THE Reviewer_Portal SHALL allow the reviewer to edit any extracted field value inline; WHEN corrections are submitted, THE Reviewer_Portal SHALL call POST /api/review/{document_id}/correct to persist the corrected values and update the document status to VERIFIED
5. WHEN the reviewer clicks "Confirm All Correct" without edits, THE Reviewer_Portal SHALL call POST /api/review/{document_id}/confirm to mark the document as VERIFIED and advance the workflow
6. THE Reviewer_Portal SHALL display the overall application status across all submitted documents (document count, verified count, workflow status) on the Loan Decision page, retrieved via GET /api/status/{application_id}
7. THE Reviewer_Portal SHALL display the AI-generated document recommendation (APPROVE / DECLINE / REFER) alongside the mock credit score on the Loan Decision page, and SHALL provide APPROVE and DECLINE buttons for the Credit_Assessor to record the final human decision via POST /api/decision/{application_id}; these decision actions SHALL require the Credit Assessor role
8. THE Reviewer_Portal SHALL provide an Audit Trail page allowing lookup of all audit events for a given application ID via GET /api/audit/{application_id}

---

### Requirement 14: Mock Credit Scoring Agent

**User Story:** As a credit assessor, I want to see a bureau-style credit score derived from the extracted document data, so that I can quickly assess the financial risk profile of a loan applicant across all four PoC markets before making a final decision.

#### Acceptance Criteria

1. THE Credit_Score_Agent SHALL compute a total credit score on a 0-1000 point scale using five weighted factor categories: Income Adequacy (max 300 pts), Employment Stability (max 200 pts), Identity Validity (max 200 pts), Document Consistency (max 200 pts), and Age & Eligibility (max 100 pts)
2. THE Credit_Score_Agent SHALL classify the total score into one of five risk bands: EXCELLENT (800-1000), GOOD (650-799), FAIR (500-649), POOR (350-499), or HIGH RISK (0-349)
3. THE Credit_Score_Agent SHALL apply market-specific income thresholds and currency units when scoring the Income Adequacy factor: PLN with minimum 2,500 for PL, RON with minimum 1,500 for RO, HUF with minimum 150,000 for HU, and CZK with minimum 20,000 for CZ
4. THE Credit_Score_Agent SHALL reference the appropriate mock bureau name for each market in the score output: BIK (Mock) for PL, Biroul de Credit (Mock) for RO, BISZ/KHR (Mock) for HU, and CBCB (Mock) for CZ
5. WHEN the GET /api/credit-score/{application_id} endpoint is called, THE IPA_Platform SHALL aggregate all extracted fields and validation results for the application's documents and invoke the Credit_Score_Agent, returning a response containing: total score, score percentage, risk band, risk icon, colour code, per-factor breakdown with score and maximum for each category, risk flags list, scoring recommendation (APPROVE / REFER / DECLINE), bureau name, and mock disclaimer
6. THE Credit_Score_Agent SHALL derive a scoring recommendation from the total score and flag count: APPROVE for scores of 650 or above with no risk flags, REFER for scores between 400 and 649 or for any score with one or fewer flags, and DECLINE for scores below 400 with two or more risk flags
7. THE Credit_Score_Agent SHALL append a risk flag for each detected data quality issue including: income below market minimum threshold, income data unavailable, employment details not found in documents, expired identity document, national ID checksum validation failure, applicant age outside eligible range (18-70), address mismatch across documents, income discrepancy exceeding 10 percent variance, and name inconsistency across documents
8. THE Credit_Score_Agent output SHALL include the disclaimer "MOCK SCORE - for demonstration only. Replace with live bureau API in production." in all responses

### Requirement 15: PDF Document Preview

**User Story:** As a document reviewer, I want to see a rendered image preview of uploaded PDF documents directly in the browser, so that I can visually inspect the source document without downloading it separately.

#### Acceptance Criteria

1. WHEN a GET /api/document/{document_id}/preview request is received for a PDF document, THE IPA_Platform SHALL return a PNG image of the first page of the PDF with HTTP content-type image/png
2. THE IPA_Platform SHALL attempt PDF-to-image conversion using pdf2image at 150 DPI as the primary rendering method; IF pdf2image is unavailable, THE IPA_Platform SHALL fall back to extracting text from the PDF via pypdf and rendering that text onto a generated white canvas image using Pillow, with a styled blue header bar and key:value field formatting
3. WHEN a GET /api/document/{document_id}/preview request is received for a non-PDF image document (JPEG, PNG), THE IPA_Platform SHALL return the original image bytes directly with the appropriate image content-type
4. THE Reviewer_Portal SHALL call GET /api/document/{document_id}/preview to render PDF documents inline within the Review Document page; a Download PDF button SHALL also be presented alongside the preview for direct file download
5. IF the document file cannot be located in storage or the preview cannot be rendered, THE IPA_Platform SHALL return HTTP 404 or HTTP 500 respectively with a descriptive error message

### Requirement 16: LangSmith Observability Integration

**User Story:** As a platform engineer, I want all LangChain and LangGraph agent invocations to be traced in LangSmith, so that I can inspect agent reasoning, debug extraction failures, and monitor latency across the full processing pipeline.

#### Acceptance Criteria

1. THE IPA_Platform SHALL enable LangSmith tracing for all LangChain and LangGraph operations when the environment variables LANGCHAIN_TRACING_V2=true, LANGCHAIN_API_KEY, and LANGCHAIN_PROJECT are present; WHEN these variables are absent, THE IPA_Platform SHALL operate normally without tracing and SHALL NOT raise an error or fail to start
2. WHEN LangSmith tracing is active, THE IPA_Platform SHALL record a trace for every orchestrator workflow run, capturing each graph node (extract, validate, recommend, pause_review) as a distinct span with its input state and output state
3. WHEN LangSmith tracing is active, THE IPA_Platform SHALL record a trace for every Document_Agent LLM call, including the prompt sent, the raw completion received, the model name, token counts, and latency
4. THE LangSmith project name used for all traces SHALL be configurable via the LANGCHAIN_PROJECT environment variable, allowing separation of PoC traces from other projects in the same LangSmith account
5. THE GET /api/health endpoint SHALL report the active database mode (SQLiteDatabase or Supabase Database) and OCR pipeline availability status (Tesseract available, pdf2image available, supported languages, and operating mode) to support operational monitoring without requiring access to LangSmith
### Requirement 17: Loan Application Form Upload and Extraction

**User Story:** As a back-office administrator, I want to upload the customer's formal loan application form alongside supporting documents, so that the system has the declared customer information to cross-reference against identity and financial evidence.

#### Acceptance Criteria

1. THE Admin_Portal SHALL provide a dedicated Loan Application section in the upload form where the operator uploads a single loan application document tagged with document type loan_application
2. WHEN a loan application document is submitted, THE Document_Agent SHALL extract the following declared fields: applicant full name, date of birth, declared residential address, declared net monthly income, declared currency, requested loan amount, loan term in weeks, employment status, employer name, bank account number, and purpose of loan
3. THE extracted loan application fields SHALL be stored as the reference data set for the application, accessible via GET /api/loan-application/{application_id}
4. THE Admin_Portal SHALL display the loan application upload section before the supporting documents section and clearly label it as the primary reference document
5. IF no loan application document is submitted in a batch, THE IPA_Platform SHALL still process the supporting documents but SHALL flag the application status as LOAN_APPLICATION_MISSING and include this as a discrepancy in the review

### Requirement 18: Cross-Reference Discrepancy Detection

**User Story:** As a document verification officer, I want the system to automatically compare the declared loan application details against all submitted supporting documents and highlight any discrepancies, so that inconsistencies are surfaced before human review rather than discovered manually.

#### Acceptance Criteria

1. WHEN all documents in a batch have been extracted (including at least one supporting document and the loan application), THE Orchestrator SHALL run a cross-reference comparison step before routing to human review
2. THE Cross_Reference_Agent SHALL compare the following field pairs between the loan application and supporting documents:
   a. Applicant name from loan application vs name extracted from identity document
   b. Date of birth from loan application vs date of birth from identity document
   c. Residential address from loan application vs address from proof-of-address document
   d. Declared net income from loan application vs net salary from income document
   e. Bank account number from loan application vs account number from bank statement
3. FOR each field comparison, THE Cross_Reference_Agent SHALL produce a discrepancy record containing: field name, declared value from loan application, extracted value from supporting document, match status (MATCH / MISMATCH / UNVERIFIABLE), and severity (HIGH for name/identity mismatches, MEDIUM for address mismatches, LOW for minor variance)
4. WHEN a name comparison is performed, THE Cross_Reference_Agent SHALL use fuzzy string matching with a threshold of 85 percent similarity; scores above 85 percent SHALL be MATCH, between 70-84 percent SHALL be flagged as WARNING, and below 70 percent SHALL be MISMATCH
5. WHEN an income comparison is performed, THE Cross_Reference_Agent SHALL flag discrepancies exceeding 10 percent variance as MISMATCH and discrepancies between 5-10 percent as WARNING
6. IF any HIGH severity discrepancy is detected, THE Orchestrator SHALL set the application status to DISCREPANCY_FOUND and ensure it appears at the top of the reviewer work queue
7. ALL discrepancy records SHALL be persisted and accessible via GET /api/discrepancies/{application_id}

### Requirement 19: Consolidated Document Review with Cross-Reference Panel

**User Story:** As a document verification officer, I want to see the loan application details, all submitted supporting documents, and the cross-reference discrepancy report on a single review screen, so that I can assess the application holistically without switching between multiple views.

#### Acceptance Criteria

1. THE Reviewer_Portal review page SHALL display three panels: (A) Loan Application Panel showing all declared fields from the loan application form, (B) Supporting Documents Panel listing each submitted document with its type, status, and OCR extraction results, and (C) Discrepancy Report Panel showing the cross-reference results
2. IN the Loan Application Panel, THE Reviewer_Portal SHALL display each declared field with a colour-coded status indicator showing whether the field was VERIFIED by a supporting document (green), has a WARNING (amber), is MISMATCHED (red), or is UNVERIFIABLE due to missing supporting document (grey)
3. IN the Supporting Documents Panel, THE Reviewer_Portal SHALL show each document with its preview image, all extracted fields, per-field confidence scores, and validation results; fields that are involved in a discrepancy SHALL be highlighted with a red border
4. IN the Discrepancy Report Panel, THE Reviewer_Portal SHALL list all detected discrepancies with severity icons (HIGH in red, MEDIUM in amber, LOW in yellow), showing the declared value vs extracted value side by side
5. THE Reviewer_Portal SHALL display a summary banner at the top of the consolidated review showing: total documents submitted, documents verified, discrepancies found (broken down by severity), and overall application risk assessment
6. THE reviewer SHALL be able to override a discrepancy by recording an explanation and marking it as REVIEWED, which updates the discrepancy record and is logged in the audit trail

---

## Change Log

### v1.2 — July 2026 (final PoC state)

**New capabilities added since v1.1:**

- **Three role-based portals**: Admin (8501), Reviewer (8502), Assessor (8503) — fully separated
- **Loan Application as reference document**: Uploaded as first document, extracted by dedicated LoanApplicationAgent
- **Cross-reference engine**: 5 field comparisons (name, DOB, address, income, bank account) with MATCH/WARNING/MISMATCH/UNVERIFIABLE classification
- **Discrepancy override**: Reviewers can mark discrepancies as REVIEWED with justification
- **Credit score in assessor portal**: Risk flags with human-readable explanations for each flag type
- **Audit trail flowchart**: Vertical pipeline flowchart with colour-coded stages (red=not started, amber=processing, green=completed)
- **Mock PDF generation**: 8 complete Polish test case PDFs (good + bad) in test-data/demo-cases/generated/
- **Demo capture script**: Automated browser walkthrough producing PDF deck via Selenium + Chrome
- **LangSmith tracing**: Optional but configured — traces all LangGraph nodes and LLM calls
- **All junk characters removed**: All emoji/non-ASCII characters stripped from Streamlit UI files

**New API endpoints added:**
- GET /api/loan-application/{application_id}
- GET /api/discrepancies/{application_id}
- POST /api/discrepancies/{application_id}/override
- GET /api/document/{document_id}/preview
- GET /api/credit-score/{application_id} (was present, now also shown in assessor portal)

**Orchestrator workflow updated (6 nodes):**
1. extract_loan_app
2. extract (document loop)
3. validate
4. cross_reference
5. pause_review OR recommend
6. END

**Assessor portal (port 8503) pages:**
- Decision Queue
- Application Summary
- Loan Decision
- Decision History
