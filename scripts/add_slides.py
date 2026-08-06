from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
import copy

IPF_DARK  = RGBColor(0x00, 0x54, 0x4E)
IPF_MID   = RGBColor(0x00, 0x6E, 0x66)
IPF_GREEN = RGBColor(0x7D, 0xC2, 0x42)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT     = RGBColor(0xF4, 0xF7, 0xF6)
GREY      = RGBColor(0x5A, 0x75, 0x70)
DARK      = RGBColor(0x1A, 0x2E, 0x2A)
BLUE      = RGBColor(0x02, 0x77, 0xBD)
PURPLE    = RGBColor(0x6A, 0x1B, 0x9A)
AMBER     = RGBColor(0xF5, 0x9E, 0x0B)
RED       = RGBColor(0xC6, 0x28, 0x28)
TEAL2     = RGBColor(0x00, 0x83, 0x8F)
BG2       = RGBColor(0xE8, 0xF5, 0xE9)
BG3       = RGBColor(0xE3, 0xF2, 0xFD)
BG4       = RGBColor(0xF3, 0xE5, 0xF5)
BG5       = RGBColor(0xFF, 0xF3, 0xE0)

prs = Presentation("scripts/demo/IPF_IPA_Tech_One_Pager.pptx")
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

def bx(s,l,t,w,h,c):
    sh=s.shapes.add_shape(1,Inches(l),Inches(t),Inches(w),Inches(h))
    sh.fill.solid();sh.fill.fore_color.rgb=c;sh.line.fill.background()
    return sh

def tx(s,text,l,t,w,h,size=9,bold=False,color=DARK,align=PP_ALIGN.LEFT,italic=False):
    tb=s.shapes.add_textbox(Inches(l),Inches(t),Inches(w),Inches(h))
    tf=tb.text_frame;tf.word_wrap=True
    p=tf.paragraphs[0];p.alignment=align
    r=p.add_run();r.text=text
    r.font.size=Pt(size);r.font.bold=bold
    r.font.color.rgb=color;r.font.italic=italic

def hdr(s,title,sub=""):
    bx(s,0,0,13.33,1.1,IPF_DARK)
    bx(s,0,1.1,13.33,0.05,IPF_GREEN)
    logo=s.shapes.add_shape(1,Inches(0.2),Inches(0.15),Inches(0.78),Inches(0.78))
    logo.fill.solid();logo.fill.fore_color.rgb=IPF_GREEN;logo.line.fill.background()
    ltf=logo.text_frame;ltf.paragraphs[0].alignment=PP_ALIGN.CENTER
    lr=ltf.paragraphs[0].add_run();lr.text="IPF"
    lr.font.size=Pt(14);lr.font.bold=True;lr.font.color.rgb=IPF_DARK
    tx(s,title,1.15,0.1,11,0.5,size=20,bold=True,color=WHITE)
    if sub:
        tx(s,sub,1.15,0.65,11,0.35,size=9,color=RGBColor(0xA0,0xC8,0xC4))
    bx(s,0,7.3,13.33,0.2,IPF_DARK)
    tx(s,"IPF IPA PoC  |  Technical Architecture Series  |  CONFIDENTIAL",0.3,7.32,12.5,0.16,size=7,color=RGBColor(0xA0,0xC8,0xC4))

def sec(s,label,l,t,w,color):
    bx(s,l,t,w,0.3,color)
    tb=s.shapes.add_textbox(Inches(l+0.1),Inches(t+0.05),Inches(w-0.2),Inches(0.2))
    tf=tb.text_frame;p=tf.paragraphs[0];p.alignment=PP_ALIGN.LEFT
    r=p.add_run();r.text=label
    r.font.size=Pt(8.5);r.font.bold=True;r.font.color.rgb=WHITE

def arr_h(s,x,y,color=GREY):
    a=s.shapes.add_shape(5,Inches(x),Inches(y),Inches(0.35),Inches(0.25))
    a.fill.solid();a.fill.fore_color.rgb=color;a.line.fill.background()

def arr_v(s,x,y,color=GREY):
    a=s.shapes.add_shape(1,Inches(x),Inches(y),Inches(0.08),Inches(0.22))
    a.fill.solid();a.fill.fore_color.rgb=color;a.line.fill.background()

# ═══════════════════════════════════════════════════════════
# SLIDE 2: DATA MODEL & PERSISTENCE SUMMARY
# ═══════════════════════════════════════════════════════════
s2=prs.slides.add_slide(blank)
bx(s2,0,0,13.33,7.5,LIGHT)
hdr(s2,"Data Model & Persistence","SQLite-backed schema — 8 core tables, full lifecycle coverage from upload to decision")

# Left: ERD-style diagram
sec(s2,"Schema Overview",0.2,1.25,5.9,IPF_DARK)
tables=[
    ("documents","batch_id  application_id  document_type\nmarket  storage_path  status  uploaded_by",IPF_DARK,1.65),
    ("extractions","document_id  field_name  extracted_value\ncorrected_value  confidence  validation_status",BLUE,2.55),
    ("loan_applications","application_id  market  document_id\nextracted_fields (JSON blob)",TEAL2,3.45),
    ("discrepancies","application_id  field_pair  declared_value\nextracted_value  status  severity  override",RED,4.35),
    ("workflow_state","batch_id  application_id  status\nrecommendation  started_at  completed_at",PURPLE,5.25),
    ("decisions","application_id  decision  assessor_id\nai_recommendation  reason_codes  timestamp",IPF_GREEN,6.15),
]
for name,cols,color,t in tables:
    bx(s2,0.2,t,5.9,0.75,WHITE)
    bx(s2,0.2,t,0.08,0.75,color)
    tx(s2,name,0.38,t+0.04,5.5,0.28,size=9,bold=True,color=color)
    tx(s2,cols,0.38,t+0.34,5.5,0.36,size=7.5,color=DARK)

# Right: persistence & storage detail
sec(s2,"Persistence Engine",6.3,1.25,6.8,IPF_MID)

persist_items=[
    ("SQLite (ipf_poc.db)","Single file database — zero external infrastructure. All tables created via CREATE IF NOT EXISTS on first startup. db_factory.py provides a clean abstraction layer so the backend can switch to PostgreSQL with a single env flag change.",BG2,IPF_DARK),
    ("File Storage (BLOB)","Uploaded PDFs and images stored as binary BLOBs in the file_storage table (storage_path key, content blob, content_type). No external object storage (S3/GCS) needed for PoC. get_file_bytes() retrieves for OCR processing.",BG3,BLUE),
    ("Document Lifecycle","UPLOADED  >  PROCESSING  >  EXTRACTED  >  PENDING_REVIEW  >  VERIFIED. Status is updated at each agent step. Human reviewer Approve/Reject is the only transition that sets VERIFIED. AI workflow cannot set VERIFIED directly.",BG5,AMBER),
    ("Factory Pattern","get_database() in db_factory.py returns SQLiteDatabase or SupabaseDatabase based on USE_SQLITE env flag. All agent and API code calls db methods — never SQL directly. Enables production swap to managed DB with zero code change.",BG4,PURPLE),
]
y=1.65
for title,detail,bg,color in persist_items:
    bx(s2,6.3,y,6.8,1.1,bg)
    bx(s2,6.3,y,0.07,1.1,color)
    tx(s2,title,6.47,y+0.06,6.4,0.3,size=9,bold=True,color=color)
    tx(s2,detail,6.47,y+0.38,6.4,0.65,size=8,color=DARK)
    y+=1.17

# ═══════════════════════════════════════════════════════════
# SLIDE 3: AUDIT TRAIL & GOVERNANCE SUMMARY
# ═══════════════════════════════════════════════════════════
s3=prs.slides.add_slide(blank)
bx(s3,0,0,13.33,7.5,LIGHT)
hdr(s3,"Audit Trail & Governance","Every action logged — immutable event record, human-in-the-loop controls, full decision accountability")

# Left: event log
sec(s3,"Audit Events — Full Lifecycle Coverage",0.2,1.25,6.0,RED)
events=[
    ("UPLOAD","Admin uploads document batch. Batch ID, file count, application ID, market logged.",IPF_DARK),
    ("EXTRACT_LOAN_APP","LoanApplicationAgent extracts declared fields. Field count logged.",BLUE),
    ("EXTRACT","DocumentAgent extracts fields per document. Fields extracted + OCR method logged.",BLUE),
    ("CROSS_REFERENCE","CrossReferenceAgent runs comparison. Total checks, mismatches, high-severity count logged.",TEAL2),
    ("PAUSE_FOR_REVIEW","Orchestrator pauses workflow. Fields needing review count logged. Human action required.",AMBER),
    ("CORRECT","Reviewer corrects an extracted field value. Old/new value, reviewer ID, document ID logged.",AMBER),
    ("CONFIRM","Reviewer approves document as verified. Reviewer ID, document ID, timestamp logged.",AMBER),
    ("RECOMMEND","AI generates recommendation (APPROVE/DECLINE/REFER). Full recommendation JSON logged.",PURPLE),
    ("APPROVE / DECLINE","Assessor records final decision. Decision, reason codes, assessor ID logged. Immutable.",IPF_GREEN),
    ("WORKFLOW_FAILED","Error in AI pipeline. Full Python traceback stored in details JSON for debugging.",RED),
    ("DISCREPANCY_OVERRIDE","Reviewer overrides a MISMATCH. Explanation and reviewer ID logged.",RED),
]
y=1.65
for i,(action,detail,color) in enumerate(events):
    bx(s3,0.2,y,6.0,0.43,WHITE)
    bx(s3,0.2,y,0.07,0.43,color)
    tx(s3,action,0.37,y+0.03,1.9,0.18,size=8,bold=True,color=color)
    tx(s3,detail,2.35,y+0.03,3.75,0.35,size=7.5,color=DARK)
    y+=0.46

# Right: governance panels
sec(s3,"Governance Principles",6.4,1.25,6.7,IPF_DARK)
gov_items=[
    ("Human-in-the-Loop — Always","The AI pipeline never auto-approves or auto-declines a loan. AI recommendation is advisory. The assessor must explicitly click APPROVE or DECLINE. The reviewer must explicitly click Approve Document or Reject Document for each file.",BG2,IPF_DARK),
    ("Immutable Decision Record","Once an APPROVE or DECLINE is recorded via POST /api/decision, it cannot be overwritten by the workflow. The workflow status moves to DECIDED and is locked.",BG3,BLUE),
    ("No Silent Failures","If the AI workflow fails (WORKFLOW_FAILED), the full Python traceback is stored in audit_log.details JSON. The application status is set to FAILED — visible in the Admin portal Upload History.",BG5,RED),
    ("Reviewer Override Trail","A reviewer who overrides a discrepancy MISMATCH must provide a written explanation. The explanation, their reviewer ID and timestamp are stored in discrepancies.override_explanation. Visible in the Reviewer Portal Panel C.",BG4,PURPLE),
    ("Data Separation","Documents are stored as BLOBs in SQLite — not sent to external storage. OpenAI API calls contain only extracted text (not raw document bytes). PII handling follows local-first PoC architecture.",BG2,TEAL2),
]
y=1.65
for title,detail,bg,color in gov_items:
    bx(s3,6.4,y,6.7,1.0,bg)
    bx(s3,6.4,y,0.07,1.0,color)
    tx(s3,title,6.57,y+0.05,6.3,0.28,size=9,bold=True,color=color)
    tx(s3,detail,6.57,y+0.35,6.3,0.57,size=7.5,color=DARK)
    y+=1.08

# ═══════════════════════════════════════════════════════════
# SLIDE 4: FULL TECHNICAL ARCHITECTURE BLOCK DIAGRAM
# ═══════════════════════════════════════════════════════════
s4=prs.slides.add_slide(blank)
bx(s4,0,0,13.33,7.5,LIGHT)
hdr(s4,"Technical Architecture — PoC Block Diagram","End-to-end system view: UI layer, API layer, AI agent layer, data layer")

# ── LAYER LABELS (left side) ─────────────────────────
layer_labels=[
    (1.25,"UI Layer\n(React/Next.js)"),
    (2.55,"API Layer\n(FastAPI)"),
    (3.75,"Orchestration\n(LangGraph)"),
    (5.05,"AI Agents\n(LangChain)"),
    (6.35,"OCR Pipeline"),
    (7.55,"NBFI Engine"),
    (8.75,"Data Layer\n(SQLite)"),
]
for t,label in layer_labels:
    bx(s4,0.1,t,1.05,1.0,IPF_DARK)
    tx(s4,label,0.12,t+0.25,1.0,0.55,size=7,bold=True,color=WHITE,align=PP_ALIGN.CENTER)

bx(s4,1.2,1.2,12.0,0.05,RGBColor(0xD1,0xE0,0xDD))

# ── UI LAYER ─────────────────────────────────────────
ui_portals=[
    ("Admin Portal\n:3000/admin","Upload docs\nMarket select",IPF_DARK,1.25),
    ("Reviewer Portal\n:3000/reviewer","OCR review\nDiscrep. check",IPF_MID,1.25),
    ("Assessor Portal\n:3000/assessor","Credit score\nAPPROVE/DECLINE",TEAL2,1.25),
]
ux=[1.3,4.85,8.4]
for i,(title,sub,color,t) in enumerate(ui_portals):
    bx(s4,ux[i],t,3.3,0.9,WHITE)
    bx(s4,ux[i],t,3.3,0.08,color)
    tx(s4,title,ux[i]+0.1,t+0.13,3.0,0.3,size=8,bold=True,color=color)
    tx(s4,sub,ux[i]+0.1,t+0.52,3.0,0.3,size=7.5,color=DARK)

# Arrow down UI -> API
for x in [2.8,6.35,9.9]:
    arr_v(s4,x,2.2,GREY)

# ── API LAYER ─────────────────────────────────────────
api_endpoints=[
    ("POST /api/upload\nGET /api/status/{id}\nGET /api/queue","Admin endpoints\n14 total REST APIs",BLUE,2.55),
    ("GET /api/review/{doc}\nPOST /api/review/correct\nPOST /api/review/confirm","Reviewer endpoints",BLUE,2.55),
    ("GET /api/credit-score/{id}\nPOST /api/decision/{id}\nGET /api/discrepancies/{id}","Assessor endpoints",BLUE,2.55),
]
for i,(title,sub,color,t) in enumerate(api_endpoints):
    bx(s4,ux[i],t,3.3,0.9,BG3)
    bx(s4,ux[i],t,0.07,0.9,color)
    tx(s4,title,ux[i]+0.15,t+0.05,3.0,0.48,size=7,color=DARK)
    tx(s4,sub,ux[i]+0.15,t+0.62,3.0,0.22,size=7,bold=True,color=color)

# Arrow: all APIs -> orchestrator (converge)
for x in [2.8,6.35,9.9]:
    arr_v(s4,x,3.5,GREY)

# ── ORCHESTRATION LAYER ───────────────────────────────
bx(s4,1.3,3.75,11.0,0.9,BG4)
bx(s4,1.3,3.75,11.0,0.07,PURPLE)
tx(s4,"LangGraph Orchestrator  —  WorkflowState (TypedDict) shared across all agents",1.45,3.8,10.5,0.25,size=8.5,bold=True,color=PURPLE)
flow="extract_loan_app  >  extract (loop per doc)  >  validate  >  cross_reference  >  [pause_for_review | recommend]  >  END"
tx(s4,flow,1.45,4.1,10.5,0.3,size=8,color=DARK)
tx(s4,"Threading: each upload triggers a daemon thread. Agents run sequentially within the thread. State is passed by value at each node transition.",1.45,4.42,10.5,0.2,size=7,color=GREY,italic=True)

arr_v(s4,6.75,4.7,GREY)

# ── AI AGENTS LAYER ───────────────────────────────────
agents=[
    ("Loan App\nAgent","Extracts declared\nloan fields",BLUE,1.3),
    ("Document\nAgent","Per-doc field\nextraction",BLUE,3.6),
    ("Validator\nAgent","Market rules\nPESEL/DTI/age",TEAL2,5.9),
    ("Cross-Ref\nAgent","Compares app\nvs docs",RED,8.2),
    ("Credit Score\nAgent","5-stage NBFI\ndecisioning",PURPLE,10.5),
]
for name,desc,color,x in agents:
    bx(s4,x,5.05,2.0,0.9,WHITE)
    bx(s4,x,5.05,0.07,0.9,color)
    tx(s4,name,x+0.12,5.1,1.75,0.3,size=8,bold=True,color=color)
    tx(s4,desc,x+0.12,5.45,1.75,0.3,size=7.5,color=DARK)
    if x < 10.5:
        arr_h(s4,x+2.05,5.38,GREY)

# LLM badge
bx(s4,1.3,6.0,11.0,0.22,RGBColor(0xED,0xE7,0xF6))
tx(s4,"LLM: OpenAI GPT-4o-mini via LangChain ChatOpenAI  |  Structured JSON output with confidence scores (0-100 per field)  |  Market context injected via system prompt",1.4,6.02,10.7,0.18,size=7.5,color=PURPLE)

# OCR badge
bx(s4,1.3,6.27,11.0,0.22,RGBColor(0xE0,0xF7,0xFA))
tx(s4,"OCR: pypdf (text PDFs)  +  pytesseract/Tesseract (images/TIFF)  |  Languages: pol, ron, hun, ces, eng  |  Fallback: LLM extraction from raw text",1.4,6.29,10.7,0.18,size=7.5,color=TEAL2)

arr_v(s4,6.75,6.52,GREY)

# ── DATA LAYER ────────────────────────────────────────
bx(s4,1.3,6.75,11.0,0.42,WHITE)
bx(s4,1.3,6.75,11.0,0.07,IPF_DARK)
tx(s4,"SQLite (ipf_poc.db)   documents  |  extractions  |  workflow_state  |  loan_applications  |  discrepancies  |  decisions  |  audit_log  |  file_storage (BLOBs)",1.45,6.8,10.5,0.18,size=8,bold=True,color=IPF_DARK)
tx(s4,"db_factory.py  —  USE_SQLITE=true env flag  |  get_database() factory  |  Swap to PostgreSQL in production with zero code change",1.45,7.0,10.5,0.14,size=7.5,color=DARK)

out="scripts/demo/IPF_IPA_Tech_Full_Pack.pptx"
prs.save(out)
print("Saved "+out+" with "+str(len(prs.slides))+" slides")