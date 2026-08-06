from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt

IPF_DARK   = RGBColor(0x00, 0x54, 0x4E)
IPF_MID    = RGBColor(0x00, 0x6E, 0x66)
IPF_GREEN  = RGBColor(0x7D, 0xC2, 0x42)
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GREY = RGBColor(0xF4, 0xF7, 0xF6)
DARK_TEXT  = RGBColor(0x1A, 0x2E, 0x2A)
MID_GREY   = RGBColor(0x5A, 0x75, 0x70)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
blank = prs.slide_layouts[6]

def bg(slide, color=LIGHT_GREY):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = color

def box(slide, l, t, w, h, color, radius=False):
    shp = slide.shapes.add_shape(1, Inches(l), Inches(t), Inches(w), Inches(h))
    shp.fill.solid(); shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    return shp

def txt(slide, text, l, t, w, h, size=14, bold=False, color=DARK_TEXT, align=PP_ALIGN.LEFT, italic=False):
    tb = slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    run = p.add_run(); run.text = text
    run.font.size = Pt(size); run.font.bold = bold
    run.font.color.rgb = color; run.font.italic = italic
    return tb

def header_bar(slide, title, subtitle=""):
    box(slide, 0, 0, 13.33, 1.4, IPF_DARK)
    box(slide, 0, 1.4, 13.33, 0.06, IPF_GREEN)
    logo = slide.shapes.add_shape(1, Inches(0.3), Inches(0.3), Inches(0.8), Inches(0.8))
    logo.fill.solid(); logo.fill.fore_color.rgb = IPF_GREEN
    logo.line.fill.background()
    ltf = logo.text_frame; ltf.paragraphs[0].alignment = PP_ALIGN.CENTER
    lr = ltf.paragraphs[0].add_run(); lr.text = "IPF"
    lr.font.size = Pt(14); lr.font.bold = True; lr.font.color.rgb = IPF_DARK
    txt(slide, title, 1.3, 0.25, 11, 0.6, size=24, bold=True, color=WHITE)
    if subtitle:
        txt(slide, subtitle, 1.3, 0.85, 11, 0.45, size=12, color=RGBColor(0xD4,0xF5,0xF3))

def pill(slide, text, l, t, w=1.5, color=IPF_GREEN, tcolor=IPF_DARK):
    shp = slide.shapes.add_shape(5, Inches(l), Inches(t), Inches(w), Inches(0.35))
    shp.fill.solid(); shp.fill.fore_color.rgb = color
    shp.line.fill.background()
    stf = shp.text_frame; stf.paragraphs[0].alignment = PP_ALIGN.CENTER
    sr = stf.paragraphs[0].add_run(); sr.text = text
    sr.font.size = Pt(10); sr.font.bold = True; sr.font.color.rgb = tcolor

# ──────────────────────────────────────────────────────────────
# SLIDE 1: TITLE
# ──────────────────────────────────────────────────────────────
s1 = prs.slides.add_slide(blank)
bg(s1, IPF_DARK)
box(s1, 0, 0, 13.33, 7.5, IPF_DARK)
box(s1, 0, 5.8, 13.33, 1.7, IPF_MID)
box(s1, 1.0, 2.5, 11.33, 0.06, IPF_GREEN)

logo2 = s1.shapes.add_shape(1, Inches(1.0), Inches(1.0), Inches(1.2), Inches(1.2))
logo2.fill.solid(); logo2.fill.fore_color.rgb = IPF_GREEN
logo2.line.fill.background()
ltf2 = logo2.text_frame; ltf2.paragraphs[0].alignment = PP_ALIGN.CENTER
lr2 = ltf2.paragraphs[0].add_run(); lr2.text = "IPF"
lr2.font.size = Pt(20); lr2.font.bold = True; lr2.font.color.rgb = IPF_DARK

txt(s1, "IPF Intelligent Process Automation", 2.5, 1.0, 10, 0.8, size=14, color=RGBColor(0x7D,0xC2,0x42))
txt(s1, "AI-Powered Loan Origination PoC", 2.5, 1.7, 10, 1.0, size=36, bold=True, color=WHITE)
txt(s1, "Process Alignment: Polish Market", 1.0, 2.8, 11, 0.7, size=20, color=RGBColor(0xD4,0xF5,0xF3))
txt(s1, "Mapping to IPF Loan Origination Process v1.0  |  Poland", 1.0, 6.0, 11, 0.5, size=12, color=RGBColor(0xA0,0xC8,0xC4))
txt(s1, "CONFIDENTIAL  |  INTERNAL REVIEW", 1.0, 6.6, 11, 0.5, size=10, color=RGBColor(0x5A,0x85,0x80))

# ──────────────────────────────────────────────────────────────
# SLIDE 2: AGENDA
# ──────────────────────────────────────────────────────────────
s2 = prs.slides.add_slide(blank)
bg(s2)
header_bar(s2, "Agenda", "What this pack covers")
items = [
    ("1", "PoC Overview", "What was built and how it works"),
    ("2", "Phase Mapping", "How the PoC aligns to each Polish process phase"),
    ("3", "AI Enhancement Layer", "Where the PoC adds value over current tooling"),
    ("4", "Integration Blueprint", "Where the PoC fits in the live MySales / IRIS flow"),
    ("5", "Key Differentiators", "NBFI decisioning engine specifics for Poland"),
    ("6", "Next Steps", "Integration path and open questions"),
]
for i, (num, title, sub) in enumerate(items):
    row = 1.7 + i * 0.82
    box(s2, 0.4, row, 0.5, 0.55, IPF_GREEN)
    ntf = s2.shapes[-1].text_frame; ntf.paragraphs[0].alignment = PP_ALIGN.CENTER
    nr = ntf.paragraphs[0].add_run(); nr.text = num
    nr.font.size = Pt(16); nr.font.bold = True; nr.font.color.rgb = IPF_DARK
    txt(s2, title, 1.1, row + 0.02, 3.5, 0.3, size=13, bold=True, color=IPF_DARK)
    txt(s2, sub, 1.1, row + 0.3, 11, 0.3, size=10, color=MID_GREY)
    box(s2, 0.4, row + 0.6, 12.53, 0.02, LIGHT_GREY)

# ──────────────────────────────────────────────────────────────
# SLIDE 3: POC OVERVIEW
# ──────────────────────────────────────────────────────────────
s3 = prs.slides.add_slide(blank)
bg(s3)
header_bar(s3, "PoC Overview", "What was built")
cards = [
    ("Admin Portal", "Two-step document upload. Loan application form + supporting docs (ID, income, address, bank statement). Market selector: PL/RO/HU/CZ."),
    ("Reviewer Portal", "AI OCR extraction with confidence scoring. Three-panel view: loan application, supporting docs, cross-reference discrepancies. Manual approve/reject per document."),
    ("Assessor Portal", "5-stage NBFI decisioning engine. Credit score gauge, risk flags with explanations. Final APPROVE / DECLINE decision with reason codes."),
    ("AI Backend", "LangGraph orchestrator with 5 AI agents. FastAPI on port 8000. SQLite persistence. OpenAI GPT-4o-mini for field extraction and recommendation."),
]
cols = [(0.3, 6.2), (6.8, 6.2)]
for i, (title, body) in enumerate(cards):
    col = i % 2; row_offset = i // 2
    l = cols[col][0]; w = cols[col][1]
    t = 1.7 + row_offset * 2.4
    box(s3, l, t, w, 2.1, WHITE)
    box(s3, l, t, 0.08, 2.1, IPF_GREEN)
    txt(s3, title, l + 0.2, t + 0.15, w - 0.3, 0.4, size=13, bold=True, color=IPF_DARK)
    txt(s3, body, l + 0.2, t + 0.55, w - 0.3, 1.4, size=10, color=DARK_TEXT)

# ──────────────────────────────────────────────────────────────
# SLIDE 4: PHASE MAPPING TABLE
# ──────────────────────────────────────────────────────────────
s4 = prs.slides.add_slide(blank)
bg(s4)
header_bar(s4, "Phase Mapping: Poland Process vs PoC", "IPF Loan Origination Process v1.0 alignment")

headers = ["IPF Poland Phase", "PoC Component", "Alignment"]
col_w = [3.8, 5.8, 2.4]
col_x = [0.3, 4.2, 10.1]
box(s4, 0.3, 1.55, 12.73, 0.45, IPF_DARK)
for j, h in enumerate(headers):
    txt(s4, h, col_x[j]+0.1, 1.6, col_w[j]-0.1, 0.35, size=11, bold=True, color=WHITE)

rows = [
    ("Phase 1 — Eligibility (S1)\nPESEL / PIN entry, soft check,\nearly rejection if not eligible",
     "NBFI Stage 0: Regulatory Gateway\nPESEL checksum, age 18-75,\nID expiry, AML/PEP filter",
     "Strong"),
    ("Phase 2 — Scoring (S2)\nBIG/BIK bureau consents,\nhard credit check via GDS",
     "NBFI Stage 2: Bureau Routing\nMock BIK score (1-100),\nBIG registry (KRD/ERIF/BIG InfoMonitor)",
     "Strong"),
    ("Phase 3 — Evidence & Underwriting\nMyCamera captures docs,\nIRIS review blocks sale",
     "Admin upload + Reviewer Portal\nAI OCR, confidence scoring,\ncross-reference engine",
     "Strong"),
    ("Phase 3 (cont.) — Affordability\nGDS credit strategy,\nDTI rules applied",
     "NBFI Stage 3: Legal Caps & DTI\nAnti-usury MPKK formula,\n40%/50% DTI caps by income band",
     "Strong"),
    ("Phase 4 — Decision & Signature\nLoan Calculator, Focus agreement",
     "Assessor Portal\nFinal APPROVE/DECLINE,\nreason codes, product route",
     "Partial"),
]
for i, (col1, col2, col3) in enumerate(rows):
    t = 2.1 + i * 0.95
    bg_col = WHITE if i % 2 == 0 else RGBColor(0xF0, 0xF9, 0xF7)
    box(s4, 0.3, t, 12.73, 0.92, bg_col)
    txt(s4, col1, col_x[0]+0.1, t+0.05, col_w[0]-0.1, 0.82, size=9, color=DARK_TEXT)
    txt(s4, col2, col_x[1]+0.1, t+0.05, col_w[1]-0.1, 0.82, size=9, color=DARK_TEXT)
    align_color = IPF_GREEN if col3 == "Strong" else RGBColor(0xF5,0x9E,0x0B)
    pill(s4, col3, col_x[2]+0.2, t+0.28, 1.8, align_color, IPF_DARK if col3=="Strong" else WHITE)

# ──────────────────────────────────────────────────────────────
# SLIDE 5: AI ENHANCEMENT LAYER
# ──────────────────────────────────────────────────────────────
s5 = prs.slides.add_slide(blank)
bg(s5)
header_bar(s5, "AI Enhancement Layer", "Where the PoC adds value over current IRIS / manual underwriting")

enhancements = [
    ("Document Intake", "IRIS today", "Manual image review by UWT staff. No automated field extraction.", "PoC today", "AI OCR extracts all fields (name, DOB, income, address, PESEL) with confidence scores. Low-confidence fields flagged automatically for human review."),
    ("Pre-Screening", "IRIS today", "Bureau API calls run for all applicants regardless of basic eligibility.", "PoC today", "Stage 0 PESEL checksum + age check eliminates ineligible applications before any bureau API cost is incurred."),
    ("Cross-Reference", "IRIS today", "No automated comparison between the loan application form and supporting documents.", "PoC today", "Cross-reference engine flags income discrepancies (>10%), name mismatches and address conflicts automatically with severity ratings."),
    ("Audit Trail", "IRIS today", "Decision rationale relies on reviewer notes and experience.", "PoC today", "Full documented rule trail for every decision — 5 stages, each rule logged with pass/fail and detail. Complete audit log in the UI."),
]
for i, (title, label1, text1, label2, text2) in enumerate(enhancements):
    t = 1.65 + i * 1.35
    box(s5, 0.3, t, 12.73, 1.25, WHITE)
    box(s5, 0.3, t, 0.08, 1.25, IPF_GREEN)
    txt(s5, title, 0.5, t+0.05, 2.2, 0.35, size=11, bold=True, color=IPF_DARK)
    pill(s5, label1, 2.8, t+0.05, 1.3, RGBColor(0xFF,0xE0,0xB2), RGBColor(0x92,0x40,0x0E))
    txt(s5, text1, 4.2, t+0.05, 4.2, 1.0, size=9, color=DARK_TEXT)
    pill(s5, label2, 8.5, t+0.05, 1.3, RGBColor(0xE8,0xF5,0xE9), IPF_DARK)
    txt(s5, text2, 9.9, t+0.05, 3.0, 1.0, size=9, color=DARK_TEXT)

# ──────────────────────────────────────────────────────────────
# SLIDE 6: INTEGRATION BLUEPRINT
# ──────────────────────────────────────────────────────────────
s6 = prs.slides.add_slide(blank)
bg(s6)
header_bar(s6, "Integration Blueprint", "Where the PoC sits in the live MySales / IRIS flow")

steps = [
    ("MySales\n(Agent App)", IPF_DARK, WHITE),
    ("ESB / ASAD\n(Orchestration)", IPF_DARK, WHITE),
    ("GDS S1+S2\n(Scoring)", IPF_DARK, WHITE),
    ("IPF IPA PoC\n(AI Review Layer)", IPF_GREEN, IPF_DARK),
    ("IRIS / UWT\n(Final UW Sign-off)", IPF_DARK, WHITE),
    ("Focus\n(Agreement)", IPF_DARK, WHITE),
]
box_w = 1.7
start_x = 0.3
y = 2.5
for i, (label, bg_c, tc) in enumerate(steps):
    x = start_x + i * 2.15
    shp = s6.shapes.add_shape(1, Inches(x), Inches(y), Inches(box_w), Inches(1.2))
    shp.fill.solid(); shp.fill.fore_color.rgb = bg_c; shp.line.fill.background()
    stf = shp.text_frame; stf.word_wrap = True
    stf.paragraphs[0].alignment = PP_ALIGN.CENTER
    sr = stf.paragraphs[0].add_run(); sr.text = label
    sr.font.size = Pt(10); sr.font.bold = True; sr.font.color.rgb = tc
    if i < len(steps) - 1:
        arr = s6.shapes.add_shape(5, Inches(x + box_w + 0.05), Inches(y + 0.45), Inches(0.38), Inches(0.3))
        arr.fill.solid(); arr.fill.fore_color.rgb = MID_GREY; arr.line.fill.background()

box(s6, 2.85*2.15+0.3-0.1, 1.7, 2.0, 0.5, RGBColor(0xE8,0xF5,0xE9))
txt(s6, "PoC sits HERE", 2.85*2.15+0.3, 1.75, 1.8, 0.4, size=9, bold=True, color=IPF_DARK, align=PP_ALIGN.CENTER)

txt(s6, "The PoC augments the existing flow between GDS S2 response and IRIS manual review.", 0.4, 4.1, 12.5, 0.5, size=11, color=DARK_TEXT)
txt(s6, "It does not replace MySales, ESB, GDS or the UWT team — it adds an AI pre-screening layer that reduces manual effort and catches discrepancies before the underwriter sees the file.", 0.4, 4.6, 12.5, 0.6, size=10, color=MID_GREY)

box(s6, 0.3, 5.4, 12.73, 1.0, RGBColor(0xE8,0xF5,0xE9))
box(s6, 0.3, 5.4, 0.08, 1.0, IPF_GREEN)
txt(s6, "Integration approach: REST API. The PoC exposes a FastAPI backend on port 8000. A lightweight adapter in ASAD or ESB can POST document bundles to /api/upload and poll /api/status/{id} for the AI review result before routing to IRIS.", 0.5, 5.45, 12.4, 0.85, size=10, color=DARK_TEXT)

# ──────────────────────────────────────────────────────────────
# SLIDE 7: NBFI DECISIONING ENGINE
# ──────────────────────────────────────────────────────────────
s7 = prs.slides.add_slide(blank)
bg(s7)
header_bar(s7, "NBFI 5-Stage Decisioning Engine", "Calibrated to Polish regulatory architecture")

stages = [
    ("Stage 0", "Regulatory Gateway", "Age 18-75, PESEL checksum, ID expiry, AML/PEP. Hard stop — no bureau cost if fails.", IPF_DARK),
    ("Stage 1", "Fraud & Identity", "Name consistency across all documents (KontoConnect simulation). Absolute hard reject on mismatch.", RGBColor(0x1A,0x52,0x76)),
    ("Stage 2", "Bureau Routing", "Mock BIK score (1-100). BIG registry (KRD/ERIF/BIG InfoMonitor). Thin file → probationary product, not rejection.", RGBColor(0x02,0x84,0xC7)),
    ("Stage 3", "Legal Caps & DTI", "Anti-usury MPKK formula. DTI: <3,500 PLN = 40% cap; >=3,500 PLN = 50% cap. Income verified via salary tags.", RGBColor(0x08,0x91,0xB2)),
    ("Stage 4", "Decision Matrix", "BIK band x BIG debt x DTI → REJECT / WITH CAP / STANDARD / UPSELL / PROBATIONARY.", IPF_GREEN),
]
for i, (num, title, detail, color) in enumerate(stages):
    t = 1.65 + i * 1.0
    box(s7, 0.3, t, 0.7, 0.82, color)
    ntf = s7.shapes[-1].text_frame; ntf.paragraphs[0].alignment = PP_ALIGN.CENTER
    nr = ntf.paragraphs[0].add_run(); nr.text = num
    nr.font.size = Pt(9); nr.font.bold = True; nr.font.color.rgb = WHITE if color != IPF_GREEN else IPF_DARK
    box(s7, 1.1, t, 12.0, 0.82, WHITE if i%2==0 else RGBColor(0xF4,0xF7,0xF6))
    txt(s7, title, 1.2, t+0.05, 3.5, 0.35, size=12, bold=True, color=color if color != IPF_GREEN else IPF_DARK)
    txt(s7, detail, 1.2, t+0.42, 11.7, 0.35, size=9.5, color=DARK_TEXT)
    if i < len(stages)-1:
        arr2 = s7.shapes.add_shape(5, Inches(0.52), Inches(t+0.84), Inches(0.26), Inches(0.18))
        arr2.fill.solid(); arr2.fill.fore_color.rgb = MID_GREY; arr2.line.fill.background()

# ──────────────────────────────────────────────────────────────
# SLIDE 8: NEXT STEPS
# ──────────────────────────────────────────────────────────────
s8 = prs.slides.add_slide(blank)
bg(s8)
header_bar(s8, "Next Steps & Open Questions", "Path to integration")

nxt = [
    ("1", "Live Bureau Integration", "Replace mock BIK/BIG calls with live API connectors to Biuro Informacji Kredytowej and KRD/ERIF. Est. 2-4 weeks depending on API access."),
    ("2", "ASAD / ESB Adapter", "Build lightweight adapter to POST document bundles from MySales/ASAD to the PoC API after S2 response. Rest API, JSON payload."),
    ("3", "IRIS Handoff", "Configure PoC to push AI-reviewed summary (extracted fields, discrepancies, decisioning stage results) into IRIS as a pre-populated underwriting pack."),
    ("4", "OpenAI Key in Production", "Replace GPT-4o-mini with a contracted Azure OpenAI endpoint for data residency compliance (EU)."),
]
open_q = [
    "Romania uploads docs before S2 — confirm if this applies to Poland too.",
    "Is IRIS the target integration point or is QScore (Romania pattern) being considered for Poland?",
    "What is the SLA for UWT review today? This is the baseline for measuring AI pre-screening ROI.",
]
txt(s8, "Recommended next steps", 0.3, 1.55, 8.0, 0.4, size=13, bold=True, color=IPF_DARK)
for i, (num, title, detail) in enumerate(nxt):
    t = 2.0 + i * 1.1
    box(s8, 0.3, t, 0.55, 0.88, IPF_GREEN)
    ntf = s8.shapes[-1].text_frame; ntf.paragraphs[0].alignment = PP_ALIGN.CENTER
    nr = ntf.paragraphs[0].add_run(); nr.text = num
    nr.font.size = Pt(16); nr.font.bold = True; nr.font.color.rgb = IPF_DARK
    box(s8, 0.95, t, 7.5, 0.88, WHITE if i%2==0 else RGBColor(0xF0,0xF9,0xF7))
    txt(s8, title, 1.1, t+0.05, 7.2, 0.33, size=11, bold=True, color=IPF_DARK)
    txt(s8, detail, 1.1, t+0.42, 7.2, 0.38, size=9, color=DARK_TEXT)

txt(s8, "Open questions to confirm with market teams", 9.0, 1.55, 4.0, 0.4, size=11, bold=True, color=IPF_DARK)
box(s8, 9.0, 1.95, 4.0, 4.8, WHITE)
box(s8, 9.0, 1.95, 0.07, 4.8, RGBColor(0xF5,0x9E,0x0B))
for i, q in enumerate(open_q):
    txt(s8, "Q"+str(i+1)+".  "+q, 9.2, 2.1+i*1.5, 3.6, 1.3, size=9, color=DARK_TEXT)

# ──────────────────────────────────────────────────────────────
# SLIDE 9: CLOSING
# ──────────────────────────────────────────────────────────────
s9 = prs.slides.add_slide(blank)
bg(s9, IPF_DARK)
box(s9, 0, 0, 13.33, 7.5, IPF_DARK)
box(s9, 0, 5.5, 13.33, 2.0, IPF_MID)
box(s9, 1.0, 3.5, 11.33, 0.06, IPF_GREEN)

txt(s9, "Summary", 1.0, 1.0, 11, 0.6, size=18, color=IPF_GREEN)
txt(s9, "The PoC covers Phases 1-3 of the Polish origination process with high fidelity.", 1.0, 1.65, 11, 0.55, size=14, color=WHITE)
txt(s9, "It adds AI automation at the highest-effort points: document intake, cross-reference checking and underwriting support.", 1.0, 2.25, 11, 0.55, size=14, color=WHITE)
txt(s9, "The 5-stage NBFI engine is calibrated to BIK/BIG bureaus, Anti-Usury Law and Polish-market DTI rules.", 1.0, 2.85, 11, 0.55, size=14, color=WHITE)
txt(s9, "Integration is via REST API — it augments, not replaces, the existing MySales / ASAD / IRIS stack.", 1.0, 3.45, 11, 0.55, size=14, color=WHITE)
txt(s9, "International Personal Finance  |  AI-Powered Loan Origination PoC  |  Internal Review", 1.0, 5.8, 11, 0.45, size=10, color=RGBColor(0xA0,0xC8,0xC4))

out = "scripts/demo/IPF_IPA_Process_Alignment.pptx"
prs.save(out)
print("Saved: "+out)