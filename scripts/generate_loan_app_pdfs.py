"""
Generate mock loan application PDF forms from test scenario JSON data.
"""
import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm, cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, grey, white

BASE_DIR = Path("test-data/loan-applications")
OUT_DIR = BASE_DIR / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MARKET_NAMES = {"PL": "Poland", "RO": "Romania", "HU": "Hungary", "CZ": "Czech Republic"}
MARKET_COLORS = {"PL": "#003189", "RO": "#003189", "HU": "#005700", "CZ": "#003189"}
CONFLICT_COLOR = HexColor("#DC3545")
CLEAN_COLOR = HexColor("#28A745")

FIELD_LABELS = {
    "applicant_full_name": "Full Name / Imie i Nazwisko / Nume complet",
    "date_of_birth": "Date of Birth / Data urodzenia / Data nasterii",
    "residential_address": "Residential Address / Adres zamieszkania / Adresa",
    "declared_net_monthly_income": "Declared Net Monthly Income",
    "declared_income_currency": "Currency",
    "requested_loan_amount": "Loan Amount Requested",
    "loan_term_weeks": "Loan Term (weeks)",
    "employment_status": "Employment Status",
    "employer_name": "Employer / Pracodawca / Angajator",
    "bank_account_number": "Bank Account Number / Nr rachunku / IBAN",
    "purpose_of_loan": "Purpose of Loan",
    "phone_number": "Phone Number",
    "email_address": "Email Address",
}

def generate_loan_application_pdf(scenario: dict):
    app_id = scenario["application_id"]
    market = scenario["market"]
    fields = scenario["loan_application"]
    conflicts = scenario.get("conflicts", [])
    conflict_field_types = [c["type"] for c in conflicts]

    out_path = OUT_DIR / f"{app_id}_loan_application.pdf"
    c = canvas.Canvas(str(out_path), pagesize=A4)
    width, height = A4
    header_color = HexColor(MARKET_COLORS.get(market, "#003189"))

    # Header
    c.setFillColor(header_color)
    c.rect(0, height - 4*cm, width, 4*cm, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(2*cm, height - 1.5*cm, "IPF HOME CREDIT")
    c.setFont("Helvetica", 11)
    c.drawString(2*cm, height - 2.2*cm, "LOAN APPLICATION FORM")
    c.setFont("Helvetica", 8)
    c.drawString(2*cm, height - 2.9*cm, f"Market: {MARKET_NAMES.get(market, market)}  |  Application ID: {app_id}")

    # Scenario banner
    if conflicts:
        c.setFillColor(CONFLICT_COLOR)
        c.rect(0, height - 5.2*cm, width, 1*cm, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(2*cm, height - 4.6*cm, f"[TEST SCENARIO] {scenario['scenario']}")
    else:
        c.setFillColor(CLEAN_COLOR)
        c.rect(0, height - 5.2*cm, width, 1*cm, fill=1)
        c.setFillColor(white)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(2*cm, height - 4.6*cm, f"[TEST SCENARIO] {scenario['scenario']}")

    # Form fields
    c.setFillColor(black)
    y = height - 6.5*cm

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(header_color)
    c.drawString(2*cm, y, "SECTION A: APPLICANT PERSONAL DETAILS")
    c.setFillColor(black)
    y -= 0.6*cm

    personal_fields = [
        "applicant_full_name", "date_of_birth", "residential_address",
        "phone_number", "email_address"
    ]
    for field in personal_fields:
        if field in fields:
            label = FIELD_LABELS.get(field, field.replace("_", " ").title())
            value = str(fields.get(field, ""))
            c.setFont("Helvetica", 7)
            c.setFillColor(grey)
            c.drawString(2*cm, y, label)
            y -= 0.35*cm
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(black)
            c.drawString(2.5*cm, y, value)
            c.setStrokeColor(grey)
            c.line(2*cm, y - 0.1*cm, width - 2*cm, y - 0.1*cm)
            y -= 0.7*cm

    y -= 0.3*cm
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(header_color)
    c.drawString(2*cm, y, "SECTION B: LOAN DETAILS")
    c.setFillColor(black)
    y -= 0.6*cm

    loan_fields = [
        "declared_net_monthly_income", "declared_income_currency",
        "requested_loan_amount", "loan_term_weeks", "purpose_of_loan"
    ]
    for field in loan_fields:
        if field in fields:
            label = FIELD_LABELS.get(field, field.replace("_", " ").title())
            value = str(fields.get(field, ""))
            c.setFont("Helvetica", 7)
            c.setFillColor(grey)
            c.drawString(2*cm, y, label)
            y -= 0.35*cm
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(black)
            c.drawString(2.5*cm, y, value)
            c.setStrokeColor(grey)
            c.line(2*cm, y - 0.1*cm, width - 2*cm, y - 0.1*cm)
            y -= 0.7*cm

    y -= 0.3*cm
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(header_color)
    c.drawString(2*cm, y, "SECTION C: EMPLOYMENT & BANKING")
    c.setFillColor(black)
    y -= 0.6*cm

    emp_fields = ["employment_status", "employer_name", "bank_account_number"]
    for field in emp_fields:
        if field in fields:
            label = FIELD_LABELS.get(field, field.replace("_", " ").title())
            value = str(fields.get(field, ""))
            c.setFont("Helvetica", 7)
            c.setFillColor(grey)
            c.drawString(2*cm, y, label)
            y -= 0.35*cm
            c.setFont("Helvetica-Bold", 10)
            c.setFillColor(black)
            c.drawString(2.5*cm, y, value)
            c.setStrokeColor(grey)
            c.line(2*cm, y - 0.1*cm, width - 2*cm, y - 0.1*cm)
            y -= 0.7*cm

    # Conflicts summary if any
    if conflicts:
        y -= 0.5*cm
        c.setFont("Helvetica-Bold", 11)
        c.setFillColor(CONFLICT_COLOR)
        c.drawString(2*cm, y, "KNOWN TEST CONFLICTS (for testing only):")
        y -= 0.5*cm
        for conf in conflicts:
            c.setFont("Helvetica", 8)
            c.setFillColor(CONFLICT_COLOR)
            c.drawString(2.5*cm, y, f"[{conf['severity']}] {conf['type']}: {conf['description'][:80]}")
            y -= 0.4*cm

    # Declaration
    y -= 0.5*cm
    c.setFillColor(HexColor("#F8F9FA"))
    c.rect(1.5*cm, y - 1.8*cm, width - 3*cm, 1.8*cm, fill=1)
    c.setFillColor(black)
    c.setFont("Helvetica", 7)
    c.drawString(2*cm, y - 0.4*cm, "I declare that all information provided in this application is true and accurate to the best of my knowledge.")
    c.drawString(2*cm, y - 0.8*cm, "I consent to the processing of my personal data for the purposes of credit assessment in accordance with GDPR.")
    c.drawString(2*cm, y - 1.3*cm, "Signature: ________________________   Date: _______________")

    # Footer
    c.setFillColor(HexColor("#6C757D"))
    c.rect(0, 0, width, 1*cm, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica", 7)
    c.drawString(2*cm, 0.4*cm, f"IPF Home Credit | Application {app_id} | CONFIDENTIAL - Test Document")
    c.drawRightString(width - 2*cm, 0.4*cm, "Page 1 of 1")

    c.save()
    return out_path


# Load scenarios and generate PDFs
with open("test-data/loan-applications/loan-applications-test-scenarios.json", encoding="utf-8-sig") as f:
    scenarios = json.load(f)

print(f"Generating {len(scenarios)} loan application PDFs...")
for s in scenarios:
    path = generate_loan_application_pdf(s)
    conflict_note = f" [{len(s['conflicts'])} conflict(s)]" if s["conflicts"] else " [CLEAN]"
    print(f"  Generated: {path.name}{conflict_note}")

print(f"\nAll PDFs saved to: {OUT_DIR}")
