"""
IPF IPA PoC - Supabase Database Client
Handles all persistence: documents, extractions, audit, decisions.
"""
from supabase import create_client, Client
from datetime import datetime
from uuid import uuid4
from typing import Optional
from .config import settings


def get_supabase() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


class Database:
    def __init__(self):
        self.client = get_supabase()

    # ---- Documents ----
    def create_document(self, batch_id: str, application_id: str,
                        document_type: str, sub_type: str, market: str,
                        storage_path: str, original_filename: str,
                        uploaded_by: str) -> dict:
        doc = {
            "id": str(uuid4()),
            "batch_id": batch_id,
            "application_id": application_id,
            "document_type": document_type,
            "sub_type": sub_type,
            "market": market,
            "storage_path": storage_path,
            "original_filename": original_filename,
            "uploaded_by": uploaded_by,
            "uploaded_at": datetime.utcnow().isoformat(),
            "status": "UPLOADED"
        }
        self.client.table("documents").insert(doc).execute()
        return doc

    def update_document_status(self, doc_id: str, status: str):
        self.client.table("documents").update(
            {"status": status}
        ).eq("id", doc_id).execute()

    def get_documents_by_batch(self, batch_id: str) -> list:
        res = self.client.table("documents").select("*").eq("batch_id", batch_id).execute()
        return res.data

    def get_documents_by_application(self, application_id: str) -> list:
        res = self.client.table("documents").select("*").eq("application_id", application_id).execute()
        return res.data

    def get_review_queue(self, status: Optional[str] = None) -> list:
        query = self.client.table("documents").select("*")
        if status:
            query = query.eq("status", status)
        else:
            query = query.in_("status", ["PENDING_REVIEW", "EXTRACTED"])
        res = query.order("uploaded_at", desc=True).execute()
        return res.data

    # ---- Extractions ----
    def save_extraction(self, document_id: str, field_name: str,
                        extracted_value: str, confidence: int,
                        validation_status: str, validation_reason: str = ""):
        record = {
            "id": str(uuid4()),
            "document_id": document_id,
            "field_name": field_name,
            "extracted_value": extracted_value,
            "confidence": confidence,
            "validation_status": validation_status,
            "validation_reason": validation_reason,
            "extracted_at": datetime.utcnow().isoformat()
        }
        self.client.table("extractions").insert(record).execute()
        return record

    def get_extractions(self, document_id: str) -> list:
        res = self.client.table("extractions").select("*").eq("document_id", document_id).execute()
        return res.data

    def update_extraction_correction(self, extraction_id: str, corrected_value: str, corrected_by: str):
        self.client.table("extractions").update({
            "corrected_value": corrected_value,
            "corrected_by": corrected_by,
            "corrected_at": datetime.utcnow().isoformat()
        }).eq("id", extraction_id).execute()

    # ---- Workflow State ----
    def create_workflow(self, batch_id: str, application_id: str, market: str) -> dict:
        wf = {
            "id": str(uuid4()),
            "batch_id": batch_id,
            "application_id": application_id,
            "market": market,
            "status": "PROCESSING",
            "started_at": datetime.utcnow().isoformat()
        }
        self.client.table("workflow_state").insert(wf).execute()
        return wf

    def update_workflow_status(self, batch_id: str, status: str, recommendation: str = None):
        update = {"status": status}
        if recommendation:
            update["recommendation"] = recommendation
        if status in ("VERIFIED", "DECIDED"):
            update["completed_at"] = datetime.utcnow().isoformat()
        self.client.table("workflow_state").update(update).eq("batch_id", batch_id).execute()

    def get_workflow(self, batch_id: str) -> Optional[dict]:
        res = self.client.table("workflow_state").select("*").eq("batch_id", batch_id).execute()
        return res.data[0] if res.data else None

    # ---- Decisions ----
    def save_decision(self, application_id: str, decision: str,
                      assessor_id: str, ai_recommendation: str, reason_codes: list = None):
        record = {
            "id": str(uuid4()),
            "application_id": application_id,
            "decision": decision,
            "assessor_id": assessor_id,
            "ai_recommendation": ai_recommendation,
            "reason_codes": reason_codes or [],
            "decided_at": datetime.utcnow().isoformat()
        }
        self.client.table("decisions").insert(record).execute()
        return record

    # ---- Audit ----
    def log_audit(self, application_id: str, action: str, actor: str,
                  document_id: str = None, details: dict = None):
        record = {
            "id": str(uuid4()),
            "application_id": application_id,
            "document_id": document_id,
            "action": action,
            "actor": actor,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        self.client.table("audit_log").insert(record).execute()
        return record

    # ---- Storage ----
    def upload_file(self, file_bytes: bytes, storage_path: str, content_type: str):
        self.client.storage.from_(settings.SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type}
        )

    def get_file_url(self, storage_path: str) -> str:
        return self.client.storage.from_(settings.SUPABASE_BUCKET).get_public_url(storage_path)
