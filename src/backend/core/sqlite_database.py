"""
IPF IPA PoC - SQLite Database (Local Fallback)
Drop-in replacement for Supabase when offline or Supabase is unavailable.
Same interface as database.py - just swap the import.

Storage: local filesystem (data/documents/)
Database: SQLite (data/ipf_poc.db)
"""
import sqlite3
import os
import json
import shutil
from datetime import datetime
from uuid import uuid4
from typing import Optional
from pathlib import Path

# Data directories
BASE_DIR = Path(__file__).parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "ipf_poc.db"
DOCS_DIR = DATA_DIR / "documents"

DATA_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)


def get_conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            batch_id TEXT NOT NULL,
            application_id TEXT NOT NULL,
            document_type TEXT NOT NULL,
            sub_type TEXT,
            market TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            original_filename TEXT,
            uploaded_by TEXT NOT NULL,
            uploaded_at TEXT DEFAULT (datetime('now')),
            status TEXT DEFAULT 'UPLOADED'
        );

        CREATE TABLE IF NOT EXISTS extractions (
            id TEXT PRIMARY KEY,
            document_id TEXT,
            field_name TEXT NOT NULL,
            extracted_value TEXT,
            confidence INTEGER,
            validation_status TEXT DEFAULT 'PENDING',
            validation_reason TEXT,
            corrected_value TEXT,
            corrected_by TEXT,
            corrected_at TEXT,
            extracted_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS workflow_state (
            id TEXT PRIMARY KEY,
            batch_id TEXT NOT NULL UNIQUE,
            application_id TEXT NOT NULL,
            market TEXT NOT NULL,
            status TEXT DEFAULT 'PROCESSING',
            recommendation TEXT,
            recommendation_data TEXT,
            started_at TEXT DEFAULT (datetime('now')),
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS decisions (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            assessor_id TEXT NOT NULL,
            ai_recommendation TEXT,
            reason_codes TEXT,
            decided_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            id TEXT PRIMARY KEY,
            application_id TEXT,
            document_id TEXT,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            details TEXT DEFAULT '{}',
            timestamp TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_docs_app ON documents(application_id);
        CREATE INDEX IF NOT EXISTS idx_docs_batch ON documents(batch_id);
        CREATE INDEX IF NOT EXISTS idx_docs_status ON documents(status);
        CREATE INDEX IF NOT EXISTS idx_ext_doc ON extractions(document_id);
        CREATE INDEX IF NOT EXISTS idx_wf_batch ON workflow_state(batch_id);
        CREATE INDEX IF NOT EXISTS idx_audit_app ON audit_log(application_id);

        CREATE TABLE IF NOT EXISTS loan_applications (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL UNIQUE,
            market TEXT NOT NULL,
            document_id TEXT,
            extracted_fields TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            status TEXT DEFAULT 'EXTRACTED'
        );

        CREATE TABLE IF NOT EXISTS discrepancies (
            id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            field_pair TEXT NOT NULL,
            label TEXT,
            severity TEXT,
            severity_icon TEXT,
            declared_value TEXT,
            extracted_value TEXT,
            source_document_id TEXT,
            source_document_type TEXT,
            status TEXT,
            similarity_pct INTEGER,
            detail TEXT,
            override_explanation TEXT,
            override_by TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_loan_app ON loan_applications(application_id);
        CREATE INDEX IF NOT EXISTS idx_discrepancy_app ON discrepancies(application_id);
    """)
    conn.commit()
    conn.close()


def row_to_dict(row) -> dict:
    if row is None:
        return None
    return dict(row)


class SQLiteDatabase:
    """Drop-in replacement for the Supabase Database class."""

    def __init__(self):
        init_db()

    # ---- Documents ----
    def create_document(self, batch_id, application_id, document_type, sub_type,
                        market, storage_path, original_filename, uploaded_by) -> dict:
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
        conn = get_conn()
        conn.execute("""INSERT INTO documents VALUES (
            :id,:batch_id,:application_id,:document_type,:sub_type,:market,
            :storage_path,:original_filename,:uploaded_by,:uploaded_at,:status)""", doc)
        conn.commit()
        conn.close()
        return doc

    def update_document_status(self, doc_id: str, status: str):
        conn = get_conn()
        conn.execute("UPDATE documents SET status=? WHERE id=?", (status, doc_id))
        conn.commit()
        conn.close()

    def get_documents_by_batch(self, batch_id: str) -> list:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM documents WHERE batch_id=?", (batch_id,)).fetchall()
        conn.close()
        return [row_to_dict(r) for r in rows]

    def get_documents_by_application(self, application_id: str) -> list:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM documents WHERE application_id=?", (application_id,)).fetchall()
        conn.close()
        return [row_to_dict(r) for r in rows]

    def get_review_queue(self, status: Optional[str] = None) -> list:
        conn = get_conn()
        if status:
            rows = conn.execute("SELECT * FROM documents WHERE status=? ORDER BY uploaded_at DESC", (status,)).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents WHERE status IN ('PENDING_REVIEW','EXTRACTED') ORDER BY uploaded_at DESC").fetchall()
        conn.close()
        return [row_to_dict(r) for r in rows]

    # ---- Extractions ----
    def save_extraction(self, document_id, field_name, extracted_value,
                        confidence, validation_status, validation_reason="") -> dict:
        record = {
            "id": str(uuid4()),
            "document_id": document_id,
            "field_name": field_name,
            "extracted_value": extracted_value,
            "confidence": confidence,
            "validation_status": validation_status,
            "validation_reason": validation_reason,
            "corrected_value": None,
            "corrected_by": None,
            "corrected_at": None,
            "extracted_at": datetime.utcnow().isoformat()
        }
        conn = get_conn()
        conn.execute("""INSERT INTO extractions VALUES (
            :id,:document_id,:field_name,:extracted_value,:confidence,
            :validation_status,:validation_reason,:corrected_value,
            :corrected_by,:corrected_at,:extracted_at)""", record)
        conn.commit()
        conn.close()
        return record

    def get_extractions(self, document_id: str) -> list:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM extractions WHERE document_id=?", (document_id,)).fetchall()
        conn.close()
        return [row_to_dict(r) for r in rows]

    def update_extraction_correction(self, extraction_id, corrected_value, corrected_by):
        conn = get_conn()
        conn.execute("""UPDATE extractions SET corrected_value=?,corrected_by=?,corrected_at=?
                        WHERE id=?""",
                     (corrected_value, corrected_by, datetime.utcnow().isoformat(), extraction_id))
        conn.commit()
        conn.close()

    # ---- Workflow State ----
    def create_workflow(self, batch_id, application_id, market) -> dict:
        wf = {
            "id": str(uuid4()),
            "batch_id": batch_id,
            "application_id": application_id,
            "market": market,
            "status": "PROCESSING",
            "recommendation": None,
            "recommendation_data": None,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None
        }
        conn = get_conn()
        conn.execute("""INSERT INTO workflow_state VALUES (
            :id,:batch_id,:application_id,:market,:status,
            :recommendation,:recommendation_data,:started_at,:completed_at)""", wf)
        conn.commit()
        conn.close()
        return wf

    def update_workflow_status(self, batch_id, status, recommendation=None):
        conn = get_conn()
        if recommendation:
            conn.execute("""UPDATE workflow_state SET status=?,recommendation=?,completed_at=?
                            WHERE batch_id=?""",
                         (status, recommendation,
                          datetime.utcnow().isoformat() if status in ("VERIFIED","DECIDED") else None,
                          batch_id))
        else:
            conn.execute("UPDATE workflow_state SET status=? WHERE batch_id=?", (status, batch_id))
        conn.commit()
        conn.close()

    def get_workflow(self, batch_id) -> Optional[dict]:
        conn = get_conn()
        row = conn.execute("SELECT * FROM workflow_state WHERE batch_id=?", (batch_id,)).fetchone()
        conn.close()
        return row_to_dict(row)

    def get_all_workflows(self, limit=50) -> list:
        conn = get_conn()
        rows = conn.execute("SELECT * FROM workflow_state ORDER BY started_at DESC LIMIT ?", (limit,)).fetchall()
        conn.close()
        return [row_to_dict(r) for r in rows]

    # ---- Decisions ----
    def save_decision(self, application_id, decision, assessor_id,
                      ai_recommendation, reason_codes=None) -> dict:
        record = {
            "id": str(uuid4()),
            "application_id": application_id,
            "decision": decision,
            "assessor_id": assessor_id,
            "ai_recommendation": ai_recommendation,
            "reason_codes": json.dumps(reason_codes or []),
            "decided_at": datetime.utcnow().isoformat()
        }
        conn = get_conn()
        conn.execute("""INSERT INTO decisions VALUES (
            :id,:application_id,:decision,:assessor_id,
            :ai_recommendation,:reason_codes,:decided_at)""", record)
        conn.commit()
        conn.close()
        return record

    # ---- Audit ----
    def log_audit(self, application_id, action, actor,
                  document_id=None, details=None) -> dict:
        record = {
            "id": str(uuid4()),
            "application_id": application_id,
            "document_id": document_id,
            "action": action,
            "actor": actor,
            "details": json.dumps(details or {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        conn = get_conn()
        conn.execute("""INSERT INTO audit_log VALUES (
            :id,:application_id,:document_id,:action,:actor,:details,:timestamp)""", record)
        conn.commit()
        conn.close()
        return record

    def get_audit_trail(self, application_id) -> list:
        conn = get_conn()
        rows = conn.execute("""SELECT * FROM audit_log WHERE application_id=?
                               ORDER BY timestamp""", (application_id,)).fetchall()
        conn.close()
        result = []
        for r in rows:
            d = row_to_dict(r)
            try:
                d["details"] = json.loads(d.get("details") or "{}")
            except Exception:
                pass
            result.append(d)
        return result

    # ---- File Storage (local filesystem) ----
    def upload_file(self, file_bytes: bytes, storage_path: str, content_type: str):
        """Save file to local data/documents/ directory."""
        target = DOCS_DIR / storage_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "wb") as f:
            f.write(file_bytes)

    def get_file_url(self, storage_path: str) -> str:
        """Return local file path as a URL-like string."""
        target = DOCS_DIR / storage_path
        if target.exists():
            return target.as_uri()  # file:///path/to/file
        return ""

    def get_file_bytes(self, storage_path: str) -> Optional[bytes]:
        """Read local file bytes."""
        target = DOCS_DIR / storage_path
        if target.exists():
            with open(target, "rb") as f:
                return f.read()
        return None


    # ---- Loan Applications ----
    def save_loan_application(self, application_id, market, document_id, extracted_fields):
        import json, uuid as _uuid
        record = {"id": str(_uuid.uuid4()), "application_id": application_id,
                  "market": market, "document_id": document_id or "",
                  "extracted_fields": json.dumps(extracted_fields or {}, ensure_ascii=False),
                  "status": "EXTRACTED"}
        conn = get_conn()
        conn.execute("INSERT OR REPLACE INTO loan_applications (id,application_id,market,document_id,extracted_fields,status) VALUES (:id,:application_id,:market,:document_id,:extracted_fields,:status)", record)
        conn.commit(); conn.close()
        record["extracted_fields"] = extracted_fields
        return record

    def get_loan_application(self, application_id):
        import json
        conn = get_conn()
        row = conn.execute("SELECT * FROM loan_applications WHERE application_id=?", (application_id,)).fetchone()
        conn.close()
        if not row:
            return None
        d = row_to_dict(row)
        try:
            d["extracted_fields"] = json.loads(d["extracted_fields"])
        except Exception:
            pass
        return d

    def save_discrepancies(self, application_id, discrepancies):
        import uuid as _uuid
        conn = get_conn()
        conn.execute("DELETE FROM discrepancies WHERE application_id=?", (application_id,))
        records = []
        for disc in discrepancies:
            rec_id = str(_uuid.uuid4())
            conn.execute("INSERT INTO discrepancies (id,application_id,field_pair,label,severity,severity_icon,declared_value,extracted_value,source_document_id,source_document_type,status,similarity_pct,detail) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (rec_id, application_id, disc.get("field_pair",""), disc.get("label",""),
                 disc.get("severity",""), disc.get("severity_icon",""),
                 str(disc.get("declared_value") or ""), str(disc.get("extracted_value") or ""),
                 disc.get("source_document_id",""), disc.get("source_document_type",""),
                 disc.get("status",""), disc.get("similarity_pct",0), disc.get("detail","")))
            records.append({**disc, "id": rec_id})
        conn.commit(); conn.close()
        return records

    def get_discrepancies(self, application_id):
        conn = get_conn()
        rows = conn.execute("SELECT * FROM discrepancies WHERE application_id=? ORDER BY severity DESC", (application_id,)).fetchall()
        conn.close()
        return [row_to_dict(r) for r in rows]

    def update_discrepancy_override(self, discrepancy_id, explanation, override_by):
        conn = get_conn()
        conn.execute("UPDATE discrepancies SET override_explanation=?,override_by=?,status=? WHERE id=?",
                     (explanation, override_by, "REVIEWED", discrepancy_id))
        conn.commit(); conn.close()
