-- IPF IPA PoC - Supabase Database Schema
-- Run this in your Supabase SQL editor

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL,
    application_id TEXT NOT NULL,
    document_type TEXT NOT NULL,
    sub_type TEXT,
    market TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    original_filename TEXT,
    uploaded_by TEXT NOT NULL,
    uploaded_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'UPLOADED'
);

CREATE TABLE IF NOT EXISTS extractions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id),
    field_name TEXT NOT NULL,
    extracted_value TEXT,
    confidence INTEGER,
    validation_status TEXT DEFAULT 'PENDING',
    validation_reason TEXT,
    corrected_value TEXT,
    corrected_by TEXT,
    corrected_at TIMESTAMPTZ,
    extracted_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflow_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL UNIQUE,
    application_id TEXT NOT NULL,
    market TEXT NOT NULL,
    status TEXT DEFAULT 'PROCESSING',
    recommendation TEXT,
    recommendation_data JSONB,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    assessor_id TEXT NOT NULL,
    ai_recommendation TEXT,
    reason_codes TEXT[],
    decided_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id TEXT,
    document_id UUID,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    details JSONB DEFAULT '{}',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_application ON documents(application_id);
CREATE INDEX IF NOT EXISTS idx_documents_batch ON documents(batch_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_extractions_document ON extractions(document_id);
CREATE INDEX IF NOT EXISTS idx_workflow_batch ON workflow_state(batch_id);
CREATE INDEX IF NOT EXISTS idx_audit_application ON audit_log(application_id);
