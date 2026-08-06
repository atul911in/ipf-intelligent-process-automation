# Technical Specification: IPF IPA PoC v2.0

## Document Control

| Version | 2.0 |
| Date | July 2026 |
| Classification | CONFIDENTIAL |
| Changes | React/Next.js UI, NBFI 5-stage engine, VERIFIED persistence fix, config.py fix, IPF branding |

---

## 1. Component Overview

| Component | Technology | Port |
|-----------|-----------|------|
| React UI | Next.js 14, Tailwind CSS, axios | 3000 |
| FastAPI Backend | FastAPI, uvicorn, python-dotenv | 8000 |
| LangGraph Orchestrator | LangGraph 1.x, daemon thread | - |
| LoanApplication Agent | LangChain, GPT-4o-mini | - |
| Document Agent | pypdf, pytesseract, GPT-4o-mini | - |
| Validator Agent | rules-based, no LLM | - |
| CrossReference Agent | rules-based comparison | - |
| CreditScore Agent | 5-stage NBFI engine | - |
| SQLite Database | SQLite3, db_factory.py | - |

---

## 2. Key Technical Fixes

| Issue | File | Fix |
|-------|------|-----|
| OPENAI_API_KEY not loaded | src/backend/core/config.py | load_dotenv() at import time |
| VERIFIED reset by workflow | src/backend/agents/orchestrator.py | validate_extractions skips VERIFIED |
| Stage 0 REJECT on PENDING | src/backend/agents/credit_score_agent.py | Expiry from extracted string |
| React blank page | ipf-ipa-react-ui/.next | Clean rebuild required |

---

## 3. NBFI Decisioning Engine

File: src/backend/agents/credit_score_agent.py

Stage 0: stage_0_hard_checks - age 18-75, PESEL checksum, ID expiry from string, AML/PEP
Stage 1: stage_1_fraud_checks - name consistency, Open Banking mock
Stage 2: stage_2_bureau_checks - mock BIK score 1-100, mock BIG debt
Stage 3: stage_3_affordability - MPKK formula, DTI 40/50 pct by income
Stage 4: stage_4_decision_matrix - BIK x BIG x DTI -> product route

BIK bands: over70=UPSELL, 46-70=STANDARD, 30-45=WITH_CAP, 1-29=REJECT, 0=PROBATIONARY
DTI cap: under 3500 PLN = 40 pct, 3500+ PLN = 50 pct

---

## 4. React UI

Project: ipf-ipa-react-ui/
IPF Colors: Primary #00544E, Accent #7DC242

Admin /admin: 2-step upload (loan app + supporting docs)
Reviewer /reviewer: Work Queue, Application Review (Panels A/B/C), Review Document, Audit Trail
Assessor /assessor: Decision Queue, Application Summary (5-stage accordion), Loan Decision, History

Passwords: Admin=ipf-admin-2026, Reviewer=ipf-reviewer-2026, Assessor=ipf-assessor-2026

---

## 5. Test Data

Location: test-data/demo-cases/generated/

DEMO-PL-BAD-001   Karolina Mazurek  DECLINE - Stage 0 expired ID
DEMO-PL-GOOD-001  Tomasz Wisnewski  APPROVE
DEMO-PL-PRIME-001 Piotr Nowak       APPROVE and UPSELL - all 5 stages pass
DEMO-PL-PRIME-002 Anna Wojcik       APPROVE STANDARD - all 5 stages pass

Each set has 5 PDFs: loan_application, dowod_osobisty, pasek_wynagrodzen, faktura_adresowa, wyciag_bankowy
