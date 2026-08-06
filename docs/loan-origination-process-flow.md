# IPF Loan Origination Process Flow

## Document Control

| Item | Detail |
|------|--------|
| Version | 2.0 |
| Date | July 2026 |
| Markets | Poland (PL), Romania (RO), Hungary (HU), Czech Republic (CZ) |

---

## 1. LangGraph Workflow Nodes

| Node | Agent | Action |
|------|-------|--------|
| extract_loan_app | LoanApplicationAgent | Extracts 11 declared fields from loan application form |
| extract (loop) | DocumentAgent | OCR + LLM extraction per supporting document |
| validate | Validator | Market rules: PESEL, CNP, expiry, age, income variance |
| cross_reference | CrossReferenceAgent | Compare 5 field pairs: name, DOB, address, income, account |
| pause_for_review | Orchestrator | Sets status PENDING_REVIEW, ends workflow |
| recommend | DocumentAgent | Generates APPROVE/DECLINE/REFER recommendation |

---

## 2. Document Status Lifecycle

UPLOADED -> PROCESSING -> EXTRACTED -> PENDING_REVIEW -> VERIFIED

VERIFIED protection: The Orchestrator validate_extractions step skips documents already VERIFIED.
Human reviewer decisions are never overwritten by the AI workflow.

---

## 3. Polish Market NBFI Engine

| Stage | Description | Regulatory Reference |
|-------|-------------|---------------------|
| Stage 0 | Age 18-75, PESEL checksum, ID expiry, AML/PEP | Polish civil law, KNF guidelines |
| Stage 1 | Name consistency, Open Banking identity | PSD2, KontoConnect |
| Stage 2 | BIK score + BIG debt registry | BIK API, KRD/ERIF/BIG InfoMonitor |
| Stage 3 | MPKK cost cap + DTI by income band | Ustawa antylichwiarska |
| Stage 4 | Decision matrix -> product route | IPF NBFI credit policy |

### DTI Thresholds (Poland)

| Income | DTI Cap |
|--------|---------|
| < 3,500 PLN/month | 40% |
| >= 3,500 PLN/month | 50% |

### Product Routes

| BIK Score | Route | Max Amount |
|-----------|-------|-----------|
| 0 (thin file) | APPROVE_PROBATIONARY | 1,000 PLN |
| 30-45 | APPROVE_WITH_CAP | 2,000 PLN |
| 46-70 | APPROVE_STANDARD | 5,000 PLN |
| >70 | APPROVE_UPSELL | Full product |
| 1-29 | REJECT | 0 |

---

## 4. Audit Events

| Event | Trigger | Actor |
|-------|---------|-------|
| UPLOAD | POST /api/upload | admin |
| EXTRACT_LOAN_APP | LoanApplicationAgent | loan_application_agent |
| EXTRACT | DocumentAgent | document_agent |
| CROSS_REFERENCE | CrossReferenceAgent | cross_reference_agent |
| PAUSE_FOR_REVIEW | Orchestrator | orchestrator |
| CORRECT | Reviewer submits corrections | reviewer |
| CONFIRM | Reviewer approves document | reviewer |
| RECOMMEND | Recommendation agent | document_agent |
| APPROVE | Assessor records approval | credit_assessor |
| DECLINE | Assessor records decline | credit_assessor |
| WORKFLOW_FAILED | Exception in workflow | orchestrator |
| DISCREPANCY_OVERRIDE | Reviewer overrides mismatch | reviewer |

---

## 5. API Endpoints Reference

| Method | Path | Purpose |
|--------|------|---------|
| POST | /api/upload | Upload documents, trigger workflow |
| GET | /api/status/{id} | Application workflow status |
| GET | /api/upload/history | All workflow history |
| GET | /api/queue | Review queue with status filter |
| GET | /api/review/{doc_id} | Document extractions + image |
| POST | /api/review/{doc_id}/correct | Submit field corrections |
| POST | /api/review/{doc_id}/confirm | Mark document VERIFIED |
| POST | /api/decision/{id} | Record APPROVE/DECLINE |
| GET | /api/audit/{id} | Full audit trail |
| GET | /api/document/{doc_id}/preview | PDF first page as PNG |
| GET | /api/credit-score/{id} | NBFI engine result |
| GET | /api/loan-application/{id} | Declared loan application fields |
| GET | /api/discrepancies/{id} | Cross-reference discrepancy report |
| POST | /api/discrepancies/{id}/override | Reviewer override with explanation |
| GET | /api/health | System health + OCR status |
