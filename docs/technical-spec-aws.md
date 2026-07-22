# Technical Specification: IPF IPA - AWS-Native Stack

## Document Control

| Item | Detail |
|------|--------|
| Version | 1.0 |
| Date | July 2026 |
| Classification | CONFIDENTIAL - Internal Working Draft |
| Prepared by | Mastek AI CoE |

---

## 1. Executive Summary

This specification defines the technical architecture for IPF Intelligent Process Automation (IPA) programme using AWS-native services, leveraging IPF existing AWS estate and Mastek operational presence on the platform.

---

## 2. Design Principles

1. Extend dont replace - Build on IPF existing AWS estate and Strategic Data Store
2. Managed-first - Prefer AWS managed services over self-hosted
3. Policy-gated - Every agent action passes through policy middleware
4. Human-in-the-loop native - Step Functions human approval tasks enforce mandatory checkpoints
5. Audit-complete - CloudTrail plus custom audit logs for full decision traceability
6. Offline-resilient - Agent mobile apps operate with cached plans during connectivity loss
7. Multilingual-native - Amazon Bedrock handles multi-language reasoning across all agents

---

## 3. Component Mapping

### 3.1 Orchestrator
- Service: AWS Step Functions (Standard Workflows)
- Coordination: EventBridge for event-driven agent-to-agent messaging
- Human approval: Step Functions waitForTaskToken
- Scaling: Automatic, no capacity planning

### 3.2 Document Processing Agent
- OCR: Amazon Textract (AnalyzeDocument + AnalyzeID)
- NLP: Amazon Bedrock (Claude 3.5 Sonnet) with market-specific prompts
- Language: Amazon Comprehend
- Storage: S3 (images) + DynamoDB (results)
- SLA: Under 30 seconds per document

### 3.3 Route Planning Agent
- Solver: Google OR-Tools on ECS Fargate
- Travel: Amazon Location Service
- Predictions: SageMaker endpoints
- Output: Route plan via AppSync to agent mobile app
- SLA: Under 60 seconds per weekly plan

### 3.4 Collections Contact Agent
- Voice: Amazon Connect (outbound campaigns)
- Dialogue: Amazon Lex + Bedrock (multilingual)
- SMS: Amazon Pinpoint
- Policy: Lambda authoriser + DynamoDB rules
- Languages: Polish, Romanian, Hungarian, Spanish, Czech
- Vulnerability: Bedrock classifier on transcripts
- Escalation: Connect transfer under 30 seconds

### 3.5 Service Desk Agent
- Triage: Bedrock Agent with ITSM tools
- RAG: Amazon Kendra or OpenSearch Serverless
- Auto-resolution: Bedrock Agent + Lambda tools
- Confidence: 90 percent threshold for auto-resolution
- Languages: 6 languages supported
- SLA: Classification under 10 seconds

### 3.6 Reconciliation Agent
- Matching: Lambda + Step Functions
- Anomaly: SageMaker endpoint (Isolation Forest)
- Triage: Bedrock for exception narratives
- Input: Kinesis stream of transactions

---

## 4. Shared Services

### Policy Gate
- Runtime: Lambda Python 3.12
- Store: DynamoDB (market-partitioned)
- Cache: ElastiCache Redis (under 5ms lookup)
- Versioning: Immutable versioned items

### Bedrock Guardrails
- Content filtering for collections conversations
- Block financial commitments and legal advice generation
- PII detection and redaction
- Per-market conduct rules

### Observability
- Tracing: AWS X-Ray
- Logs: CloudWatch (90-day hot, S3 cold)
- Alerting: CloudWatch Alarms to SNS
- Bedrock: Model invocation logging to S3

---

## 5. Data Architecture

| Store | Service | Purpose |
|-------|---------|---------|
| Operational DB | RDS PostgreSQL Multi-AZ | Workflow state, review queue |
| Key-value | DynamoDB | Policy, extraction results |
| Warehouse | Snowflake on AWS | SDS, analytics |
| Vector | OpenSearch Serverless | RAG embeddings |
| Cache | ElastiCache Redis | Policy cache |
| Objects | S3 | Documents, recordings |
| Events | MSK or Kinesis | FOCUS integration |
| Search | Amazon Kendra | Knowledge base |

### FOCUS Integration
- Real-time: Kinesis to FOCUS Bridge Lambda to FOCUS API
- Batch: FOCUS to S3 to Glue ETL to Snowflake
- Failure: DLQ, exponential backoff, alarm after 5 failures
- Audit: Every exchange logged

---

## 6. ML Services (SageMaker)

| Model | Purpose |
|-------|---------|
| Visit-window predictor | Best time to visit customer |
| Collection propensity | Payment likelihood |
| Cure probability | Arrears resolution likelihood |
| Anomaly detection | Reconciliation exceptions |
| Document classifier | Document type ID |

Supporting: Feature Store, Experiments, Model Registry, Model Monitor, Clarify

---

## 7. Security and Compliance

- Auth: Cognito (users) + IAM Identity Centre (internal)
- Network: Private subnets, VPC endpoints, no public internet
- Encryption: KMS CMKs per-market, AES-256 at rest, TLS 1.3 transit
- GDPR: EU-only processing (eu-west-1), lifecycle policies, deletion pipeline
- Audit: CloudTrail + S3 archive (immutable, 7-year retention)
- EU AI Act: Model Cards, Clarify bias monitoring, model registry
- Protection: GuardDuty, Security Hub, Inspector, WAF

---

## 8. Cost Estimate (Annual at Scale)

| Component | GBP per annum |
|-----------|---------------|
| Bedrock | 120k-200k |
| Lambda + Step Functions | 30k-60k |
| ECS Fargate | 40k-70k |
| Connect (5 markets) | 80k-150k |
| SageMaker | 50k-90k |
| Textract | 30k-50k |
| RDS + DynamoDB + ElastiCache | 60k-100k |
| MSK / Kinesis | 25k-45k |
| S3 + transfer | 20k-40k |
| Kendra / OpenSearch | 30k-50k |
| Other | 20k-35k |
| TOTAL | 505k-890k |

---

## 9. Delivery Phases

| Phase | Duration | Scope |
|-------|----------|-------|
| Phase 0 | 6-8 weeks | CDK infra, Step Functions, Bedrock POC, FOCUS bridge |
| Wave 1 MVP-A | 3-4 months | Document Agent in one EU market |
| Wave 1 MVP-B | 3-4 months | Route Agent in Mexico |
| Wave 2 | Months 5-9 | Service Desk, Recon, Nudge Agents |
| Wave 3 | Months 9-18 | Collections Agent, multi-market scale |

---

## 10. AWS Advantages for IPF

- IPF already on AWS with SDS on Snowflake
- Mastek already manages the data platform
- Bedrock offers multiple models (Claude, Titan, Llama)
- Connect plus Lex is purpose-built for contact centres
- Textract pre-trained on European ID formats
- SageMaker covers full ML lifecycle
- All services auto-scale
- eu-west-1 has ISO 27001, SOC 2, GDPR, DORA compliance

---

## 11. Risks

| Risk | Mitigation |
|------|-----------|
| Bedrock EU availability | eu-west-1 has Claude + Titan |
| Connect multilingual limits | Custom Lex bots + Bedrock |
| Textract on handwritten | Bedrock post-processing + human fallback |
| FOCUS latency | Async-first design |
| Cost at volume | Provisioned throughput + model tiering |
| Vendor lock-in | Snowflake portable, standard patterns |
