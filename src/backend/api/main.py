"""
IPF IPA PoC - FastAPI Backend
Main API server exposing endpoints for Admin UI and Reviewer UI.
"""
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from uuid import uuid4
import threading

from ..core.db_factory import get_database
from ..core.config import settings
from ..agents.orchestrator import orchestrator, WorkflowState

app = FastAPI(title="IPF IPA PoC API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CorrectionRequest(BaseModel):
    extraction_id: str
    corrected_value: str
    corrected_by: str


class DecisionRequest(BaseModel):
    decision: str
    assessor_id: str
    reason_codes: list[str] = []


@app.post("/api/upload")
async def upload_documents(
    application_id: str = Form(...),
    market: str = Form(...),
    document_types: str = Form(...),
    uploaded_by: str = Form(default="admin"),
    files: list[UploadFile] = File(...)
):
    db = get_database()
    if len(files) > settings.MAX_BATCH_FILES:
        raise HTTPException(400, f"Max {settings.MAX_BATCH_FILES} files per batch")

    batch_id = str(uuid4())
    doc_types = document_types.split(",")
    doc_ids = []

    for i, file in enumerate(files):
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
            raise HTTPException(400, f"File {file.filename} exceeds {settings.MAX_UPLOAD_SIZE_MB}MB")
        doc_type = doc_types[i].strip() if i < len(doc_types) else "unknown"
        storage_path = f"{application_id}/{batch_id}/{file.filename}"
        db.upload_file(content, storage_path, file.content_type or "application/octet-stream")
        doc = db.create_document(
            batch_id=batch_id,
            application_id=application_id,
            document_type=doc_type,
            sub_type=doc_type,
            market=market,
            storage_path=storage_path,
            original_filename=file.filename,
            uploaded_by=uploaded_by
        )
        doc_ids.append(doc["id"])

    db.log_audit(application_id, "UPLOAD", uploaded_by,
                 details={"batch_id": batch_id, "file_count": len(files)})
    db.create_workflow(batch_id, application_id, market)

    threading.Thread(
        target=run_workflow,
        args=(batch_id, application_id, market, doc_ids),
        daemon=True
    ).start()

    return {
        "batch_id": batch_id,
        "application_id": application_id,
        "document_ids": doc_ids,
        "status": "PROCESSING",
        "message": f"{len(files)} documents uploaded and processing started"
    }


def run_workflow(batch_id, application_id, market, doc_ids):
    db = get_database()
    try:
        initial_state: WorkflowState = {
            "batch_id": batch_id,
            "application_id": application_id,
            "market": market,
            "document_ids": doc_ids,
            "current_doc_index": 0,
            "extractions": [],
            "validations": [],
            "fields_needing_review": [],
            "recommendation": None,
            "status": "PROCESSING",
            "error": None
        }
        orchestrator.invoke(initial_state)
    except Exception as e:
        import traceback, logging
        logging.error(f"WORKFLOW ERROR for {batch_id}: {traceback.format_exc()}")
        db.update_workflow_status(batch_id, "FAILED")
        db.log_audit(application_id, "WORKFLOW_FAILED", "orchestrator",
                     details={"error": str(e), "traceback": traceback.format_exc()})


@app.get("/api/status/{application_id}")
async def get_status(application_id: str):
    db = get_database()
    docs = db.get_documents_by_application(application_id)
    if not docs:
        raise HTTPException(404, "Application not found")
    batch_id = docs[0]["batch_id"]
    workflow = db.get_workflow(batch_id)
    return {
        "application_id": application_id,
        "batch_id": batch_id,
        "workflow_status": workflow["status"] if workflow else "UNKNOWN",
        "documents": [{"id": d["id"], "filename": d["original_filename"],
                       "type": d["document_type"], "status": d["status"]} for d in docs],
        "recommendation": workflow.get("recommendation") if workflow else None
    }


@app.get("/api/upload/history")
async def upload_history():
    db = get_database()
    try:
        res = db.client.table("workflow_state").select("*").order("started_at", desc=True).limit(50).execute()
        return {"uploads": res.data}
    except AttributeError:
        return {"uploads": db.get_all_workflows(limit=50)}


@app.get("/api/queue")
async def get_review_queue(status: Optional[str] = None):
    db = get_database()
    docs = db.get_review_queue(status)
    return {"items": docs, "total": len(docs)}


@app.get("/api/review/{document_id}")
async def get_document_review(document_id: str):
    db = get_database()
    extractions = db.get_extractions(document_id)

    # Get document info
    doc = None
    try:
        res = db.client.table("documents").select("*").eq("id", document_id).execute()
        doc = res.data[0] if res.data else None
    except AttributeError:
        # SQLite
        conn = db.get_conn() if hasattr(db, 'get_conn') else None
        if conn:
            import sqlite3
            row = conn.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
            if row:
                doc = dict(row)
            conn.close()

    if not doc:
        # Try alternate approach for SQLite
        from ..core.sqlite_database import get_conn, row_to_dict
        try:
            conn = get_conn()
            row = conn.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
            doc = row_to_dict(row)
            conn.close()
        except Exception:
            pass

    if not extractions and not doc:
        raise HTTPException(404, "Document not found")

    # Get image as base64 for Streamlit display
    image_b64 = None
    content_type = "image/jpeg"
    if doc:
        try:
            file_bytes = db.get_file_bytes(doc["storage_path"]) if hasattr(db, "get_file_bytes") else None
            if file_bytes:
                import base64
                image_b64 = base64.b64encode(file_bytes).decode("utf-8")
                fname = doc.get("original_filename", "").lower()
                content_type = "application/pdf" if fname.endswith(".pdf") else "image/jpeg"
        except Exception:
            pass

    return {
        "document_id": document_id,
        "document_type": doc["document_type"] if doc else "unknown",
        "market": doc["market"] if doc else "unknown",
        "original_filename": doc["original_filename"] if doc else "",
        "image_b64": image_b64,
        "content_type": content_type,
        "status": doc["status"] if doc else "unknown",
        "extractions": extractions
    }


@app.post("/api/review/{document_id}/correct")
async def submit_corrections(document_id: str, corrections: list[CorrectionRequest]):
    db = get_database()
    for c in corrections:
        db.update_extraction_correction(c.extraction_id, c.corrected_value, c.corrected_by)
    db.update_document_status(document_id, "VERIFIED")

    # Get app_id for audit
    app_id = ""
    try:
        from ..core.sqlite_database import get_conn, row_to_dict
        conn = get_conn()
        row = conn.execute("SELECT application_id FROM documents WHERE id=?", (document_id,)).fetchone()
        if row:
            app_id = row[0]
        conn.close()
    except Exception:
        pass

    db.log_audit(app_id, "CORRECT",
                 corrections[0].corrected_by if corrections else "reviewer",
                 document_id=document_id,
                 details={"corrections_count": len(corrections)})
    return {"status": "corrections_applied", "document_id": document_id}


@app.post("/api/review/{document_id}/confirm")
async def confirm_document(document_id: str, reviewer_id: str = "reviewer"):
    db = get_database()
    db.update_document_status(document_id, "VERIFIED")

    app_id = ""
    try:
        from ..core.sqlite_database import get_conn
        conn = get_conn()
        row = conn.execute("SELECT application_id FROM documents WHERE id=?", (document_id,)).fetchone()
        if row:
            app_id = row[0]
        conn.close()
    except Exception:
        pass

    db.log_audit(app_id, "CONFIRM", reviewer_id, document_id=document_id)
    return {"status": "confirmed", "document_id": document_id}


@app.post("/api/decision/{application_id}")
async def submit_decision(application_id: str, request: DecisionRequest):
    db = get_database()
    docs = db.get_documents_by_application(application_id)
    if not docs:
        raise HTTPException(404, "Application not found")

    batch_id = docs[0]["batch_id"]
    workflow = db.get_workflow(batch_id)
    db.save_decision(
        application_id=application_id,
        decision=request.decision,
        assessor_id=request.assessor_id,
        ai_recommendation=workflow.get("recommendation", "UNKNOWN") if workflow else "UNKNOWN",
        reason_codes=request.reason_codes
    )
    db.update_workflow_status(batch_id, "DECIDED")
    db.log_audit(application_id, request.decision, request.assessor_id,
                 details={"reason_codes": request.reason_codes})
    return {
        "status": "decision_recorded",
        "application_id": application_id,
        "decision": request.decision,
        "assessor_id": request.assessor_id
    }


@app.get("/api/audit/{application_id}")
async def get_audit_trail(application_id: str):
    db = get_database()
    try:
        res = db.client.table("audit_log").select("*").eq(
            "application_id", application_id).order("timestamp").execute()
        return {"audit_trail": res.data}
    except AttributeError:
        return {"audit_trail": db.get_audit_trail(application_id)}




@app.get("/api/document/{document_id}/preview")
async def get_document_preview(document_id: str):
    """Return PDF first page as PNG image for inline display."""
    db = get_database()
    # Get doc info
    try:
        from ..core.sqlite_database import get_conn, row_to_dict
        conn = get_conn()
        row = conn.execute("SELECT * FROM documents WHERE id=?", (document_id,)).fetchone()
        doc = row_to_dict(row)
        conn.close()
    except Exception:
        doc = None

    if not doc:
        raise HTTPException(404, "Document not found")

    file_bytes = db.get_file_bytes(doc["storage_path"]) if hasattr(db, "get_file_bytes") else None
    if not file_bytes:
        raise HTTPException(404, "File not found")

    fname = doc.get("original_filename", "")
    if fname.lower().endswith(".pdf"):
        # Convert PDF first page to PNG using pypdf + Pillow
        try:
            from pypdf import PdfReader
            from PIL import Image as PILImage
            import io as _io
            # Extract text-based PDF page as image using pdf2image if available
            try:
                from pdf2image import convert_from_bytes
                images = convert_from_bytes(file_bytes, dpi=150, first_page=1, last_page=1)
                if images:
                    buf = _io.BytesIO()
                    images[0].save(buf, format="PNG")
                    from fastapi.responses import Response
                    return Response(content=buf.getvalue(), media_type="image/png")
            except Exception:
                pass

            # Fallback: render PDF text content onto a white image using Pillow
            from pypdf import PdfReader
            from PIL import Image as PILImage, ImageDraw, ImageFont
            reader = PdfReader(_io.BytesIO(file_bytes))
            page = reader.pages[0]
            text = page.extract_text() or ""

            img = PILImage.new("RGB", (620, 820), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            try:
                font_bold = ImageFont.truetype("arial.ttf", 14)
                font_reg = ImageFont.truetype("arial.ttf", 12)
            except Exception:
                font_bold = ImageFont.load_default()
                font_reg = font_bold

            # Header bar
            draw.rectangle([0, 0, 620, 44], fill=(30, 80, 220))
            draw.text((10, 12), f"Document: {fname}", fill=(255, 255, 255), font=font_bold)

            # Content
            y = 58
            for line in text.split("\n")[:45]:
                line = line.strip()
                if not line:
                    y += 8
                    continue
                if ":" in line:
                    parts = line.split(":", 1)
                    draw.text((14, y), parts[0] + ":", fill=(30, 80, 220), font=font_bold)
                    draw.text((14 + len(parts[0]) * 8, y), parts[1], fill=(40, 40, 40), font=font_reg)
                else:
                    draw.text((14, y), line, fill=(60, 60, 60), font=font_reg)
                y += 22
                if y > 790:
                    break

            draw.rectangle([0, 800, 620, 820], fill=(220, 230, 255))
            draw.text((10, 804), "IPF IPA PoC - Document Preview", fill=(30, 80, 220), font=font_reg)

            buf = _io.BytesIO()
            img.save(buf, format="PNG")
            from fastapi.responses import Response
            return Response(content=buf.getvalue(), media_type="image/png")
        except Exception as e:
            raise HTTPException(500, f"Could not render PDF: {e}")
    else:
        # For image files: return as-is
        import base64 as _b64
        img_bytes = _b64.b64decode(content) if isinstance(file_bytes, str) else file_bytes
        from fastapi.responses import Response
        mt = "image/jpeg" if fname.lower().endswith((".jpg", ".jpeg")) else "image/png"
        return Response(content=img_bytes, media_type=mt)



@app.get("/api/credit-score/{application_id}")
async def get_credit_score(application_id: str):
    """Compute mock credit score for an application based on extracted documents."""
    from ..agents.credit_score_agent import compute_credit_score
    db = get_database()

    docs = db.get_documents_by_application(application_id)
    if not docs:
        raise HTTPException(404, "Application not found")

    market = docs[0].get("market", "PL")

    # Gather all extractions and validations
    all_extractions = []
    all_validations = []
    for doc in docs:
        exts = db.get_extractions(doc["id"])
        all_extractions.extend(exts)
        for ext in exts:
            if ext.get("validation_status"):
                all_validations.append({
                    "field_name": ext["field_name"],
                    "validation": {
                        "status": ext["validation_status"],
                        "reason": ext.get("validation_reason", "")
                    }
                })

    result = compute_credit_score(
        extractions=all_extractions,
        validations=all_validations,
        market=market
    )
    return result



@app.get("/api/loan-application/{application_id}")
async def get_loan_application(application_id: str):
    """Get extracted loan application declared fields."""
    db = get_database()
    loan_app = db.get_loan_application(application_id)
    if not loan_app:
        raise HTTPException(404, "Loan application data not found. Ensure loan_application document was uploaded.")
    return loan_app


@app.get("/api/discrepancies/{application_id}")
async def get_discrepancies(application_id: str):
    """Get cross-reference discrepancy report for an application."""
    db = get_database()
    discrepancies = db.get_discrepancies(application_id)
    summary = {
        "total": len(discrepancies),
        "mismatches": sum(1 for d in discrepancies if d.get("status") == "MISMATCH"),
        "warnings": sum(1 for d in discrepancies if d.get("status") == "WARNING"),
        "matches": sum(1 for d in discrepancies if d.get("status") == "MATCH"),
        "unverifiable": sum(1 for d in discrepancies if d.get("status") == "UNVERIFIABLE"),
        "high_severity": sum(1 for d in discrepancies if d.get("status") == "MISMATCH" and d.get("severity") == "HIGH"),
    }
    return {"summary": summary, "discrepancies": discrepancies}


class DiscrepancyOverride(BaseModel):
    discrepancy_id: str
    explanation: str
    override_by: str


@app.post("/api/discrepancies/{application_id}/override")
async def override_discrepancy(application_id: str, request: DiscrepancyOverride):
    """Reviewer overrides a discrepancy with an explanation."""
    db = get_database()
    db.update_discrepancy_override(request.discrepancy_id, request.explanation, request.override_by)
    db.log_audit(application_id, "DISCREPANCY_OVERRIDE", request.override_by,
                 details={"discrepancy_id": request.discrepancy_id, "explanation": request.explanation})
    return {"status": "overridden", "discrepancy_id": request.discrepancy_id}


@app.get("/api/health")
async def health():
    from ..agents.ocr_utils import get_ocr_status
    db = get_database()
    return {
        "status": "healthy",
        "service": "ipf-ipa-poc",
        "db_mode": type(db).__name__,
        "ocr": get_ocr_status()
    }


