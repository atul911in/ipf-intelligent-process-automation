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
AMBER     = RGBColor(0xF5, 0x9E, 0x0B)
AMBER_BG  = RGBColor(0xFF, 0xF3, 0xCD)

prs = Presentation()
prs.slide_width  = Inches(13.33)
prs.slide_height = Inches(7.5)
slide = prs.slides.add_slide(prs.slide_layouts[6])

def box(l,t,w,h,color):
    s = slide.shapes.add_shape(1,Inches(l),Inches(t),Inches(w),Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = color; s.line.fill.background()
    return s

def txt(text,l,t,w,h,size=11,bold=False,color=DARK,align=PP_ALIGN.LEFT,italic=False):
    tb = slide.shapes.add_textbox(Inches(l),Inches(t),Inches(w),Inches(h))
    tf = tb.text_frame; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    r.font.size = Pt(size); r.font.bold = bold
    r.font.color.rgb = color; r.font.italic = italic

# ── BACKGROUND ─────────────────────────────────────────────
box(0, 0, 13.33, 7.5, LIGHT)

# ── LEFT DARK COLUMN ───────────────────────────────────────
box(0, 0, 3.6, 7.5, IPF_DARK)
box(3.6, 0, 0.06, 7.5, IPF_GREEN)

# ── TOP HEADER BAR ─────────────────────────────────────────
box(3.66, 0, 9.67, 1.3, IPF_DARK)
box(3.66, 1.3, 9.67, 0.05, IPF_GREEN)

# IPF logo badge
logo = slide.shapes.add_shape(1,Inches(0.3),Inches(0.3),Inches(0.9),Inches(0.9))
logo.fill.solid(); logo.fill.fore_color.rgb = IPF_GREEN; logo.line.fill.background()
ltf = logo.text_frame; ltf.paragraphs[0].alignment = PP_ALIGN.CENTER
lr = ltf.paragraphs[0].add_run(); lr.text = "IPF"
lr.font.size = Pt(16); lr.font.bold = True; lr.font.color.rgb = IPF_DARK

# Header text
txt("IPF Intelligent Process Automation", 4.0, 0.12, 9, 0.45, size=10, color=RGBColor(0x7D,0xC2,0x42))
txt("AI-Powered Loan Origination", 4.0, 0.55, 9, 0.55, size=22, bold=True, color=WHITE)
txt("Executive Overview  |  Poland Home Credit Market  |  Proof of Concept", 4.0, 1.05, 9, 0.32, size=9, color=RGBColor(0xA0,0xC8,0xC4))

# ── LEFT COLUMN CONTENT ────────────────────────────────────
txt("The Challenge", 0.25, 1.55, 3.2, 0.38, size=12, bold=True, color=IPF_GREEN)
txt("Manual document review in the loan origination back-office is time-consuming, error-prone and does not scale. Underwriting teams spend significant time on repetitive extraction tasks before they can make a credit judgement.", 0.25, 1.98, 3.25, 1.1, size=9, color=RGBColor(0xD4,0xF5,0xF3))

txt("The Opportunity", 0.25, 3.2, 3.2, 0.38, size=12, bold=True, color=IPF_GREEN)
txt("AI can pre-screen every document bundle, extract all fields with confidence scores, flag discrepancies and produce a structured decisioning recommendation — before a human reviewer touches the file.", 0.25, 3.6, 3.25, 1.0, size=9, color=RGBColor(0xD4,0xF5,0xF3))

txt("Markets in scope", 0.25, 4.75, 3.2, 0.35, size=11, bold=True, color=IPF_GREEN)
for m, sub in [("Poland","Primary — full regulatory alignment"),("Romania","Supported"),("Hungary","Supported"),("Czech Rep.","Supported")]:
    y = 5.15 + [("Poland","Primary — full regulatory alignment"),("Romania","Supported"),("Hungary","Supported"),("Czech Rep.","Supported")].index((m,sub)) * 0.42
    box(0.25, y, 0.35, 0.32, IPF_GREEN)
    s = slide.shapes[-1].text_frame; s.paragraphs[0].alignment = PP_ALIGN.CENTER
    sr = s.paragraphs[0].add_run(); sr.text = ("PL","RO","HU","CZ")[["Poland","Romania","Hungary","Czech Rep."].index(m)]
    sr.font.size = Pt(8); sr.font.bold = True; sr.font.color.rgb = IPF_DARK
    txt(m, 0.68, y+0.02, 1.4, 0.2, size=9, bold=True, color=WHITE)
    txt(sub, 0.68, y+0.19, 2.7, 0.18, size=7.5, color=RGBColor(0xA0,0xC8,0xC4))

txt("CONFIDENTIAL  |  INTERNAL", 0.25, 7.1, 3.2, 0.3, size=7, color=GREY, italic=True)

# ── RIGHT AREA: THREE ROWS ─────────────────────────────────

# ROW 1: How it works — 3 portal cards
txt("How It Works  —  Three Role-Based Portals", 3.85, 1.5, 9.1, 0.38, size=12, bold=True, color=IPF_DARK)

portals = [
    ("Admin Portal", "Back-office staff upload the loan application form + supporting documents (ID, income, address, bank statement) via a two-step intake wizard.", IPF_DARK),
    ("Reviewer Portal", "Document reviewers verify AI-extracted fields, inspect cross-reference discrepancies and approve or reject each document with confidence-scored evidence.", IPF_MID),
    ("Assessor Portal", "Credit assessors see a clean applicant summary, credit score gauge and 5-stage decisioning breakdown — then record the final Approve or Decline.", IPF_GREEN),
]
for i, (title, body, color) in enumerate(portals):
    x = 3.85 + i * 3.16
    box(x, 1.95, 3.0, 1.65, WHITE)
    box(x, 1.95, 3.0, 0.07, color)
    tc = IPF_DARK if color == IPF_GREEN else WHITE
    hdr = slide.shapes[-2]; htf = hdr.text_frame
    txt(("01  " if i==0 else "02  " if i==1 else "03  ")+title, x+0.12, 2.0, 2.75, 0.35, size=10, bold=True, color=color)
    txt(body, x+0.12, 2.38, 2.75, 1.15, size=8.5, color=DARK)

# ROW 2: AI engine + what it replaces
txt("The AI Engine", 3.85, 3.75, 9.1, 0.35, size=12, bold=True, color=IPF_DARK)

box(3.85, 4.15, 5.85, 1.5, WHITE)
box(3.85, 4.15, 0.07, 1.5, IPF_DARK)
txt("5-Stage NBFI Decisioning Pipeline", 4.0, 4.2, 5.5, 0.35, size=10, bold=True, color=IPF_DARK)
stages = "Stage 0: Regulatory Gateway (PESEL, age, ID expiry, AML)  |  Stage 1: Identity / Fraud check  |  Stage 2: BIK + BIG bureau routing  |  Stage 3: Anti-Usury cost cap + DTI (40%/50% by income)  |  Stage 4: Decision matrix — REJECT / STANDARD / UPSELL / PROBATIONARY"
txt(stages, 4.0, 4.58, 5.6, 1.0, size=8, color=DARK)

box(9.8, 4.15, 3.15, 1.5, WHITE)
box(9.8, 4.15, 0.07, 1.5, AMBER)
txt("What it augments", 9.97, 4.2, 2.9, 0.35, size=10, bold=True, color=DARK)
repl = [
    "IRIS manual review  +  AI pre-screening",
    "BIK/BIG API  +  Mock bureau routing (live-ready)",
    "UWT team judgement  +  AI discrepancy engine",
]
for j, r in enumerate(repl):
    txt("  " + r, 9.97, 4.6 + j*0.33, 2.9, 0.28, size=8, color=DARK)

# ROW 3: Three outcome metrics + bottom note
txt("What this PoC demonstrates", 3.85, 5.78, 9.1, 0.35, size=12, bold=True, color=IPF_DARK)

metrics = [
    ("Faster intake", "AI extracts all document fields in seconds — no manual data entry by reviewers"),
    ("Fewer missed flags", "Cross-reference engine catches income discrepancies, name mismatches and expired IDs automatically"),
    ("Audit-ready decisions", "Every stage of the decisioning engine is logged with rule detail — full audit trail for every application"),
]
for i, (label, detail) in enumerate(metrics):
    x = 3.85 + i * 3.16
    box(x, 6.18, 3.0, 0.9, RGBColor(0xE8,0xF5,0xE9))
    box(x, 6.18, 3.0, 0.07, IPF_GREEN)
    txt(label, x+0.12, 6.24, 2.75, 0.28, size=9, bold=True, color=IPF_DARK)
    txt(detail, x+0.12, 6.52, 2.75, 0.5, size=7.5, color=DARK)

out = "scripts/demo/IPF_IPA_One_Pager.pptx"
prs.save(out)
print("Saved: "+out)