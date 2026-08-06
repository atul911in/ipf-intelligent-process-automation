export type WorkflowStatus = "PROCESSING" | "PENDING_REVIEW" | "PENDING_DECISION" | "DECIDED" | "FAILED" | "UNKNOWN";
export type DocumentStatus = "UPLOADED" | "PROCESSING" | "EXTRACTED" | "PENDING_REVIEW" | "VERIFIED" | "FAILED";
export type Market = "PL" | "RO" | "HU" | "CZ";

export interface DocumentItem {
  id: string;
  filename: string;
  type: string;
  status: DocumentStatus;
  application_id?: string;
  market?: string;
  uploaded_at?: string;
}

export interface AppStatus {
  application_id: string;
  batch_id: string;
  workflow_status: WorkflowStatus;
  documents: DocumentItem[];
  recommendation?: string;
}

export interface Extraction {
  id: string;
  field_name: string;
  extracted_value: string;
  corrected_value?: string;
  confidence: number;
  validation_status: "PASS" | "FAIL" | "WARNING" | "PENDING";
  validation_reason?: string;
}

export interface Discrepancy {
  id: string;
  label: string;
  status: "MATCH" | "MISMATCH" | "WARNING" | "UNVERIFIABLE";
  severity: string;
  declared_value: string;
  extracted_value: string;
  detail: string;
  source_document_type?: string;
  override_explanation?: string;
  override_by?: string;
}

export interface DiscrepancySummary {
  total: number;
  mismatches: number;
  warnings: number;
  matches: number;
  unverifiable: number;
  high_severity: number;
}

export interface CreditScore {
  score: number;
  score_pct: number;
  risk_band: string;
  risk_icon: string;
  recommendation: string;
  bureau_name: string;
  disclaimer: string;
  breakdown: Array<{
    category: string;
    score: number;
    max: number;
    pct: number;
    detail: string;
  }>;
  flags: string[];
}

export interface AuditEvent {
  id: string;
  application_id: string;
  action: string;
  actor: string;
  document_id?: string;
  timestamp: string;
  details?: Record<string, unknown>;
}

export interface LoanApplication {
  application_id: string;
  extracted_fields: Record<string, { value: string; confidence?: number } | string>;
}
