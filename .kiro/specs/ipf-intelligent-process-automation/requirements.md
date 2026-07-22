# Requirements Document

## Introduction

This document defines the requirements for the IPF Intelligent Process Automation programme, covering four solution areas designed to reduce IPF's cost-income ratio from ~61.9% toward the 49-51% target. The programme addresses the inherent labour intensity of the agent-led home credit model (~21,000 colleagues), the tight coupling of the FOCUS core system with branch structures, and the low ITSM maturity (2.9/5). The four solution areas are: Intelligent Loan Origination, Intelligent Agent Operations, AI Service Desk, and Intelligent Collections. All solutions must support multi-market deployment across Poland, Romania, Hungary, Spain, and the Czech Republic with full multilingual capability and GDPR compliance.

## Glossary

- **IPA_Platform**: The overarching Intelligent Process Automation platform that orchestrates the four solution areas and provides shared services (authentication, logging, monitoring, multilingual support)
- **Loan_Origination_Engine**: The automated document verification and loan processing subsystem that uses OCR and NLP to extract and validate customer documents
- **Agent_Operations_Optimizer**: The geospatial AI subsystem that generates optimised route plans and schedules for field agents
- **AI_Service_Desk**: The AI-powered IT service desk subsystem that provides automated ticket triage, auto-resolution, and knowledge management
- **Collections_Engine**: The conversational AI subsystem that automates early-stage collections via voice and SMS bots in local languages
- **FOCUS_System**: IPF's legacy core banking and loan management system, tightly coupled with branch structures and lacking service-oriented architecture
- **Agent**: A field-based IPF colleague who visits customers at home to originate loans and collect payments
- **Market**: A country in which IPF operates (Poland, Romania, Hungary, Spain, Czech Republic)
- **OCR**: Optical Character Recognition — technology to extract text from scanned documents and images
- **NLP**: Natural Language Processing — technology to understand and extract structured information from unstructured text
- **ITSM**: IT Service Management — the set of practices for managing IT services
- **Escalation**: The process of routing a case from automated handling to a human agent when complexity thresholds are exceeded
- **GDPR**: General Data Protection Regulation — EU data privacy legislation applicable across all IPF markets
- **Credit_Assessor**: A qualified human decision-maker responsible for reviewing AI-prepared loan recommendations and making final approval or decline decisions

## Requirements

### Requirement 1: Multi-Language Document Extraction

**User Story:** As a loan processing team member, I want documents submitted by customers to be automatically extracted and structured regardless of language, so that manual data entry is eliminated and processing time is reduced.

#### Acceptance Criteria

1. WHEN a customer document image is submitted, THE Loan_Origination_Engine SHALL extract text content using OCR with a minimum accuracy of 95% for printed text
2. WHEN extracted text is in Polish, Romanian, Hungarian, Spanish, or Czech, THE Loan_Origination_Engine SHALL identify the document language and apply language-specific NLP extraction rules
3. WHEN a document of type identity card, proof of address, or income statement is submitted, THE Loan_Origination_Engine SHALL extract all required fields defined in the market-specific document schema
4. IF OCR confidence for any extracted field falls below 85%, THEN THE Loan_Origination_Engine SHALL flag the field for manual review and route the document to a human operator
5. WHEN document extraction is complete, THE Loan_Origination_Engine SHALL return structured data within 30 seconds of document submission

### Requirement 2: Automated Document Verification

**User Story:** As a credit assessment officer, I want submitted identity and proof documents to be automatically verified against validation rules, so that fraudulent or invalid documents are detected without manual inspection.

#### Acceptance Criteria

1. WHEN a customer identity document is extracted, THE Loan_Origination_Engine SHALL verify the document expiry date, format consistency, and cross-reference the name against the loan application
2. WHEN a proof of address document is extracted, THE Loan_Origination_Engine SHALL verify the address matches the customer's registered address within the loan application
3. WHEN an income document is extracted, THE Loan_Origination_Engine SHALL verify the stated income against the declared income on the loan application and flag discrepancies exceeding 10%
4. IF document verification fails any validation rule, THEN THE Loan_Origination_Engine SHALL generate a rejection reason code and notify the submitting Agent within 60 seconds
5. WHEN all documents for a loan application pass verification, THE Loan_Origination_Engine SHALL update the loan application status to "documents verified" in the FOCUS_System

### Requirement 3: Human-Verified Loan Approval with AI Assistance

**User Story:** As a credit assessor, I want the system to prepare loan applications with a recommendation and supporting data, so that I can make informed approval decisions efficiently while retaining full authority over every loan decision.

#### Acceptance Criteria

1. WHEN a loan application has status "documents verified", THE Loan_Origination_Engine SHALL generate a recommendation (approve, decline, or refer) with supporting data including credit score results, document verification outcomes, and risk indicators
2. WHEN a recommendation is generated, THE Loan_Origination_Engine SHALL present the prepared application to a human Credit_Assessor within 3 minutes of document verification completion
3. THE Loan_Origination_Engine SHALL route all loan applications to a human Credit_Assessor for final decision regardless of whether automated approval criteria are met
4. THE Loan_Origination_Engine SHALL prohibit automatic approval of any loan application without explicit human Credit_Assessor confirmation
5. WHEN a human Credit_Assessor records a final decision (approve or decline), THE Loan_Origination_Engine SHALL write the decision, the assessor's identity, reason codes, the AI-generated recommendation, and a full audit trail to the FOCUS_System via the integration layer
6. WHEN a human Credit_Assessor has not acted on a routed application within 30 minutes, THE Loan_Origination_Engine SHALL send a reminder notification to the Credit_Assessor and escalate to the team lead after 60 minutes

### Requirement 4: Agent Route Optimisation

**User Story:** As a field agent, I want my daily visit schedule to be optimised for minimal travel time, so that I can spend more time with customers and complete more visits per day.

#### Acceptance Criteria

1. WHEN an Agent's daily schedule is generated, THE Agent_Operations_Optimizer SHALL produce a route plan that minimises total travel time using geospatial optimisation algorithms
2. THE Agent_Operations_Optimizer SHALL factor in customer appointment windows, Agent working hours, and estimated visit duration when generating route plans
3. WHEN a route plan is generated, THE Agent_Operations_Optimizer SHALL provide turn-by-turn navigation data compatible with the Agent's mobile application
4. WHEN traffic or road condition data is available, THE Agent_Operations_Optimizer SHALL incorporate real-time conditions into route calculations
5. THE Agent_Operations_Optimizer SHALL generate route plans within 60 seconds of schedule finalisation

### Requirement 5: Dynamic Schedule Re-Optimisation

**User Story:** As a field agent, I want my schedule to adapt in real time when visits are cancelled or new urgent visits are added, so that my remaining time is used efficiently.

#### Acceptance Criteria

1. WHEN a scheduled visit is cancelled or a new visit is added during the working day, THE Agent_Operations_Optimizer SHALL recalculate the remaining route within 30 seconds
2. WHEN re-optimisation occurs, THE Agent_Operations_Optimizer SHALL notify the Agent via push notification on the mobile application with the updated route
3. WHILE an Agent is in transit, THE Agent_Operations_Optimizer SHALL preserve the current destination and re-optimise only subsequent visits
4. IF re-optimisation results in a visit that cannot be completed within working hours, THEN THE Agent_Operations_Optimizer SHALL flag the visit for rescheduling and notify the branch coordinator

### Requirement 6: Agent Location and Performance Tracking

**User Story:** As a branch manager, I want visibility of agent locations and visit completion status, so that I can monitor operational performance and provide support when needed.

#### Acceptance Criteria

1. WHILE an Agent is on duty, THE Agent_Operations_Optimizer SHALL collect GPS location data at intervals of no more than 5 minutes with Agent consent
2. WHEN an Agent arrives at a customer location, THE Agent_Operations_Optimizer SHALL record the arrival time and match it against the scheduled appointment
3. THE Agent_Operations_Optimizer SHALL provide a dashboard view showing all active Agents' current locations and visit completion rates for branch managers
4. WHEN an Agent deviates from the planned route by more than 15 minutes, THE Agent_Operations_Optimizer SHALL send an alert to the branch coordinator

### Requirement 7: AI-Powered Ticket Triage and Classification

**User Story:** As an IT support analyst, I want incoming service desk tickets to be automatically classified and prioritised, so that tickets reach the correct resolver group without manual sorting.

#### Acceptance Criteria

1. WHEN a new service desk ticket is created, THE AI_Service_Desk SHALL classify the ticket into a category and subcategory within 10 seconds of submission
2. WHEN a ticket is classified, THE AI_Service_Desk SHALL assign a priority level (Critical, High, Medium, Low) based on impact and urgency assessment from the ticket content
3. WHEN a ticket is classified and prioritised, THE AI_Service_Desk SHALL route the ticket to the appropriate resolver group based on category mapping rules
4. THE AI_Service_Desk SHALL achieve a classification accuracy of at least 90% measured against human-assigned categories over a rolling 30-day window
5. WHEN a ticket is submitted in Polish, Romanian, Hungarian, Spanish, Czech, or English, THE AI_Service_Desk SHALL process and classify the ticket in the original language

### Requirement 8: Automated Ticket Resolution

**User Story:** As an IT end user, I want common IT issues to be resolved automatically without waiting for a human analyst, so that I can return to productive work faster.

#### Acceptance Criteria

1. WHEN a ticket matches a known resolution pattern with confidence above 90%, THE AI_Service_Desk SHALL execute the automated resolution workflow and notify the requester
2. WHEN an automated resolution is applied, THE AI_Service_Desk SHALL request confirmation from the requester that the issue is resolved within 24 hours
3. IF the requester confirms the issue is not resolved, THEN THE AI_Service_Desk SHALL escalate the ticket to a human analyst with the attempted resolution details attached
4. IF no automated resolution pattern matches with confidence above 90%, THEN THE AI_Service_Desk SHALL route the ticket to a human analyst without delay
5. THE AI_Service_Desk SHALL log all automated resolution attempts and outcomes for continuous improvement analysis

### Requirement 9: Knowledge Management and Self-Service

**User Story:** As an IT end user, I want to search a knowledge base for solutions before raising a ticket, so that I can resolve common issues independently.

#### Acceptance Criteria

1. WHEN a user submits a search query, THE AI_Service_Desk SHALL return relevant knowledge articles ranked by relevance within 5 seconds
2. WHEN a user begins creating a ticket, THE AI_Service_Desk SHALL suggest relevant knowledge articles based on the ticket description before submission
3. THE AI_Service_Desk SHALL support knowledge article search and display in Polish, Romanian, Hungarian, Spanish, Czech, and English
4. WHEN an automated resolution is successful, THE AI_Service_Desk SHALL create or update a knowledge article documenting the resolution steps
5. THE AI_Service_Desk SHALL track knowledge article usage and surface the most effective articles for each ticket category

### Requirement 10: Automated Early-Stage Collections Contact

**User Story:** As a collections manager, I want early-stage overdue accounts to be contacted automatically via voice and SMS bots, so that human agents focus only on complex cases requiring negotiation.

#### Acceptance Criteria

1. WHEN a customer account reaches 1 day past due, THE Collections_Engine SHALL initiate an automated contact sequence via SMS in the customer's registered language
2. WHEN a customer account reaches 7 days past due without payment or arrangement, THE Collections_Engine SHALL initiate an automated voice call in the customer's registered language
3. THE Collections_Engine SHALL support automated conversations in Polish, Romanian, Hungarian, Spanish, and Czech with natural-sounding speech synthesis
4. WHEN a customer responds to an automated contact and agrees to a payment arrangement, THE Collections_Engine SHALL record the arrangement and update the account status in the FOCUS_System
5. WHEN an automated voice conversation detects customer distress, dispute, or complex negotiation need, THE Collections_Engine SHALL transfer the call to a human collections agent within 30 seconds

### Requirement 11: Collections Escalation and Handoff

**User Story:** As a collections agent, I want to receive full context when a case is escalated from automated handling, so that I can continue the conversation without asking the customer to repeat information.

#### Acceptance Criteria

1. WHEN a collections case is escalated to a human Agent, THE Collections_Engine SHALL provide the complete interaction history including transcripts, payment history, and previous arrangements
2. WHEN escalation occurs during a live voice call, THE Collections_Engine SHALL perform a warm transfer providing the human Agent with a real-time summary before connecting
3. IF a customer has not responded to 3 automated contact attempts across SMS and voice channels, THEN THE Collections_Engine SHALL escalate the account to a human Agent for direct follow-up
4. WHEN a case is escalated, THE Collections_Engine SHALL assign a priority score based on days past due, outstanding balance, and customer risk profile

### Requirement 12: FOCUS System Integration

**User Story:** As a systems architect, I want all automation solutions to integrate with the FOCUS core system through a standardised integration layer, so that data consistency is maintained and integration costs are manageable.

#### Acceptance Criteria

1. THE IPA_Platform SHALL communicate with the FOCUS_System exclusively through a defined integration layer that abstracts the underlying system coupling
2. WHEN any automation component writes data to the FOCUS_System, THE IPA_Platform SHALL validate the data against the FOCUS_System schema before submission
3. IF the FOCUS_System is unavailable, THEN THE IPA_Platform SHALL queue transactions and retry with exponential backoff until the system is available, notifying operations staff after 5 failed attempts
4. THE IPA_Platform SHALL maintain an audit log of all data exchanges with the FOCUS_System including timestamps, payload summaries, and outcome status
5. WHEN a new Market is onboarded, THE IPA_Platform SHALL support market-specific FOCUS_System configuration without requiring changes to the integration layer code

### Requirement 13: Data Privacy and GDPR Compliance

**User Story:** As a data protection officer, I want all automation components to enforce GDPR requirements, so that customer data is processed lawfully and IPF maintains regulatory compliance across all EU markets.

#### Acceptance Criteria

1. THE IPA_Platform SHALL process customer personal data only for the specific purpose declared at the point of collection, with a documented legal basis for each processing activity
2. WHEN a customer exercises a data access request, THE IPA_Platform SHALL provide all personal data held across automation components within 30 days
3. WHEN a customer exercises a data deletion request, THE IPA_Platform SHALL delete or anonymise personal data across all automation components within 30 days, except where legal retention obligations apply
4. THE IPA_Platform SHALL encrypt all customer personal data at rest using AES-256 and in transit using TLS 1.2 or higher
5. WHEN personal data is processed by any automation component, THE IPA_Platform SHALL log the processing activity including purpose, legal basis, data categories, and retention period
6. THE IPA_Platform SHALL enforce data residency requirements by storing and processing personal data within the EU region

### Requirement 14: Multi-Market Deployment and Configuration

**User Story:** As a programme manager, I want to deploy automation solutions to new markets using configuration rather than code changes, so that market rollout timelines are predictable and efficient.

#### Acceptance Criteria

1. THE IPA_Platform SHALL support market-specific configuration including language, currency, regulatory rules, and business thresholds without code modifications
2. WHEN a new Market is onboarded, THE IPA_Platform SHALL allow market-specific document templates, validation rules, and workflow parameters to be configured through an administration interface
3. THE IPA_Platform SHALL support concurrent operation across multiple Markets with complete data isolation between Markets
4. WHEN a configuration change is applied to a Market, THE IPA_Platform SHALL apply the change without affecting other Markets' operations
5. THE IPA_Platform SHALL support phased rollout by enabling or disabling individual solution areas per Market independently

### Requirement 15: Monitoring, Observability, and Reporting

**User Story:** As an operations manager, I want unified monitoring and reporting across all automation components, so that I can track programme benefits realisation and identify operational issues proactively.

#### Acceptance Criteria

1. THE IPA_Platform SHALL provide a unified dashboard showing key performance indicators for each solution area across all Markets
2. WHEN any automation component experiences an error rate exceeding 5% over a 15-minute window, THE IPA_Platform SHALL raise an alert to the operations team
3. THE IPA_Platform SHALL record processing volumes, success rates, processing times, and exception rates for each automation component
4. THE IPA_Platform SHALL generate monthly benefits realisation reports showing cost savings, processing time reductions, and automation rates against baseline measurements
5. WHEN an automation component's response time exceeds the defined threshold for that component, THE IPA_Platform SHALL log a performance warning and notify the operations team

### Requirement 16: Multi-Agent AI Architecture

**User Story:** As a solutions architect, I want the IPA platform to be built as a coordinated system of purpose-built AI agents with clear decision boundaries, so that each agent can be developed, tested, deployed, and scaled independently while maintaining system-wide governance.

#### Acceptance Criteria

1. THE IPA_Platform SHALL implement a multi-agent architecture with dedicated AI agents for document processing, route optimisation, collections contact, service desk operations, and reconciliation
2. THE IPA_Platform SHALL provide an orchestrator service that coordinates agent-to-agent communication, manages workflow state, and enforces execution order based on defined dependency graphs
3. WHEN any AI agent produces a decision or recommendation, THE IPA_Platform SHALL route that output through a shared policy gate middleware that validates the action against market-specific rules before execution
4. THE IPA_Platform SHALL maintain each AI agent as a stateless decision service with workflow state owned by the orchestrator, enabling independent scaling and deployment of individual agents
5. WHEN a new AI agent is added to the platform, THE IPA_Platform SHALL allow registration and integration without requiring changes to existing agents or the orchestrator core logic
6. THE IPA_Platform SHALL log every agent invocation, tool call, and decision with full traceability including inputs, outputs, policy version applied, and execution timestamp

### Requirement 17: Technology Portability and Cloud Agnosticism

**User Story:** As a technology director, I want the IPA platform architecture to support deployment on multiple cloud providers or technology stacks without fundamental redesign, so that the organisation retains strategic flexibility and avoids vendor lock-in on the AI layer.

#### Acceptance Criteria

1. THE IPA_Platform SHALL abstract LLM provider dependencies behind a model interface layer that allows switching between providers (OpenAI, Anthropic, AWS Bedrock, Google Vertex) without changes to agent logic
2. THE IPA_Platform SHALL support two validated technology stacks: an AWS-native stack (Step Functions, Bedrock, Textract, Connect, SageMaker) and a cloud-agnostic stack (LangGraph, open-source tools, Kubernetes)
3. THE IPA_Platform SHALL store all domain data in provider-neutral formats and storage systems (Snowflake, PostgreSQL) that are portable across cloud environments
4. WHEN a technology stack decision is made for a market deployment, THE IPA_Platform SHALL deploy using infrastructure-as-code templates specific to the chosen stack without requiring application code changes
5. THE IPA_Platform SHALL ensure that the policy gate, audit logging, and data residency controls function identically regardless of the underlying technology stack

### Requirement 18: AI Agent Policy Governance and Conduct Controls

**User Story:** As a compliance officer, I want every AI agent action to be governed by versioned, market-specific policy rules with mandatory human escalation paths, so that the platform operates within regulatory boundaries across all markets and no agent can take actions beyond its defined authority.

#### Acceptance Criteria

1. THE IPA_Platform SHALL maintain a versioned policy catalogue containing market-specific rules for contact windows, frequency caps, treatment envelopes, vulnerability screening, and conduct requirements
2. WHEN any AI agent attempts an action, THE policy gate SHALL validate the action against the applicable policy version and either permit, block, or escalate based on the rule outcome
3. IF a vulnerability signal is detected during any customer interaction (voice, SMS, or digital), THEN THE IPA_Platform SHALL immediately halt automated treatment and transfer to a trained human agent
4. THE IPA_Platform SHALL record which policy version governed each decision, enabling retrospective audit and regulatory evidence production
5. WHEN policy rules are updated for a market, THE IPA_Platform SHALL apply the new version to future decisions without requiring agent redeployment, while maintaining an immutable record of historical policy versions
6. THE IPA_Platform SHALL support champion/challenger experimentation at the branch or cell level, with pre-registered metrics and complaint-rate thresholds that trigger automatic rollback if exceeded

### Requirement 19: Mock Credit Scoring (PoC Phase)

**User Story:** As a credit assessor, I want to see a bureau-style credit score derived from extracted document data across all four PoC markets, so that I can assess financial risk before making a final loan decision.

#### Acceptance Criteria

1. THE IPA_Platform SHALL compute a mock credit score on a 0-1000 point scale using five weighted factors: Income Adequacy (300pts), Employment Stability (200pts), Identity Validity (200pts), Document Consistency (200pts), and Age and Eligibility (100pts)
2. THE IPA_Platform SHALL classify scores into five risk bands: EXCELLENT (800-1000), GOOD (650-799), FAIR (500-649), POOR (350-499), HIGH RISK (0-349)
3. THE IPA_Platform SHALL apply market-specific income thresholds: 2,500 PLN for Poland, 1,500 RON for Romania, 150,000 HUF for Hungary, and 20,000 CZK for Czech Republic
4. THE IPA_Platform SHALL reference the appropriate national credit bureau name in all score outputs: BIK for Poland, Biroul de Credit for Romania, BISZ/KHR for Hungary, and CBCB for Czech Republic
5. ALL credit score outputs SHALL include the disclaimer that the score is a mock simulation and must be replaced with live bureau API integration in production
6. THE IPA_Platform SHALL expose credit scores via a dedicated REST endpoint that returns the score, risk band, per-factor breakdown, risk flags, and scoring recommendation alongside the AI document recommendation in the Credit Assessor decision screen

### Requirement 20: Observability and Tracing

**User Story:** As a platform engineer, I want all AI agent invocations to be traced in an observability platform, so that I can inspect agent reasoning, debug failures, and monitor performance across the processing pipeline.

#### Acceptance Criteria

1. THE IPA_Platform SHALL integrate with LangSmith for tracing all LangChain and LangGraph operations when LANGCHAIN_TRACING_V2, LANGCHAIN_API_KEY, and LANGCHAIN_PROJECT environment variables are present
2. WHEN tracing is active, THE IPA_Platform SHALL record a trace for every orchestrator workflow run capturing each graph node as a distinct span with inputs, outputs, and latency
3. WHEN tracing is active, THE IPA_Platform SHALL record every LLM call with prompt, completion, model name, token counts, and latency
4. THE IPA_Platform SHALL operate normally without tracing when LangSmith credentials are not configured

### Requirement 21: Loan Application Form as Reference Document

**User Story:** As a loan origination officer, I want the customer's completed loan application form to be uploaded and extracted alongside supporting documents, so that all declared information is captured as the authoritative reference for cross-verification.

#### Acceptance Criteria

1. THE Loan_Origination_Engine SHALL accept a loan application form as a distinct document type (loan_application) in addition to identity, address, and income supporting documents
2. WHEN a loan application document is extracted, THE Loan_Origination_Engine SHALL capture all declared fields including applicant name, date of birth, residential address, declared income, requested loan amount, loan term, employment status, and bank account details
3. THE extracted loan application data SHALL be stored as the reference dataset for the application and SHALL be accessible to all downstream agents for cross-verification

### Requirement 22: Automated Cross-Reference and Discrepancy Detection

**User Story:** As a compliance officer, I want the system to automatically detect inconsistencies between what a customer declared on their loan application and the evidence provided in supporting documents, so that fraud indicators and data quality issues are surfaced before human review.

#### Acceptance Criteria

1. WHEN all documents for a loan application are extracted, THE Loan_Origination_Engine SHALL automatically compare declared loan application fields against corresponding fields in supporting documents
2. THE cross-reference SHALL cover: applicant name (identity document), date of birth (identity document), residential address (proof of address), net income (income document), and bank account number (bank statement)
3. FOR each comparison, THE Loan_Origination_Engine SHALL classify the result as MATCH, WARNING (partial match within tolerance), MISMATCH, or UNVERIFIABLE and assign severity: HIGH for identity mismatches, MEDIUM for address mismatches, and LOW for minor financial variances
4. IF any HIGH severity discrepancy is detected, THE Loan_Origination_Engine SHALL escalate the application to a senior credit assessor and flag it prominently in the review queue

### Requirement 23: Consolidated Application Review Interface

**User Story:** As a credit assessor, I want a single review screen that shows the loan application, all supporting documents, and a cross-reference discrepancy report side by side, so that I can make an informed approval decision without navigating multiple screens.

#### Acceptance Criteria

1. THE review interface SHALL present three integrated panels: loan application declared fields, supporting document extractions with confidence scores, and a cross-reference discrepancy report
2. EACH discrepancy SHALL show the declared value, extracted value, mismatch severity, and a field for the reviewer to record an override explanation
3. WHEN a reviewer overrides a discrepancy, THE system SHALL log the override with reviewer identity, timestamp, and justification in the audit trail

### Requirement 24: Credit Assessor Decision Portal

**User Story:** As a credit assessor, I want a dedicated portal separate from the document reviewer interface, showing only the information I need to make credit decisions, so that my workflow is clean and focused without distracting technical details.

#### Acceptance Criteria

1. THE Credit_Assessor portal SHALL be a separate Streamlit application served on port 8503, accessible only to users with the credit assessor password
2. THE portal SHALL provide four pages: Decision Queue (applications awaiting decision), Application Summary (one-page overview), Loan Decision (approve/decline), and Decision History
3. THE Application Summary page SHALL display: applicant declared details, credit score gauge with risk band, score breakdown by factor, and risk flags with human-readable explanation text for each flag
4. THE Loan Decision page SHALL require the assessor to select reason codes before declining a loan; approvals SHALL record the assessor ID, timestamp, and any notes
5. THE portal SHALL NOT display raw OCR confidence scores, field extraction details, or document correction controls â€” these are the domain of the Document Reviewer portal

### Requirement 25: Risk Flag Explanations

**User Story:** As a credit assessor, I want each detected risk flag to include a plain-language explanation of what the flag means and why it matters, so that I can make an informed decision without needing to interpret technical output.

#### Acceptance Criteria

1. FOR each risk flag produced by the Credit_Score_Agent, THE system SHALL display an explanation covering: what the flag detected, why it is a concern for lending, and what action the assessor should consider
2. THE explanations SHALL be tailored to the flag type: income discrepancy, expired document, address mismatch, name inconsistency, employment not verified, and age outside eligible range
3. THE explanations SHALL be displayed as expandable panels beneath each flag, collapsed by default to avoid cluttering the decision screen

### Requirement 26: Audit Trail Visualisation

**User Story:** As a document reviewer, I want to see both the raw event log and a visual pipeline flowchart in the audit trail, so that I can quickly understand where an application is in the processing pipeline and what events have occurred.

#### Acceptance Criteria

1. THE Audit Trail page SHALL display a two-column layout: event log on the left, processing pipeline flowchart on the right
2. THE pipeline flowchart SHALL show all defined processing stages as circular nodes connected by vertical lines, colour-coded as: red (not started), amber (currently processing), green (completed)
3. THE pipeline SHALL include stages: Documents Uploaded, Loan App Extracted, Documents Extracted, Cross-Reference Check, Pending Review, Field Corrections, Document Confirmed, AI Recommendation, Loan Approved/Declined
