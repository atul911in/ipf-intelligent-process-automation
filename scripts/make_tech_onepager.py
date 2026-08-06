from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

IPF_DARK  = RGBColor(0x00, 0x54, 0x4E)
IPF_MID   = RGBColor(0x00, 0x6E, 0x66)
IPF_GREEN = RGBColor(0x7D, 0xC2, 0x42)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT     = RGBColor(0xF4, 0xF7, 0xF6)
GREY      = RGBColor(0x5A, 0x75, 0x70)
DARK      = RGBColor(0x1A, 0x2E, 0x2A)
BLUE      = RGBColor(0x02, 0x77, 0xBD)
PURPLE    = RGBColor(0x6A, 0x1B, 0x9A)
TEAL2     = RGBColor(0x00, 0x83, 0x8F)
AMBER     = RGBColor(0xF5, 0x9E, 0x0B)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
s = prs.slides.add_slide(prs.slide_layouts[6])

def box(l,t,w,h,color,slide=s):
    sh = slide.shapes.add_shape(1,Inches(l),Inches(t),Inches(w),Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = color; sh.line.fill.background()
    return sh

def txt(text,l,t,w,h,size=9,bold=False,color=DARK,align=PP_ALIGN.LEFT,italic=False,slide=s):
    tb = slide.shapes.add_textbox(Inches(l),Inches(t),Inches(w),Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color; r.font.italic = italic

def section_header(label, l, t, w, color):
    box(l, t, w, 0.32, color)
    tb = s.shapes.add_textbox(Inches(l+0.1), Inches(t+0.04), Inches(w-0.2), Inches(0.25))
    tf = tb.text_frame
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = label
    r.font.size = Pt(9); r.font.bold = True; r.font.color.rgb = WHITE

# ── BACKGROUND ─────────────────────────────────────────────
box(0, 0, 13.33, 7.5, LIGHT)

# ── TOP HEADER ─────────────────────────────────────────────
box(0, 0, 13.33, 1.1, IPF_DARK)
box(0, 1.1, 13.33, 0.05, IPF_GREEN)

logo = s.shapes.add_shape(1,Inches(0.2),Inches(0.15),Inches(0.78),Inches(0.78))
logo.fill.solid(); logo.fill.fore_color.rgb = IPF_GREEN; logo.line.fill.background()
ltf = logo.text_frame; ltf.paragraphs[0].alignment = PP_ALIGN.CENTER
lr = ltf.paragraphs[0].add_run(); lr.text = "IPF"
lr.font.size = Pt(14); lr.font.bold = True; lr.font.color.rgb = IPF_DARK

txt("Technical Architecture", 1.15, 0.08, 7, 0.45, size=20, bold=True, color=WHITE)
txt("IPF Intelligent Process Automation  |  Proof of Concept  |  AI Agent Workflow, Data Persistence, LLM Stack, Audit & Governance", 1.15, 0.6, 11.5, 0.38, size=9, color=RGBColor(0xA0,0xC8,0xC4))

# Key stats top-right
stats = [("5","AI Agents"),("6","LangGraph\nNodes"),("14","REST API\nEndpoints"),("100%","Audit\nLogged")]
for i,(v,l) in enumerate(stats):
    x = 9.5 + i * 0.95
    txt(v, x, 0.05, 0.85, 0.42, size=18, bold=True, color=IPF_GREEN, align=PP_ALIGN.CENTER)
    txt(l, x, 0.47, 0.85, 0.42, size=7, color=RGBColor(0xA0,0xC8,0xC4), align=PP_ALIGN.CENTER)

# ── COLUMN LAYOUT: 3 columns ───────────────────────────────
# Col A: 0.2-4.3  (4.1w)  AI Agent Workflow
# Col B: 4.4-8.8  (4.4w)  Data + Persistence
# Col C: 8.9-13.1 (4.2w)  LLM + Audit

# ════════════════════════════════════════════
# COLUMN A: AI AGENT WORKFLOW
# ════════════════════════════════════════════
section_header("AI Agent Workflow  —  LangGraph Orchestrator", 0.2, 1.25, 4.1, IPF_DARK)

agents = [
    ("Loan Application Agent", "Extracts declared fields from the loan application form: name, DOB, address, income, PESEL, employer, loan amount.", BLUE),
    ("Document Agent", "Extracts fields from each supporting document (ID card, payslip, utility bill, bank statement) using OCR + GPT-4o-mini.", BLUE),
    ("Validator Agent", "Applies market rules to each extracted field: PESEL checksum, CNP/Rodne cislo, expiry dates, age eligibility, income match.", TEAL2),
    ("Cross-Reference Agent", "Compares loan application declared values against extracted document values. Flags MISMATCH, WARNING or MATCH with severity.", TEAL2),
    ("Credit Score Agent", "Runs 5-stage NBFI decisioning engine. Returns score, risk band, product route and full stage audit trail.", PURPLE),
]
y = 1.65
for i,(name,desc,color) in enumerate(agents):
    box(0.2, y, 0.32, 0.55, color)
    ntf = s.shapes[-1].text_frame; ntf.paragraphs[0].alignment = PP_ALIGN.CENTER
    nr = ntf.paragraphs[0].add_run(); nr.text = str(i+1)
    nr.font.size = Pt(10); nr.font.bold = True; nr.font.color.rgb = WHITE
    box(0.55, y, 3.75, 0.55, WHITE)
    txt(name, 0.65, y+0.02, 3.55, 0.22, size=8.5, bold=True, color=color)
    txt(desc, 0.65, y+0.25, 3.55, 0.25, size=7.5, color=DARK)
    if i < len(agents)-1:
        arr = s.shapes.add_shape(5, Inches(0.3), Inches(y+0.57), Inches(0.15), Inches(0.12))
        arr.fill.solid(); arr.fill.fore_color.rgb = GREY; arr.line.fill.background()
    y += 0.7

# Flow labels
box(0.2, 5.25, 4.1, 0.28, RGBColor(0xE8,0xF5,0xE9))
txt("Orchestration: LangGraph StateGraph  |  All agents share WorkflowState (typed dict). Agents execute sequentially with conditional branching at validation and cross-reference nodes.", 0.3, 5.27, 3.9, 0.24, size=7, color=IPF_DARK)

box(0.2, 5.6, 4.1, 0.28, RGBColor(0xE8,0xF5,0xE9))
txt("Entry: extract_loan_app  >  extract (loop per doc)  >  validate  >  cross_reference  >  [pause_review | recommend]  >  END", 0.3, 5.62, 3.9, 0.24, size=7, color=IPF_DARK)

section_header("OCR Pipeline", 0.2, 5.95, 4.1, GREY)
txt("pypdf (text PDFs)  +  pytesseract / Tesseract (image files, TIFF, JPG)  |  Supported languages: pol, ron, hun, ces, eng  |  Fallback: LLM extraction from raw text", 0.3, 6.32, 3.9, 0.4, size=7.5, color=DARK)

# ════════════════════════════════════════════
# COLUMN B: DATA & PERSISTENCE
# ════════════════════════════════════════════
section_header("Data Model  &  Persistence", 4.4, 1.25, 4.4, IPF_MID)

tables = [
    ("documents", "document_id, batch_id, application_id, document_type, market, storage_path, status, uploaded_by, timestamps"),
    ("extractions", "extraction_id, document_id, field_name, extracted_value, corrected_value, confidence, validation_status, validation_reason"),
    ("workflow_state", "batch_id, application_id, market, status [PROCESSING/PENDING_REVIEW/DECIDED/FAILED], recommendation, started_at"),
    ("loan_applications", "application_id, market, extracted_fields (JSON), document_id"),
    ("discrepancies", "discrepancy_id, application_id, field_pair, declared_value, extracted_value, status, severity, override_explanation"),
    ("decisions", "decision_id, application_id, decision [APPROVE/DECLINE], assessor_id, ai_recommendation, reason_codes, timestamp"),
    ("audit_log", "event_id, application_id, action, actor, document_id, details (JSON), timestamp"),
    ("file_storage", "storage_path (key), content (BLOB), content_type  —  stores raw uploaded PDFs/images in SQLite"),
]
y = 1.65
for tname, cols in tables:
    box(4.4, y, 4.4, 0.52, WHITE)
    box(4.4, y, 0.06, 0.52, IPF_MID)
    txt(tname, 4.55, y+0.02, 4.2, 0.2, size=8.5, bold=True, color=IPF_DARK)
    txt(cols, 4.55, y+0.24, 4.1, 0.24, size=6.5, color=DARK)
    y += 0.56

section_header("Storage Engine", 4.4, 5.95, 4.4, GREY)
box(4.4, 6.32, 4.4, 0.55, WHITE)
txt("SQLite (ipf_poc.db)  |  db_factory.py abstracts database access. USE_SQLITE=true env flag. All tables created via CREATE IF NOT EXISTS on startup. File blobs stored as BLOB in file_storage table — no external object storage required for PoC.", 4.5, 6.34, 4.2, 0.5, size=7.5, color=DARK)

# ════════════════════════════════════════════
# COLUMN C: LLM + AUDIT + GOVERNANCE
# ════════════════════════════════════════════
section_header("LLM Stack", 8.9, 1.25, 4.2, PURPLE)

llm_items = [
    ("GPT-4o-mini (OpenAI)", "Primary LLM for field extraction and recommendation. Called by DocumentAgent and LoanApplicationAgent via LangChain ChatOpenAI."),
    ("LangChain", "Prompt templates, output parsing, LLM chain management. Version 0.2.x. Structured JSON output enforced via system prompts."),
    ("LangGraph", "Stateful multi-agent orchestration. StateGraph with typed WorkflowState. Conditional edges at validate and cross_reference nodes."),
    ("Prompt Engineering", "Each agent uses a structured system prompt specifying market context, field schema and output format. Confidence scores (0-100) returned per field."),
]
y = 1.65
for title, detail in llm_items:
    box(8.9, y, 4.2, 0.52, WHITE)
    box(8.9, y, 0.06, 0.52, PURPLE)
    txt(title, 9.05, y+0.02, 3.95, 0.2, size=8.5, bold=True, color=PURPLE)
    txt(detail, 9.05, y+0.24, 3.95, 0.24, size=7, color=DARK)
    y += 0.57

section_header("Audit Trail & Governance", 8.9, 4.0, 4.2, RGBColor(0xC6, 0x28, 0x28))
audit_events = [
    "UPLOAD — document batch ingested",
    "EXTRACT_LOAN_APP — loan application fields extracted",
    "EXTRACT — per-document field extraction",
    "CROSS_REFERENCE — discrepancy check completed",
    "PAUSE_FOR_REVIEW — workflow paused, human review required",
    "CORRECT — reviewer corrected extracted field",
    "CONFIRM — reviewer approved document",
    "RECOMMEND — AI recommendation generated",
    "APPROVE / DECLINE — final assessor decision recorded",
    "WORKFLOW_FAILED — error logged with full traceback",
    "DISCREPANCY_OVERRIDE — reviewer overrode a mismatch",
]
box(8.9, 4.37, 4.2, 2.55, WHITE)
txt("Every event is written to audit_log with: action, actor (agent or user ID), document_id, application_id, JSON details, and UTC timestamp.\n\nEvents logged:", 9.0, 4.4, 3.95, 0.45, size=7.5, color=DARK)
for j, ev in enumerate(audit_events):
    col = 0 if j < 6 else 1
    row = j if j < 6 else j-6
    txt("  " + ev, 9.0 + col*2.1, 4.87 + row*0.33, 2.0, 0.28, size=7, color=DARK)

section_header("Human-in-the-Loop Controls", 8.9, 6.98, 4.2, IPF_MID)
txt("Reviewer must explicitly Approve or Reject each document. Assessor makes final APPROVE/DECLINE. AI recommendation is advisory only — never auto-executes. All decisions are immutable and audit-logged.", 9.0, 7.06, 4.0, 0.38, size=7, color=DARK)

# ── BOTTOM FOOTER ──────────────────────────────────────────
box(0, 7.3, 13.33, 0.2, IPF_DARK)
txt("IPF IPA PoC  |  FastAPI (port 8000)  +  Next.js React UI (port 3000)  |  Python 3.14  |  SQLite  |  LangGraph + LangChain + OpenAI GPT-4o-mini  |  CONFIDENTIAL — INTERNAL REVIEW", 0.3, 7.31, 12.7, 0.18, size=7, color=RGBColor(0xA0,0xC8,0xC4))

out = "scripts/demo/IPF_IPA_Tech_One_Pager.pptx"
prs.save(out)
print("Saved: "+out)