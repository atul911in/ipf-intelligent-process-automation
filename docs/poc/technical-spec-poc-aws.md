# PoC Technical Specification: AWS-Native Stack

## Document Control

| Item | Detail |
|------|--------|
| Version | 1.0 |
| Date | July 2026 |
| Scope | PoC - Orchestrator + Document Extraction Agent |
| Classification | CONFIDENTIAL - Internal Working Draft |
| Prepared by | Mastek AI CoE |

---

## 1. Overview

This specification defines the technical design for the IPF IPA Proof of Concept using AWS-native services. The PoC scope is: (1) AWS Step Functions as the Orchestrator, and (2) Amazon Textract + Bedrock as the Document Extraction Agent. Designed for deployment on IPF existing AWS estate.

---

## 2. Architecture

`
                    +-------------------+
                    | API Gateway (REST) |
                    +---------+---------+
                              |
                    +---------v---------+
                    | AWS STEP FUNCTIONS |
                    |                    |
                    | - State Machine    |
                    | - EventBridge      |
                    | - Policy Lambda    |
                    | - Human Task Token |
                    +---------+---------+
                              |
              +---------------+---------------+
              |                               |
    +---------v---------+           +---------v---------+
    |  DOCUMENT LAMBDA  |           |  HUMAN REVIEW     |
    |  CHAIN            |           |  (SQS + AppSync)  |
    |                   |           |                    |
    |  - Textract Call  |           +--------------------+
    |  - Comprehend     |
    |  - Bedrock Extract|
    |  - Validator      |
    +---------+---------+
              |
    +---------v---------+
    |  AWS SERVICES     |
    |                   |
    |  - Textract       |
    |  - Comprehend     |
    |  - Bedrock Claude |
    |  - FOCUS Mock ECS |
    +---------+---------+
              |
    +---------v---------+
    |  DATA LAYER       |
    |                   |
    |  - S3 (documents) |
    |  - DynamoDB       |
    |  - RDS PostgreSQL |
    +-------------------+
`

---

## 3. Step Functions Orchestrator

### 3.1 State Machine Definition

`json
{
  "Comment": "IPF IPA PoC - Document Processing Workflow",
  "StartAt": "ExtractDocuments",
  "States": {
    "ExtractDocuments": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:ipf-poc-extract",
      "Retry": [{"ErrorEquals": ["States.TaskFailed"], "MaxAttempts": 3, "BackoffRate": 2}],
      "Next": "ValidateFields",
      "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "HandleFailure"}]
    },
    "ValidateFields": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:ipf-poc-validate",
      "Next": "PolicyGateCheck"
    },
    "PolicyGateCheck": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:ipf-poc-policy-gate",
      "Next": "RouteDecision"
    },
    "RouteDecision": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.policyResult.needsHumanReview",
          "BooleanEquals": true,
          "Next": "HumanDocumentReview"
        },
        {
          "Variable": "$.policyResult.blocked",
          "BooleanEquals": true,
          "Next": "HandleFailure"
        }
      ],
      "Default": "GenerateRecommendation"
    },
    "HumanDocumentReview": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
      "Parameters": {
        "QueueUrl": "HUMAN_REVIEW_QUEUE_URL",
        "MessageBody": {
          "taskToken.$": "UTF8.Task.Token",
          "workflowId.$": "$.workflowId",
          "reviewData.$": "$.fieldsNeedingReview"
        }
      },
      "TimeoutSeconds": 3600,
      "Next": "ValidateFields"
    },
    "GenerateRecommendation": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:ipf-poc-recommend",
      "Next": "CreditAssessorReview"
    },
    "CreditAssessorReview": {
      "Type": "Task",
      "Resource": "arn:aws:states:::sqs:sendMessage.waitForTaskToken",
      "Comment": "MANDATORY human approval - no loan auto-approved",
      "Parameters": {
        "QueueUrl": "CREDIT_ASSESSOR_QUEUE_URL",
        "MessageBody": {
          "taskToken.$": "UTF8.Task.Token",
          "workflowId.$": "$.workflowId",
          "recommendation.$": "$.recommendation"
        }
      },
      "TimeoutSeconds": 7200,
      "Next": "RecordDecision"
    },
    "RecordDecision": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:ipf-poc-record",
      "Next": "WorkflowComplete"
    },
    "WorkflowComplete": {
      "Type": "Succeed"
    },
    "HandleFailure": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:eu-west-1:ACCOUNT:function:ipf-poc-failure",
      "Next": "WorkflowFailed"
    },
    "WorkflowFailed": {
      "Type": "Fail",
      "Cause": "Workflow failed after retries or policy block"
    }
  }
}
`

### 3.2 Human-in-the-Loop Pattern

`
Step Functions (waitForTaskToken)
    -> SQS (review queue)
    -> Human Review UI (reads from SQS)
    -> Human submits correction
    -> Lambda (sends SendTaskSuccess with token)
    -> Step Functions resumes
`

### 3.3 Orchestrator Characteristics

| Attribute | Specification |
|-----------|--------------|
| Service | Step Functions Standard Workflow |
| Max duration | 1 year (supports long human review waits) |
| Retry | 3 attempts with exponential backoff per step |
| Concurrency | 1,000+ (Step Functions default) |
| State size | 256 KB per execution (sufficient for PoC) |
| Cost | Pay per state transition (pennies per workflow) |

---

## 4. Document Extraction Lambda Chain

### 4.1 Extraction Pipeline

`
S3 Event (document uploaded)
  -> Lambda: ipf-poc-extract
      1. Call Textract AnalyzeDocument (for general docs)
         OR Textract AnalyzeID (for identity documents)
      2. Call Comprehend DetectDominantLanguage
      3. Call Bedrock InvokeModel (Claude 3.5 Sonnet)
         - Prompt: Extract fields per market schema
         - Input: Textract raw text + document type
         - Output: Structured JSON with field values
      4. Compute confidence scores per field
      5. Return extraction result to Step Functions
`

### 4.2 Lambda Functions

| Function | Runtime | Memory | Timeout | Purpose |
|----------|---------|--------|---------|---------|
| ipf-poc-extract | Python 3.12 | 1024 MB | 60s | OCR + NLP extraction |
| ipf-poc-validate | Python 3.12 | 512 MB | 30s | Field validation + cross-ref |
| ipf-poc-policy-gate | Python 3.12 | 256 MB | 10s | Policy rule evaluation |
| ipf-poc-recommend | Python 3.12 | 512 MB | 30s | Compile recommendation package |
| ipf-poc-record | Python 3.12 | 256 MB | 10s | Write to FOCUS mock + audit |
| ipf-poc-failure | Python 3.12 | 256 MB | 10s | Error handling + alerting |
| ipf-poc-resume | Python 3.12 | 256 MB | 10s | Process human input, send task token |

### 4.3 Textract Configuration

`python
import boto3

textract = boto3.client('textract', region_name='eu-west-1')

# For identity documents
def extract_id_document(bucket, key):
    response = textract.analyze_id(
        DocumentPages=[{'S3Object': {'Bucket': bucket, 'Name': key}}]
    )
    return response['IdentityDocuments']

# For general documents (utility bills, payslips)
def extract_general_document(bucket, key):
    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['FORMS', 'TABLES']
    )
    return response['Blocks']
`

### 4.4 Bedrock Field Extraction

`python
import boto3, json

bedrock = boto3.client('bedrock-runtime', region_name='eu-west-1')

def extract_fields_with_bedrock(raw_text, document_type, market, schema):
    prompt = f"""Extract the following fields from this {document_type} document.
Market: {market}
Required fields: {json.dumps(schema['required_fields'])}

Document text:
{raw_text}

Return a JSON object with each field name as key and extracted value.
Include a confidence estimate (0.0-1.0) for each field.
If a field cannot be found, set value to null and confidence to 0.0.
"""
    response = bedrock.invoke_model(
        modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        })
    )
    return json.loads(response['body'].read())
`

---

## 5. Policy Gate Lambda

`python
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
policy_table = dynamodb.Table('ipf-poc-policy-rules')

def lambda_handler(event, context):
    market = event['market']
    extraction = event['extractionResults']
    
    # Load active policy rules for market
    rules = load_rules(market)
    
    decisions = []
    needs_review = False
    blocked = False
    
    for rule in rules:
        result = evaluate_rule(rule, extraction)
        decisions.append({
            'ruleId': rule['ruleId'],
            'ruleVersion': rule['version'],
            'result': result['outcome'],
            'timestamp': datetime.utcnow().isoformat()
        })
        if result['outcome'] == 'FLAG_FOR_REVIEW':
            needs_review = True
        elif result['outcome'] == 'BLOCK':
            blocked = True
    
    # Log all decisions to audit table
    log_policy_decisions(event['workflowId'], decisions)
    
    return {
        'needsHumanReview': needs_review,
        'blocked': blocked,
        'decisions': decisions,
        'fieldsNeedingReview': [f for f in extraction if f['confidence'] < 85]
    }
`

---

## 6. Data Stores

| Store | Service | Purpose | PoC Config |
|-------|---------|---------|-----------|
| Documents | S3 | Uploaded document images | Single bucket, lifecycle 90 days |
| Extraction results | DynamoDB | Per-document extraction data | On-demand capacity |
| Policy rules | DynamoDB | Versioned market rules | Pre-loaded for PoC market |
| Audit trail | DynamoDB | Immutable decision log | TTL disabled (retain all) |
| Workflow state | Step Functions | Execution history | Built-in, 90-day retention |
| FOCUS mock data | RDS PostgreSQL | Loan application reference data | db.t3.micro |
| Human review queue | SQS | Pending review items | Standard queue |
| Assessor queue | SQS | Pending loan decisions | Standard queue |

---

## 7. FOCUS Mock API

`python
# ECS Fargate service simulating FOCUS system
# Provides loan application data for cross-reference
# Accepts decision writes

from fastapi import FastAPI
app = FastAPI()

@app.get("/api/v1/applications/{app_id}")
def get_application(app_id: str):
    """Return mock loan application data for cross-reference."""
    return {
        "applicationId": app_id,
        "customerName": "Jan Kowalski",
        "declaredIncome": 5500.00,
        "registeredAddress": "ul. Marszalkowska 1, Warszawa",
        "status": "DOCUMENTS_PENDING"
    }

@app.post("/api/v1/applications/{app_id}/decision")
def record_decision(app_id: str, decision: dict):
    """Record loan decision from credit assessor."""
    # Validate and store
    return {"status": "recorded", "applicationId": app_id}
`

---

## 8. Infrastructure as Code (CDK)

`	ypescript
// Simplified CDK stack structure
export class IpfPocStack extends cdk.Stack {
  constructor(scope: Construct, id: string) {
    super(scope, id);

    // S3 bucket for documents
    const docBucket = new s3.Bucket(this, 'DocBucket', {
      encryption: s3.BucketEncryption.KMS,
      enforceSSL: true,
    });

    // DynamoDB tables
    const auditTable = new dynamodb.Table(this, 'AuditTable', {
      partitionKey: { name: 'workflowId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // Lambda functions
    const extractFn = new lambda.Function(this, 'ExtractFn', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.lambda_handler',
      code: lambda.Code.fromAsset('lambda/extract'),
      timeout: cdk.Duration.seconds(60),
      memorySize: 1024,
    });

    // Grant Textract and Bedrock access
    extractFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['textract:AnalyzeDocument', 'textract:AnalyzeID'],
      resources: ['*'],
    }));
    extractFn.addToRolePolicy(new iam.PolicyStatement({
      actions: ['bedrock:InvokeModel'],
      resources: ['arn:aws:bedrock:eu-west-1::foundation-model/*'],
    }));

    // Step Functions state machine
    const stateMachine = new sfn.StateMachine(this, 'DocWorkflow', {
      definitionBody: sfn.DefinitionBody.fromFile('statemachine/workflow.asl.json'),
    });
  }
}
`

---

## 9. Observability (PoC)

| Concern | AWS Service | Detail |
|---------|-------------|--------|
| Workflow tracking | Step Functions console | Visual execution graph |
| Lambda logs | CloudWatch Logs | Structured JSON, per-function |
| Tracing | X-Ray | End-to-end request traces |
| Metrics | CloudWatch Metrics | Custom: extraction time, accuracy |
| Alerting | CloudWatch Alarm + SNS | Error rate over 5 percent |
| Bedrock usage | CloudWatch | Token consumption per invocation |
| Cost | Cost Explorer | Per-service daily breakdown |

---

## 10. Security (PoC)

| Concern | Implementation |
|---------|---------------|
| IAM | Least-privilege per Lambda; Step Functions execution role |
| Encryption | S3 SSE-KMS; DynamoDB encryption; RDS encryption |
| Network | Lambda in VPC (private subnet) for RDS access |
| API auth | API Gateway with IAM auth (PoC); Cognito for production |
| Secrets | Secrets Manager for API keys, DB credentials |
| Data residency | All resources in eu-west-1 |

---

## 11. Testing Strategy

| Test Type | Scope | Tool |
|-----------|-------|------|
| Unit tests | Lambda functions, validators | pytest + moto (AWS mocking) |
| Integration | Step Functions + Lambdas | AWS SAM local + Step Functions Local |
| Document accuracy | Textract + Bedrock on test corpus | Custom eval script |
| End-to-end | Full workflow via API Gateway | pytest + requests |
| Load test | 100 concurrent executions | Artillery / custom script |

---

## 12. PoC Timeline

| Week | Deliverable |
|------|-------------|
| 1-2 | CDK stack; S3, DynamoDB, Lambda scaffolds; FOCUS mock on ECS |
| 3-4 | Textract + Bedrock extraction pipeline; Polish/Romanian schemas |
| 5-6 | Policy gate Lambda; validation logic; confidence scoring |
| 7-8 | Step Functions state machine; SQS human review; resume Lambda |
| 9-10 | Human review UI (simple React on Amplify); end-to-end flow |
| 11-12 | Accuracy testing on 200 doc corpus; performance; exit criteria |

---

## 13. PoC Cost Estimate

| Component | Monthly Cost (GBP) |
|-----------|-------------------|
| Textract (200 docs x iterations) | 50-100 |
| Bedrock Claude (200 docs x iterations) | 100-300 |
| Lambda executions | 5-20 |
| Step Functions transitions | 5-10 |
| S3 + DynamoDB | 10-20 |
| RDS (FOCUS mock, db.t3.micro) | 15-25 |
| ECS Fargate (FOCUS mock) | 30-50 |
| API Gateway | 5-10 |
| CloudWatch + X-Ray | 10-20 |
| **Total PoC monthly run** | **230-555** |

Note: AWS PoC is roughly half the cost of LangChain PoC due to managed services and no external LLM API markup.

---

## 14. Exit Criteria (Maps to PoC Requirements)

| Criterion | Target | Measurement |
|-----------|--------|-------------|
| Extraction accuracy | 90 percent+ | Textract + Bedrock vs ground truth |
| Workflow reliability | Less than 1 percent failure | Step Functions execution history |
| End-to-end latency | Under 3 minutes (p95) | CloudWatch custom metric |
| Concurrent workflows | 100+ | Step Functions concurrent executions |
| Human-in-the-loop | Demonstrated working | QA walkthrough of SQS + resume flow |
| Cost per document | Documented | Cost Explorer / document count |

---

## 15. AWS vs LangChain PoC Comparison

| Dimension | AWS PoC | LangChain PoC |
|-----------|---------|---------------|
| Setup time | Faster (CDK + managed services) | More config (Docker, PostgreSQL, MinIO) |
| Monthly cost | 230-555 GBP | 500-1100 GBP |
| Operational burden | Low (serverless) | Medium (containers to manage) |
| Debugging | Step Functions visual console | LangSmith traces (if configured) |
| Portability | AWS-locked | Deploy anywhere |
| Transition to prod | CDK to multi-env pipeline | K8s manifests to production cluster |
| Model flexibility | Bedrock (Claude, Titan, Llama) | Any provider (OpenAI, Anthropic, etc.) |

---

## 16. UI and Event Architecture (Requirements 11-13)

### 16.1 Architecture with UI Layer

`
+------------------+                  +--------------------+
|  ADMIN UI        |                  |  REVIEWER UI       |
|  (React/Amplify) |                  |  (React/Amplify)   |
|                  |                  |                    |
|  - Doc upload    |                  |  - Work queue      |
|  - Batch submit  |                  |  - Doc viewer      |
|  - Upload history|                  |  - Field editor    |
+--------+---------+                  |  - Confidence view |
         |                            |  - Approve/Decline |
         | Upload to S3               +--------+-----------+
         v                                     |
+------------------+     S3 Event      +-------+----------+
|  S3 Bucket       |----------------->| EventBridge       |
|  (Persistent)    |  (on PutObject)   +-------+----------+
+------------------+                           |
                                               | Rule triggers
                                               v
                                      +--------+----------+
                                      | Lambda: Start     |
                                      | Step Functions    |
                                      | Workflow          |
                                      +-------------------+
                                               |
                                      +--------v----------+
                                      | STEP FUNCTIONS    |
                                      | STATE MACHINE     |
                                      +-------------------+
`

### 16.2 Admin UI (Document Upload Portal)

| Attribute | Specification |
|-----------|--------------|
| Framework | React 18 + Next.js 14, hosted on AWS Amplify |
| Auth | Amazon Cognito (user pool group: back-office-admin) |
| Upload | AWS Amplify Storage (direct S3 upload with presigned URLs) |
| Max batch | 20 files per submission |
| Formats | JPEG, PNG, PDF, TIFF (validated client-side + Lambda) |
| Max file size | 25 MB per file |
| Storage | S3 bucket with versioning enabled - permanent retention |
| Metadata | DynamoDB table for upload records |

**Key Pages:**
- /upload - Drag-and-drop with application ID and document type per file
- /history - Searchable upload history with DynamoDB query
- /history/:batchId - Batch detail with per-file processing status

**Upload Flow (S3 Presigned URL pattern):**

`
1. Admin UI calls API Gateway -> Lambda (get-presigned-url)
2. Lambda validates user role, generates S3 presigned PUT URL
3. Admin UI uploads directly to S3 (no API Gateway size limits)
4. S3 PutObject event fires -> EventBridge
5. Lambda writes metadata to DynamoDB
6. EventBridge rule triggers Step Functions workflow
`

**Lambda: Generate Presigned URL**

`python
import boto3, json
from uuid import uuid4

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ipf-poc-documents')

def lambda_handler(event, context):
    body = json.loads(event['body'])
    user_id = event['requestContext']['authorizer']['claims']['sub']
    
    batch_id = str(uuid4())
    presigned_urls = []
    
    for doc in body['documents']:
        doc_id = str(uuid4())
        key = f"{body['application_id']}/{batch_id}/{doc_id}/{doc['filename']}"
        
        url = s3.generate_presigned_url('put_object', Params={
            'Bucket': 'ipf-poc-documents',
            'Key': key,
            'ContentType': doc['content_type']
        }, ExpiresIn=300)
        
        # Write metadata
        table.put_item(Item={
            'documentId': doc_id,
            'batchId': batch_id,
            'applicationId': body['application_id'],
            'documentType': doc['document_type'],
            'market': body['market'],
            'storageKey': key,
            'uploadedBy': user_id,
            'status': 'UPLOADING',
            'createdAt': datetime.utcnow().isoformat()
        })
        
        presigned_urls.append({
            'document_id': doc_id,
            'upload_url': url,
            'filename': doc['filename']
        })
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'batch_id': batch_id,
            'presigned_urls': presigned_urls
        })
    }
`

### 16.3 Event-Driven Processing Trigger

| Attribute | Specification |
|-----------|--------------|
| Event source | S3 Event Notification -> EventBridge |
| Event type | Object Created (PutObject) |
| Rule | EventBridge rule matches S3 bucket + prefix pattern |
| Target | Lambda function that starts Step Functions execution |
| Latency | S3 event within 1-5 seconds of upload completion |
| Idempotency | Lambda checks if execution already exists for batch_id |
| DLQ | SQS dead-letter queue for failed event processing |

**EventBridge Rule:**

`json
{
  "source": ["aws.s3"],
  "detail-type": ["Object Created"],
  "detail": {
    "bucket": {"name": ["ipf-poc-documents"]},
    "object": {"key": [{"prefix": ""}]}
  }
}
`

**Lambda: Start Workflow (triggered by last file in batch):**

`python
import boto3, json

sfn = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ipf-poc-documents')

def lambda_handler(event, context):
    # Get document metadata from S3 event
    key = event['detail']['object']['key']
    parts = key.split('/')
    application_id, batch_id = parts[0], parts[1]
    
    # Update document status
    doc_id = parts[2]
    table.update_item(
        Key={'documentId': doc_id},
        UpdateExpression='SET #s = :s',
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={':s': 'UPLOADED'}
    )
    
    # Check if all docs in batch are uploaded
    batch_docs = table.query(
        IndexName='batch-index',
        KeyConditionExpression='batchId = :bid',
        ExpressionAttributeValues={':bid': batch_id}
    )['Items']
    
    all_uploaded = all(d['status'] == 'UPLOADED' for d in batch_docs)
    
    if all_uploaded:
        # Idempotency: check if workflow already started
        execution_name = f"batch-{batch_id}"
        try:
            sfn.start_execution(
                stateMachineArn=STATE_MACHINE_ARN,
                name=execution_name,
                input=json.dumps({
                    'batchId': batch_id,
                    'applicationId': application_id,
                    'market': batch_docs[0]['market'],
                    'documents': [{
                        'documentId': d['documentId'],
                        'documentType': d['documentType'],
                        'storageKey': d['storageKey']
                    } for d in batch_docs]
                })
            )
        except sfn.exceptions.ExecutionAlreadyExists:
            pass  # Idempotent - already started
    
    return {'statusCode': 200}
`

### 16.4 Reviewer UI (Document Review Portal)

| Attribute | Specification |
|-----------|--------------|
| Framework | React 18 + Next.js 14, hosted on AWS Amplify |
| Auth | Amazon Cognito (groups: document-reviewer, credit-assessor) |
| Real-time | AppSync subscriptions for live status updates |
| Image viewer | S3 presigned URLs for document display |
| Confidence display | Colour-coded: green (85%+), amber (70-84%), red (<70%) |

**Key Pages:**
- /queue - Work queue (DynamoDB query, filterable)
- /review/:applicationId - All documents for an application
- /review/:applicationId/:documentId - Side-by-side review
- /decision/:applicationId - Credit assessor approval page

**API Gateway Endpoints (Lambda-backed):**

| Endpoint | Method | Lambda | Purpose |
|----------|--------|--------|---------|
| /review/queue | GET | get-review-queue | Fetch pending review items |
| /review/{appId}/{docId} | GET | get-document-review | Get extraction + presigned image URL |
| /review/{appId}/{docId}/correct | POST | submit-corrections | Save corrections + resume workflow |
| /decision/{appId} | POST | submit-decision | Record assessor decision + resume |
| /audit/{appId} | GET | get-audit-trail | Full audit log for application |

**Lambda: Submit Corrections and Resume Workflow:**

`python
import boto3, json

sfn = boto3.client('stepfunctions')
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    body = json.loads(event['body'])
    user_id = event['requestContext']['authorizer']['claims']['sub']
    app_id = event['pathParameters']['applicationId']
    doc_id = event['pathParameters']['documentId']
    
    # Save corrections to DynamoDB
    corrections_table = dynamodb.Table('ipf-poc-corrections')
    for correction in body['corrections']:
        corrections_table.put_item(Item={
            'documentId': doc_id,
            'fieldName': correction['field_name'],
            'originalValue': correction['original_value'],
            'correctedValue': correction['corrected_value'],
            'correctedBy': user_id,
            'correctedAt': datetime.utcnow().isoformat()
        })
    
    # Resume Step Functions (send task token)
    task_token = body['task_token']
    sfn.send_task_success(
        taskToken=task_token,
        output=json.dumps({
            'corrections': body['corrections'],
            'corrected_by': user_id,
            'action': 'CORRECTIONS_SUBMITTED'
        })
    )
    
    # Audit log
    audit_table = dynamodb.Table('ipf-poc-audit')
    audit_table.put_item(Item={
        'applicationId': app_id,
        'timestamp': datetime.utcnow().isoformat(),
        'action': 'FIELD_CORRECTION',
        'userId': user_id,
        'documentId': doc_id,
        'details': json.dumps(body['corrections'])
    })
    
    return {'statusCode': 200, 'body': json.dumps({'status': 'corrections_applied'})}
`

### 16.5 Cognito User Pool Configuration

| Group | Portal Access | Permissions |
|-------|--------------|-------------|
| back-office-admin | Admin UI (Amplify app 1) | Upload documents, view history |
| document-reviewer | Reviewer UI (Amplify app 2) | View queue, review, correct fields |
| credit-assessor | Reviewer UI (Amplify app 2) | All reviewer + approve/decline |
| operations | Both (read-only) | View audit trails, dashboards |

### 16.6 Updated CDK Stack (with UI infrastructure)

`	ypescript
// Additional CDK constructs for UI
const adminApp = new amplify.App(this, 'AdminUI', {
  sourceCodeProvider: new amplify.GitHubSourceCodeProvider({...}),
});

const reviewerApp = new amplify.App(this, 'ReviewerUI', {
  sourceCodeProvider: new amplify.GitHubSourceCodeProvider({...}),
});

// Cognito
const userPool = new cognito.UserPool(this, 'IPFPoCPool', {
  selfSignUpEnabled: false,
  signInAliases: { email: true },
});

const adminGroup = new cognito.CfnUserPoolGroup(this, 'AdminGroup', {
  userPoolId: userPool.userPoolId,
  groupName: 'back-office-admin',
});

const reviewerGroup = new cognito.CfnUserPoolGroup(this, 'ReviewerGroup', {
  userPoolId: userPool.userPoolId,
  groupName: 'document-reviewer',
});

const assessorGroup = new cognito.CfnUserPoolGroup(this, 'AssessorGroup', {
  userPoolId: userPool.userPoolId,
  groupName: 'credit-assessor',
});

// S3 event -> EventBridge -> Lambda -> Step Functions
const docBucket = new s3.Bucket(this, 'DocBucket', {
  eventBridgeEnabled: true,
  versioned: true,
  encryption: s3.BucketEncryption.KMS,
});

new events.Rule(this, 'DocUploadRule', {
  eventPattern: {
    source: ['aws.s3'],
    detailType: ['Object Created'],
    detail: { bucket: { name: [docBucket.bucketName] } },
  },
  targets: [new targets.LambdaFunction(startWorkflowFn)],
});
`

### 16.7 Updated PoC Timeline (with UI)

| Week | Deliverable |
|------|-------------|
| 1-2 | CDK stack: S3, DynamoDB, Cognito, API Gateway, Amplify scaffolds |
| 3-4 | Document Agent: Textract + Bedrock extraction pipeline |
| 5-6 | Step Functions state machine + EventBridge trigger + policy gate |
| 7-8 | Admin UI: upload portal (Amplify + S3 presigned uploads) |
| 9-10 | Reviewer UI: queue, document viewer, field editor, decision page |
| 11-12 | Integration: event flow end-to-end, human-in-the-loop via task tokens |
| 13-14 | Accuracy testing on 200 docs, performance testing, exit criteria |

Note: Timeline extends from 12 to 14 weeks to accommodate the two UI applications.

### 16.8 Updated Cost Estimate (with UI)

| Component | Monthly Cost (GBP) |
|-----------|-------------------|
| Previous total (Section 13) | 230-555 |
| Amplify Hosting (2 apps) | 10-25 |
| Cognito (user pool, <100 users) | 0-5 |
| API Gateway (additional endpoints) | 5-10 |
| Additional Lambda (UI handlers) | 5-15 |
| AppSync (real-time subscriptions) | 10-20 |
| **Updated total** | **260-630** |
