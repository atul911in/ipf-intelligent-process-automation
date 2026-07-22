# Intelligent Loan Origination – Process Flow

## Overview

This diagram shows how Requirements 1, 2, and 3 work together to create an end-to-end loan origination process where AI handles document extraction and verification, but **a human always makes the final approval decision**.

---

## Process Flow Diagram

```mermaid
flowchart TD
    %% Requirement 1: Document Extraction
    A[📄 Customer Submits Documents<br/>ID, Proof of Address, Income] --> B{OCR + NLP Engine<br/>Extracts Text & Data}
    
    B --> C{Language<br/>Detected?}
    C -->|Polish, Romanian,<br/>Hungarian, Spanish, Czech| D[Apply Language-Specific<br/>NLP Extraction Rules]
    
    D --> E{OCR Confidence<br/>≥ 85%?}
    E -->|Yes| F[✅ Structured Data Extracted<br/>Within 30 seconds]
    E -->|No| G[⚠️ Flag for Manual Review<br/>Route to Human Operator]
    
    G --> H[Human Operator<br/>Reviews & Corrects Data]
    H --> F

    %% Requirement 2: Document Verification
    F --> I{Automated<br/>Verification Checks}
    
    I --> J[Check ID:<br/>Expiry, Format, Name Match]
    I --> K[Check Address:<br/>Matches Application]
    I --> L[Check Income:<br/>Within 10% of Declared]
    
    J --> M{All Checks<br/>Pass?}
    K --> M
    L --> M
    
    M -->|No| N[❌ Generate Rejection Code<br/>Notify Agent within 60s]
    N --> O[Agent Reviews with Customer<br/>Request Correct Documents]
    O --> A
    
    M -->|Yes| P[✅ Status Updated to<br/>"Documents Verified" in FOCUS]

    %% Requirement 3: Human-Verified Approval
    P --> Q[🤖 AI Generates Recommendation<br/>Approve / Decline / Refer]
    Q --> R[Prepare Supporting Data:<br/>Credit Score, Risk Indicators,<br/>Verification Results]
    
    R --> S[📋 Route to Human<br/>Credit Assessor<br/>Within 3 minutes]
    
    S --> T{Human Credit Assessor<br/>Reviews Application}
    
    T -->|Approve| U[✅ Loan Approved<br/>Decision + Audit Trail<br/>Written to FOCUS]
    T -->|Decline| V[❌ Loan Declined<br/>Decision + Reason Codes<br/>Written to FOCUS]
    
    S --> W{No Action<br/>Within 30 min?}
    W -->|Yes| X[⏰ Reminder Sent<br/>to Assessor]
    X --> Y{Still No Action<br/>After 60 min?}
    Y -->|Yes| Z[🔔 Escalate to<br/>Team Lead]

    %% Styling
    style A fill:#e3f2fd,stroke:#1565c0
    style G fill:#fff3e0,stroke:#e65100
    style N fill:#ffebee,stroke:#c62828
    style P fill:#e8f5e9,stroke:#2e7d32
    style Q fill:#f3e5f5,stroke:#6a1b9a
    style S fill:#fff9c4,stroke:#f57f17
    style T fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    style U fill:#e8f5e9,stroke:#2e7d32
    style V fill:#ffebee,stroke:#c62828
```

---

## Key Points for Business Users

| Stage | What Happens | Who Does It | Time |
|-------|-------------|-------------|------|
| **1. Document Extraction** | System reads and extracts data from customer documents (ID, address, income) | 🤖 AI (OCR + NLP) | < 30 seconds |
| **2. Document Verification** | System checks documents are valid, not expired, and match the application | 🤖 AI (Automated Rules) | < 60 seconds |
| **3. Loan Decision** | AI prepares a recommendation with all data, then a **human** reviews and decides | 👤 Human Credit Assessor | < 3 min to present |

---

## Critical Safeguard

> **⚠️ No loan is ever automatically approved.**
> 
> The AI assists by extracting documents, verifying them, and preparing a recommendation — but **every single loan application** goes to a qualified human Credit Assessor for the final approve/decline decision.

---

## Exception Handling

| Exception | Action |
|-----------|--------|
| Low OCR confidence (< 85%) | Flagged for human operator review |
| Document verification fails | Agent notified within 60s, customer asked for correct documents |
| Assessor doesn't act in 30 min | Reminder notification sent |
| Assessor doesn't act in 60 min | Escalated to team lead |

