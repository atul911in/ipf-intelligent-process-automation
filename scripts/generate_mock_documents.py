"""
IPF PoC - Mock Document Image Generator
Generates PDF documents mimicking real document layouts for testing OCR + extraction.
Uses reportlab for PDF generation.

Usage: python generate_mock_documents.py
Output: test-data/{market}/{category}/generated/ directory with PDF files
"""

import json
import os
from pathlib import Path
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import black, grey, lightgrey, white, HexColor
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Table, TableStyle

BASE_DIR = Path(__file__).parent.parent / "test-data"
OUTPUT_SUFFIX = "generated"


def create_output_dir(market, category):
    out = BASE_DIR / market / category / OUTPUT_SUFFIX
    out.mkdir(parents=True, exist_ok=True)
    return out


# ============================================================
# POLISH DOCUMENTS
# ============================================================

def generate_polish_id(data, output_path):
    """Generate a mock Polish ID card (Dowod Osobisty) PDF."""
    filepath = output_path / f"{data['document_id']}.pdf"
    c = canvas.Canvas(str(filepath), pagesize=(86*mm, 54*mm))  # ID card size
    
    # Background
    c.setFillColor(HexColor("#E8F0FE"))
    c.rect(0, 0, 86*mm, 54*mm, fill=1)
    
    # Header
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 6)
    c.drawString(3*mm, 50*mm, "RZECZPOSPOLITA POLSKA")
    c.setFont("Helvetica", 5)
    c.drawString(3*mm, 47*mm, "DOWOD OSOBISTY / IDENTITY CARD")
    
    # Photo placeholder
    c.setFillColor(lightgrey)
    c.rect(3*mm, 15*mm, 22*mm, 28*mm, fill=1)
    c.setFillColor(grey)
    c.setFont("Helvetica", 4)
    c.drawString(7*mm, 28*mm, "[PHOTO]")
    
    # Fields
    gt = data["ground_truth"]
    c.setFillColor(black)
    c.setFont("Helvetica", 4)
    
    fields = [
        (28*mm, 44*mm, "Nazwisko / Surname:", gt.get("last_name", "")),
        (28*mm, 40*mm, "Imie / Name:", gt.get("first_name", "")),
        (28*mm, 36*mm, "Data urodzenia / Date of birth:", gt.get("date_of_birth", "")),
        (28*mm, 32*mm, "PESEL:", gt.get("pesel", "")),
        (28*mm, 28*mm, "Nr dokumentu / Doc No:", gt.get("document_number", "")),
        (28*mm, 24*mm, "Wazny do / Valid until:", gt.get("expiry_date", "")),
        (28*mm, 20*mm, "Obywatelstwo / Nationality:", gt.get("nationality", "")),
        (28*mm, 16*mm, "Plec / Sex:", gt.get("sex", "")),
    ]
    
    for x, y, label, value in fields:
        c.setFont("Helvetica", 3.5)
        c.setFillColor(grey)
        c.drawString(x, y, label)
        c.setFont("Helvetica-Bold", 5)
        c.setFillColor(black)
        c.drawString(x, y - 3*mm, value)
    
    # Footer
    c.setFont("Helvetica", 3)
    c.setFillColor(grey)
    c.drawString(3*mm, 3*mm, f"Organ wydajacy: {gt.get('issuing_authority', '')}")
    
    c.save()
    return filepath


def generate_polish_utility_bill(data, output_path):
    """Generate a mock Polish utility bill (Faktura VAT) PDF."""
    filepath = output_path / f"{data['document_id']}.pdf"
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4
    
    gt = data["ground_truth"]
    
    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 2*cm, gt.get("provider_name", "Provider"))
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height - 3.5*cm, "FAKTURA VAT")
    
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, height - 4.5*cm, f"Numer: {gt.get('invoice_number', '')}")
    c.drawString(2*cm, height - 5*cm, f"Data wystawienia: {gt.get('invoice_date', '')}")
    
    # Customer section
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2*cm, height - 7*cm, "NABYWCA / ODBIORCA:")
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, height - 7.7*cm, gt.get("customer_name", ""))
    c.drawString(2*cm, height - 8.4*cm, gt.get("customer_address", ""))
    
    # Billing details
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, height - 10*cm, f"Okres rozliczeniowy: {gt.get('billing_period', '')}")
    c.drawString(2*cm, height - 10.7*cm, f"Numer licznika: {gt.get('meter_number', '')}")
    
    # Amount
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, height - 12.5*cm, f"DO ZAPLATY: {gt.get('amount_due', '')}")
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, height - 13.2*cm, f"Termin platnosci: {gt.get('due_date', '')}")
    
    c.save()
    return filepath


def generate_polish_payslip(data, output_path):
    """Generate a mock Polish payslip (Pasek wynagrodzen) PDF."""
    filepath = output_path / f"{data['document_id']}.pdf"
    c = canvas.Canvas(str(filepath), pagesize=A4)
    width, height = A4
    
    gt = data["ground_truth"]
    
    # Header
    c.setFont("Helvetica-Bold", 11)
    c.drawString(2*cm, height - 2*cm, gt.get("employer_name", ""))
    c.setFont("Helvetica", 8)
    c.drawString(2*cm, height - 2.7*cm, gt.get("employer_address", ""))
    c.drawString(2*cm, height - 3.2*cm, f"NIP: {gt.get('employer_nip', '')}")
    
    # Title
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height - 4.5*cm, "PASEK WYNAGRODZEN")
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, height - 5.2*cm, f"Okres: {gt.get('pay_period', '')}")
    
    # Employee
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2*cm, height - 6.5*cm, "Pracownik:")
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, height - 7.2*cm, gt.get("employee_name", ""))
    c.drawString(2*cm, height - 7.7*cm, f"PESEL: {gt.get('employee_pesel', '')}")
    c.drawString(2*cm, height - 8.2*cm, f"Stanowisko: {gt.get('position', '')}")
    
    # Salary breakdown
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2*cm, height - 9.5*cm, "Skladniki wynagrodzenia:")
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, height - 10.2*cm, f"Wynagrodzenie brutto: {gt.get('gross_salary', '')}")
    c.drawString(2*cm, height - 10.7*cm, f"Zaliczka na podatek: {gt.get('tax_deducted', '')}")
    c.drawString(2*cm, height - 11.2*cm, f"Skladki ZUS: {gt.get('social_security_employee', '')}")
    
    # Net
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2*cm, height - 12.5*cm, f"DO WYPLATY (netto): {gt.get('net_salary', '')}")
    c.setFont("Helvetica", 8)
    c.drawString(2*cm, height - 13.2*cm, f"Data wyplaty: {gt.get('payment_date', '')}")
    
    c.save()
    return filepath


# ============================================================
# ROMANIAN DOCUMENTS
# ============================================================

def generate_romanian_id(data, output_path):
    """Generate a mock Romanian ID card (Carte de Identitate) PDF."""
    filepath = output_path / f"{data['document_id']}.pdf"
    c = canvas.Canvas(str(filepath), pagesize=(86*mm, 54*mm))
    
    # Background
    c.setFillColor(HexColor("#FFF8E1"))
    c.rect(0, 0, 86*mm, 54*mm, fill=1)
    
    # Header
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 5)
    c.drawString(3*mm, 50*mm, "ROMANIA")
    c.setFont("Helvetica", 4)
    c.drawString(3*mm, 47*mm, "CARTE DE IDENTITATE")
    
    # Photo placeholder
    c.setFillColor(lightgrey)
    c.rect(3*mm, 15*mm, 22*mm, 28*mm, fill=1)
    c.setFillColor(grey)
    c.setFont("Helvetica", 4)
    c.drawString(7*mm, 28*mm, "[FOTO]")
    
    gt = data["ground_truth"]
    c.setFillColor(black)
    
    fields = [
        (28*mm, 44*mm, "Nume / Last name:", gt.get("last_name", "")),
        (28*mm, 40*mm, "Prenume / First name:", gt.get("first_name", "")),
        (28*mm, 36*mm, "CNP:", gt.get("cnp", "")),
        (28*mm, 32*mm, "Seria/Nr:", f"{gt.get('document_series', '')} {gt.get('document_number', '')}"),
        (28*mm, 28*mm, "Data nasterii:", gt.get("date_of_birth", "")),
        (28*mm, 24*mm, "Valabil pana la:", gt.get("expiry_date", "")),
        (28*mm, 20*mm, "Domiciliu:", gt.get("address", "")[:40]),
    ]
    
    for x, y, label, value in fields:
        c.setFont("Helvetica", 3.5)
        c.setFillColor(grey)
        c.drawString(x, y, label)
        c.setFont("Helvetica-Bold", 4.5)
        c.setFillColor(black)
        c.drawString(x, y - 2.5*mm, str(value))
    
    c.save()
    return filepath


# ============================================================
# HUNGARIAN DOCUMENTS
# ============================================================

def generate_hungarian_id(data, output_path):
    """Generate a mock Hungarian ID card (Szemelyazonossagi igazolvany) PDF."""
    filepath = output_path / f"{data['document_id']}.pdf"
    c = canvas.Canvas(str(filepath), pagesize=(86*mm, 54*mm))
    
    c.setFillColor(HexColor("#E8F5E9"))
    c.rect(0, 0, 86*mm, 54*mm, fill=1)
    
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 5)
    c.drawString(3*mm, 50*mm, "MAGYARORSZAG / HUNGARY")
    c.setFont("Helvetica", 4)
    c.drawString(3*mm, 47*mm, "SZEMELYAZONOSSAGI IGAZOLVANY")
    
    c.setFillColor(lightgrey)
    c.rect(3*mm, 15*mm, 22*mm, 28*mm, fill=1)
    
    gt = data["ground_truth"]
    c.setFillColor(black)
    
    fields = [
        (28*mm, 44*mm, "Csaladi nev:", gt.get("last_name", "")),
        (28*mm, 40*mm, "Utonev:", gt.get("first_name", "")),
        (28*mm, 36*mm, "Szemelyi szam:", gt.get("personal_id_number", "")),
        (28*mm, 32*mm, "Okmany szama:", gt.get("document_number", "")),
        (28*mm, 28*mm, "Szuletesi datum:", gt.get("date_of_birth", "")),
        (28*mm, 24*mm, "Ervenyes:", gt.get("expiry_date", "")),
        (28*mm, 20*mm, "Anyja neve:", gt.get("mothers_name", "")),
    ]
    
    for x, y, label, value in fields:
        c.setFont("Helvetica", 3.5)
        c.setFillColor(grey)
        c.drawString(x, y, label)
        c.setFont("Helvetica-Bold", 4.5)
        c.setFillColor(black)
        c.drawString(x, y - 2.5*mm, str(value))
    
    c.save()
    return filepath


# ============================================================
# CZECH DOCUMENTS
# ============================================================

def generate_czech_id(data, output_path):
    """Generate a mock Czech ID card (Obcansky prukaz) PDF."""
    filepath = output_path / f"{data['document_id']}.pdf"
    c = canvas.Canvas(str(filepath), pagesize=(86*mm, 54*mm))
    
    c.setFillColor(HexColor("#E3F2FD"))
    c.rect(0, 0, 86*mm, 54*mm, fill=1)
    
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 5)
    c.drawString(3*mm, 50*mm, "CESKA REPUBLIKA")
    c.setFont("Helvetica", 4)
    c.drawString(3*mm, 47*mm, "OBCANSKY PRUKAZ / IDENTITY CARD")
    
    c.setFillColor(lightgrey)
    c.rect(3*mm, 15*mm, 22*mm, 28*mm, fill=1)
    
    gt = data["ground_truth"]
    c.setFillColor(black)
    
    fields = [
        (28*mm, 44*mm, "Prijmeni / Surname:", gt.get("last_name", "")),
        (28*mm, 40*mm, "Jmeno / Name:", gt.get("first_name", "")),
        (28*mm, 36*mm, "Rodne cislo:", gt.get("rodne_cislo", "")),
        (28*mm, 32*mm, "Cislo dokladu:", gt.get("document_number", "")),
        (28*mm, 28*mm, "Datum narozeni:", gt.get("date_of_birth", "")),
        (28*mm, 24*mm, "Platnost do:", gt.get("expiry_date", "")),
        (28*mm, 20*mm, "Adresa:", gt.get("permanent_address", "")[:35]),
    ]
    
    for x, y, label, value in fields:
        c.setFont("Helvetica", 3.5)
        c.setFillColor(grey)
        c.drawString(x, y, label)
        c.setFont("Helvetica-Bold", 4.5)
        c.setFillColor(black)
        c.drawString(x, y - 2.5*mm, str(value))
    
    c.save()
    return filepath


# ============================================================
# MAIN - Generate all documents
# ============================================================

def load_ground_truth(market, category):
    path = BASE_DIR / market / category / "ground-truth.json"
    if path.exists():
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return []


def main():
    generated_count = 0
    
    # Polish documents
    print("Generating Polish documents...")
    for data in load_ground_truth("poland", "identity"):
        out = create_output_dir("poland", "identity")
        generate_polish_id(data, out)
        generated_count += 1
    
    for data in load_ground_truth("poland", "address"):
        out = create_output_dir("poland", "address")
        generate_polish_utility_bill(data, out)
        generated_count += 1
    
    for data in load_ground_truth("poland", "income"):
        out = create_output_dir("poland", "income")
        generate_polish_payslip(data, out)
        generated_count += 1
    
    # Romanian documents
    print("Generating Romanian documents...")
    for data in load_ground_truth("romania", "identity"):
        out = create_output_dir("romania", "identity")
        generate_romanian_id(data, out)
        generated_count += 1
    
    for data in load_ground_truth("romania", "address"):
        out = create_output_dir("romania", "address")
        generate_polish_utility_bill(data, out)  # Same layout, different content
        generated_count += 1
    
    for data in load_ground_truth("romania", "income"):
        out = create_output_dir("romania", "income")
        generate_polish_payslip(data, out)  # Same layout pattern
        generated_count += 1
    
    # Hungarian documents
    print("Generating Hungarian documents...")
    for data in load_ground_truth("hungary", "identity"):
        out = create_output_dir("hungary", "identity")
        generate_hungarian_id(data, out)
        generated_count += 1
    
    for data in load_ground_truth("hungary", "income"):
        out = create_output_dir("hungary", "income")
        generate_polish_payslip(data, out)  # Reuse payslip layout
        generated_count += 1
    
    # Czech documents
    print("Generating Czech documents...")
    for data in load_ground_truth("czech", "identity"):
        out = create_output_dir("czech", "identity")
        generate_czech_id(data, out)
        generated_count += 1
    
    for data in load_ground_truth("czech", "income"):
        out = create_output_dir("czech", "income")
        generate_polish_payslip(data, out)  # Reuse layout
        generated_count += 1
    
    for data in load_ground_truth("czech", "residence"):
        out = create_output_dir("czech", "residence")
        generate_polish_utility_bill(data, out)  # Reuse layout
        generated_count += 1
    
    print(f"\nDone! Generated {generated_count} mock PDF documents.")
    print(f"Output directories: test-data/{{market}}/{{category}}/generated/")


if __name__ == "__main__":
    main()

