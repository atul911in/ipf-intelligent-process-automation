"""
IPF IPA PoC - LangGraph Orchestrator
All db and agent access is lazy (via get_db() and get_doc_agent())
to avoid import-time errors when OpenAI key is not yet loaded.
"""
from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, Annotated
from operator import add
import os

from .document_agent import DocumentAgent
from .loan_application_agent import LoanApplicationAgent
from .cross_reference_agent import run_cross_reference
from .validator import validate_field
from .ocr_utils import extract_text
from ..core.db_factory import get_database
from ..core.config import settings

# PostgresSaver optional
try:
    from langgraph.checkpoint.postgres import PostgresSaver
    POSTGRES_CHECKPOINTER_AVAILABLE = True
except ImportError:
    POSTGRES_CHECKPOINTER_AVAILABLE = False

# Lazy singletons
_doc_agent = None
_db = None


def get_doc_agent():
    global _doc_agent
    if _doc_agent is None:
        _doc_agent = DocumentAgent()
    return _doc_agent

_loan_agent = None

def get_loan_agent():
    global _loan_agent
    if _loan_agent is None:
        _loan_agent = LoanApplicationAgent()
    return _loan_agent


def get_db():
    global _db
    if _db is None:
        _db = get_database()
    return _db


class WorkflowState(TypedDict):
    batch_id: str
    application_id: str
    market: str
    document_ids: list[str]
    current_doc_index: int
    extractions: Annotated[list, add]
    validations: Annotated[list, add]
    fields_needing_review: list[dict]
    loan_app_data: Optional[dict]
    discrepancies: Optional[list]
    recommendation: Optional[dict]
    status: str
    error: Optional[str]


def extract_document(state: WorkflowState) -> dict:
    """Extract fields from the current document using OCR + LLM."""
    _db = get_db()
    _agent = get_doc_agent()
    doc_index = state.get("current_doc_index", 0)
    doc_ids = state["document_ids"]

    if doc_index >= len(doc_ids):
        return {"status": "ALL_EXTRACTED", "current_doc_index": doc_index}

    doc_id = doc_ids[doc_index]
    docs = _db.get_documents_by_batch(state["batch_id"])
    doc = next((d for d in docs if d["id"] == doc_id), None)
    if not doc:
        return {"error": f"Document {doc_id} not found", "status": "FAILED",
                "current_doc_index": doc_index + 1}

    # Extract text via OCR pipeline (pypdf for text PDFs, Tesseract for images)
    ocr_text = ""
    try:
        if hasattr(_db, "get_file_bytes"):
            file_bytes = _db.get_file_bytes(doc["storage_path"])
            if file_bytes:
                fname = doc.get("original_filename", "")
                ctype = "application/pdf" if fname.lower().endswith(".pdf") else "image/jpeg"
                ocr_text, _ = extract_text(file_bytes, ctype)
    except Exception:
        pass

    extraction_input = (ocr_text.strip() if (ocr_text and len(ocr_text.strip()) > 20)
                        else f"Document type: {doc['document_type']}, Market: {state['market']}")

    extraction_results = _agent.extract_fields(
        ocr_text=extraction_input,
        document_type=doc["document_type"],
        market=state["market"]
    )

    for field in extraction_results:
        _db.save_extraction(
            document_id=doc_id,
            field_name=field["field_name"],
            extracted_value=str(field.get("value", "") or ""),
            confidence=field.get("confidence", 0),
            validation_status="PENDING",
            validation_reason=""
        )

    _db.update_document_status(doc_id, "EXTRACTED")
    _db.log_audit(
        application_id=state["application_id"],
        action="EXTRACT", actor="document_agent",
        document_id=doc_id,
        details={"fields_extracted": len(extraction_results), "ocr_used": bool(ocr_text)}
    )

    return {"extractions": [{"document_id": doc_id, "fields": extraction_results}],
            "current_doc_index": doc_index + 1}


def validate_extractions(state: WorkflowState) -> dict:
    """Validate all extracted fields against market rules."""
    _db = get_db()
    all_validations = []
    fields_needing_review = []

    for extraction in state.get("extractions", []):
        doc_id = extraction["document_id"]
        for field in extraction["fields"]:
            result = validate_field(
                field_name=field["field_name"],
                value=field.get("value"),
                market=state["market"]
            )
            validation = {
                "document_id": doc_id,
                "field_name": field["field_name"],
                "value": field.get("value"),
                "confidence": field.get("confidence", 0),
                "validation": result
            }
            all_validations.append(validation)
            if (field.get("confidence", 0) < settings.CONFIDENCE_THRESHOLD
                    or result["status"] == "FAIL"):
                fields_needing_review.append(validation)

    for doc_id in state["document_ids"]:
        doc_validations = [v for v in all_validations if v["document_id"] == doc_id]
        needs_review = any(
            v["validation"]["status"] == "FAIL"
            or v["confidence"] < settings.CONFIDENCE_THRESHOLD
            for v in doc_validations
        )
        _db.update_document_status(doc_id, "PENDING_REVIEW" if needs_review else "VERIFIED")

    return {"validations": all_validations, "fields_needing_review": fields_needing_review}


def check_review_needed(state: WorkflowState) -> str:
    return "needs_review" if state.get("fields_needing_review") else "all_clear"

def check_review_needed_after_cross_ref(state: WorkflowState) -> str:
    """After cross-reference, route to review if there are mismatches or field issues."""
    has_field_issues = bool(state.get("fields_needing_review"))
    discrepancies = state.get("discrepancies") or []
    has_high_mismatches = any(d.get("status") == "MISMATCH" and d.get("severity") == "HIGH" for d in discrepancies)
    if has_field_issues or has_high_mismatches:
        return "needs_review"
    return "all_clear"


def generate_recommendation(state: WorkflowState) -> dict:
    """Generate AI recommendation. Human always makes final decision."""
    _db = get_db()
    _agent = get_doc_agent()
    recommendation = _agent.generate_recommendation(
        application_id=state["application_id"],
        all_extractions=state.get("extractions", []),
        all_validations=state.get("validations", [])
    )
    _db.update_workflow_status(
        batch_id=state["batch_id"],
        status="PENDING_DECISION",
        recommendation=recommendation.get("recommendation", "REFER")
    )
    _db.log_audit(
        application_id=state["application_id"],
        action="RECOMMEND", actor="document_agent",
        details=recommendation
    )
    return {"recommendation": recommendation, "status": "PENDING_DECISION"}


def pause_for_review(state: WorkflowState) -> dict:
    """Pause workflow — human review required."""
    _db = get_db()
    _db.update_workflow_status(state["batch_id"], "PENDING_REVIEW")
    _db.log_audit(
        application_id=state["application_id"],
        action="PAUSE_FOR_REVIEW", actor="orchestrator",
        details={"fields_count": len(state.get("fields_needing_review", []))}
    )
    return {"status": "PENDING_REVIEW"}


def extract_loan_application_step(state: WorkflowState) -> dict:
    """Extract fields from the loan application document if present."""
    dbase = get_db()
    docs = dbase.get_documents_by_batch(state["batch_id"])
    loan_app_doc = next((d for d in docs if d["document_type"] == "loan_application"), None)
    if not loan_app_doc:
        return {"loan_app_data": None}

    agent = get_loan_agent()
    ocr_text = ""
    try:
        if hasattr(dbase, "get_file_bytes"):
            file_bytes = dbase.get_file_bytes(loan_app_doc["storage_path"])
            if file_bytes:
                ctype = "application/pdf" if loan_app_doc["original_filename"].lower().endswith(".pdf") else "image/jpeg"
                ocr_text, _ = extract_text(file_bytes, ctype)
    except Exception:
        pass

    extraction_input = ocr_text.strip() if (ocr_text and len(ocr_text.strip()) > 20) else f"Loan application form, market: {state['market']}"
    loan_app_fields = agent.extract_loan_application(extraction_input, state["market"])

    dbase.save_loan_application(
        application_id=state["application_id"],
        market=state["market"],
        document_id=loan_app_doc["id"],
        extracted_fields=loan_app_fields
    )
    dbase.log_audit(
        application_id=state["application_id"],
        action="EXTRACT_LOAN_APP",
        actor="loan_application_agent",
        details={"fields_found": len([k for k, v in loan_app_fields.items() if isinstance(v, dict) and v.get("value")])}
    )
    return {"loan_app_data": loan_app_fields}


def cross_reference_step(state: WorkflowState) -> dict:
    """Compare loan application fields against supporting document extractions."""
    dbase = get_db()
    loan_app_data = state.get("loan_app_data")
    if not loan_app_data:
        return {"discrepancies": []}

    docs = dbase.get_documents_by_batch(state["batch_id"])
    supporting_extractions = {}
    for doc in docs:
        if doc["document_type"] != "loan_application":
            exts = dbase.get_extractions(doc["id"])
            supporting_extractions[doc["id"]] = {
                "doc_type": doc["document_type"],
                "extractions": exts
            }

    discrepancies = run_cross_reference(loan_app_data, supporting_extractions)
    saved = dbase.save_discrepancies(state["application_id"], discrepancies)

    high_count = sum(1 for d in discrepancies if d.get("status") == "MISMATCH" and d.get("severity") == "HIGH")
    dbase.log_audit(
        application_id=state["application_id"],
        action="CROSS_REFERENCE",
        actor="cross_reference_agent",
        details={"total_checks": len(discrepancies), "mismatches": sum(1 for d in discrepancies if d.get("status") == "MISMATCH"), "high_severity": high_count}
    )
    return {"discrepancies": discrepancies}


def should_continue_extracting(state: WorkflowState) -> str:
    idx = state.get("current_doc_index", 0)
    total = len(state.get("document_ids", []))
    return "extract" if idx < total else "validate"


def build_workflow():
    workflow = StateGraph(WorkflowState)
    workflow.add_node("extract_loan_app", extract_loan_application_step)
    workflow.add_node("extract", extract_document)
    workflow.add_node("validate", validate_extractions)
    workflow.add_node("cross_reference", cross_reference_step)
    workflow.add_node("recommend", generate_recommendation)
    workflow.add_node("pause_review", pause_for_review)
    workflow.set_entry_point("extract_loan_app")
    workflow.add_edge("extract_loan_app", "extract")
    workflow.add_conditional_edges("extract", should_continue_extracting,
                                   {"extract": "extract", "validate": "validate"})
    workflow.add_edge("validate", "cross_reference")
    workflow.add_conditional_edges("cross_reference", check_review_needed_after_cross_ref,
                                   {"needs_review": "pause_review", "all_clear": "recommend"})
    workflow.add_edge("recommend", END)
    workflow.add_edge("pause_review", END)

    # Optional PostgresSaver for full state persistence
    if POSTGRES_CHECKPOINTER_AVAILABLE and os.getenv("SUPABASE_URL"):
        try:
            host_id = os.getenv("SUPABASE_URL", "").replace("https://", "").split(".")[0]
            conn = f"postgresql://postgres:{os.getenv('SUPABASE_DB_PASSWORD','')}@db.{host_id}.supabase.co:5432/postgres"
            checkpointer = PostgresSaver.from_conn_string(conn)
            return workflow.compile(checkpointer=checkpointer)
        except Exception:
            pass

    return workflow.compile()


orchestrator = build_workflow()
