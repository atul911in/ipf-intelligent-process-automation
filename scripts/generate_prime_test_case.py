"""
Generate DEMO-PL-PRIME-001: All-pass 5-stage test case for IPF NBFI decisioning engine.
Applicant: Piotr Nowak - Prime customer, all stages PASS, outcome: APPROVE AND UPSELL
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, white

OUT_DIR = Path("test-data/demo-cases/generated")
OUT_DIR.mkdir(parents=True, exist_ok=True)

APP_ID = "DEMO-PL-PRIME-001"
FULL_NAME = "Piotr Nowak"
DOB = "1984-03-22"
AGE = 41
PESEL = "84032212345"
ID_NUM = "AXC 847291"
ID_EXPIRY = "2030-03-22"
ADDRESS = "ul. Krakowska 15/4, 30-001 Krakow"
EMPLOYER = "Comarch SA"
CONTRACT = "Umowa o prace na czas nieokreslony"
EMP_START = "2018-04-01"
NET_SAL = "5500.00"
GROSS_SAL = "7200.00"
BANK_ACC = "PL61 1090 1014 0000 0712 1981 2345"
LOAN_AMT = "4000.00"
LOAN_WEEKS = "52"
PURPOSE = "Remont mieszkania"

HDR = HexColor("#003189")
GRN = HexColor("#28A745")
TEAL = HexColor("#0d7377")


def page_header(c, title, sub, color):
    w, h = A4
    c.setFillColor(color)
    c.rect(0, h - 4.2*cm, w, 4.2*cm, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, h - 1.6*cm, "IPF HOME CREDIT  |  PROVIDENT POLSKA")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, h - 2.4*cm, title)
    c.setFont("Helvetica", 8)
    c.drawString(2*cm, h - 3.1*cm, sub)
    c.drawString(2*cm, h - 3.8*cm, "Application ID: " + APP_ID + "  |  Market: Poland (PL)")
    c.setFillColor(GRN)
    c.rect(0, h - 5.2*cm, w, 0.9*cm, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(2*cm, h - 4.85*cm, "[DEMO-PL-PRIME-001] All 5 decisioning stages PASS | Expected: APPROVE AND UPSELL")


def row(c, label, value, y, hi=False):
    w = A4[0]
    if hi:
        c.setFillColor(HexColor("#e8f5e9"))
        c.rect(1.5*cm, y - 3, w - 3*cm, 0.65*cm, fill=1, stroke=0)
    c.setFillColor(HDR)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(2*cm, y, label)
    c.setFillColor(black)
    c.setFont("Helvetica", 9)
    c.drawString(8*cm, y, str(value))
    return y - 0.82*cm


def sec(c, text, y, color=None):
    if color is None:
        color = HDR
    w = A4[0]
    c.setFillColor(color)
    c.rect(1.5*cm, y - 2, w - 3*cm, 0.62*cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(2*cm, y + 1, text)
    return y - 1.0*cm


def footer_badge(c, y, lines, color):
    w = A4[0]
    h = len(lines) * 0.42*cm + 0.3*cm
    c.setFillColor(color)
    c.rect(1.5*cm, y - h, w - 3*cm, h, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7)
    yy = y - 0.35*cm
    for line in lines:
        c.drawString(2*cm, yy, line)
        yy -= 0.42*cm
    return y - h - 0.3*cm


def footer(c):
    w, h = A4
    c.setFillColor(HDR)
    c.rect(0, 0.8*cm, w, 0.5*cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica", 7)
    c.drawString(2*cm, 0.95*cm, "IPF Home Credit  |  ul. Krakowska 45, 31-116 Krakow  |  www.provident.pl")

# ===== DOC 1: LOAN APPLICATION =====
def gen_loan_app():
    path = OUT_DIR / (APP_ID + "_1_loan_application.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    page_header(c, "LOAN APPLICATION FORM / WNIOSEK KREDYTOWY", "Customer self-declaration - Stage 0,1,3 data", HDR)
    y = h - 5.8*cm
    y = sec(c, "SECTION A: PERSONAL DETAILS", y)
    y = row(c, "Full Name / Imie i Nazwisko:", FULL_NAME, y, hi=True)
    y = row(c, "Date of Birth / Data urodzenia:", DOB, y)
    y = row(c, "Age / Wiek:", str(AGE) + " years  [Stage 0: PASS - within 18-75 range]", y, hi=True)
    y = row(c, "PESEL Number:", PESEL + "  [Stage 0: checksum algorithm PASS]", y, hi=True)
    y = row(c, "National ID / Dowod Osobisty:", ID_NUM, y)
    y = row(c, "ID Expiry / Data waznosci:", ID_EXPIRY + "  [Stage 0: PASS - expires 2030]", y, hi=True)
    y = row(c, "Address / Adres zamieszkania:", ADDRESS, y, hi=True)
    y = row(c, "Phone / Telefon:", "+48 601 234 567", y)
    y = row(c, "Email:", "piotr.nowak@gmail.com", y)
    y -= 0.3*cm
    y = sec(c, "SECTION B: EMPLOYMENT AND INCOME", y)
    y = row(c, "Employer / Pracodawca:", EMPLOYER, y, hi=True)
    y = row(c, "Contract / Rodzaj umowy:", CONTRACT, y, hi=True)
    y = row(c, "Employment Start:", EMP_START + "  [7 years tenure - stability PASS]", y)
    y = row(c, "Net Monthly Income:", NET_SAL + " PLN  [Stage 3: income > 3500 PLN pivot -> DTI cap 50%]", y, hi=True)
    y = row(c, "Bank Account / Rachunek:", BANK_ACC, y, hi=True)
    y -= 0.3*cm
    y = sec(c, "SECTION C: LOAN REQUEST", y)
    y = row(c, "Loan Amount / Kwota kredytu:", LOAN_AMT + " PLN  [within Stage 4 Standard 5000 PLN limit]", y, hi=True)
    y = row(c, "Loan Term / Okres kredytu:", LOAN_WEEKS + " weeks", y)
    y = row(c, "Purpose / Cel:", PURPOSE, y)
    y = footer_badge(c, y - 0.5*cm, [
        "STAGE 0: Age 41 PASS | PESEL checksum PASS | ID valid until 2030 PASS | No PEP/AML flag PASS",
        "STAGE 1: Name 'Piotr Nowak' - will be verified against all supporting documents",
        "STAGE 3: Declared income 5500 PLN - will be verified via payslip and bank statement"
    ], GRN)
    footer(c)
    c.save()
    print("Generated: " + str(path))

# ===== DOC 2: NATIONAL ID =====
def gen_id():
    path = OUT_DIR / (APP_ID + "_2_dowod_osobisty.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    page_header(c, "DOWOD OSOBISTY / NATIONAL IDENTITY CARD", "Polish government-issued ID - Stage 0 verification", TEAL)
    y = h - 5.8*cm
    y = sec(c, "IDENTITY DOCUMENT", y, TEAL)
    c.setFillColor(HexColor("#e3f2fd"))
    c.rect(2*cm, y - 5.5*cm, w - 4*cm, 5.5*cm, fill=1, stroke=1)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.5*cm, y - 0.7*cm, "RZECZPOSPOLITA POLSKA - DOWOD OSOBISTY")
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.5*cm, y - 1.5*cm, "Imie i Nazwisko / Full Name:  " + FULL_NAME)
    c.setFont("Helvetica", 9)
    c.drawString(2.5*cm, y - 2.1*cm, "Data urodzenia / Date of Birth:  " + DOB)
    c.drawString(2.5*cm, y - 2.7*cm, "Nr PESEL:  " + PESEL)
    c.drawString(2.5*cm, y - 3.3*cm, "Nr dokumentu / Document No:  " + ID_NUM)
    c.drawString(2.5*cm, y - 3.9*cm, "Adres zameldowania:  " + ADDRESS)
    c.setFillColor(GRN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.5*cm, y - 4.7*cm, "Data waznosci / Expiry:  " + ID_EXPIRY + "  [STATUS: VALID - NOT EXPIRED]")
    y -= 6.5*cm
    y = footer_badge(c, y, [
        "STAGE 0 RULE 0.1: Age 41 - within 18-75 range [PASS]",
        "STAGE 0 RULE 0.1b: PESEL " + PESEL + " - checksum algorithm verified [PASS]",
        "STAGE 0 RULE 0.2: ID expires 2030-03-22 - document is VALID and NOT EXPIRED [PASS]",
        "STAGE 0 RULE 0.3: Name 'Piotr Nowak' - no PEP/AML sanction list match [PASS]",
        "STAGE 1 RULE 1.2: Name on ID matches loan application exactly [PASS]"
    ], TEAL)
    footer(c)
    c.save()
    print("Generated: " + str(path))

# ===== DOC 3: PAYSLIP =====
def gen_payslip():
    path = OUT_DIR / (APP_ID + "_3_pasek_wynagrodzen.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    PAY_COLOR = HexColor("#1a5276")
    page_header(c, "PASEK WYNAGRODZEN / PAYSLIP - JUNE 2025", "Monthly salary statement - Stage 1 and 3 verification", PAY_COLOR)
    y = h - 5.8*cm
    y = sec(c, "EMPLOYER / PRACODAWCA", y, PAY_COLOR)
    y = row(c, "Pracodawca:", EMPLOYER, y, hi=True)
    y = row(c, "NIP pracodawcy:", "6762397379", y)
    y = row(c, "Adres:", "ul. Jana Pawla II 39a, 31-864 Krakow", y)
    y -= 0.3*cm
    y = sec(c, "EMPLOYEE / PRACOWNIK", y, PAY_COLOR)
    y = row(c, "Imie i Nazwisko:", FULL_NAME + "  [MATCHES loan application - Stage 1 PASS]", y, hi=True)
    y = row(c, "PESEL:", PESEL, y)
    y = row(c, "Rodzaj umowy:", CONTRACT, y, hi=True)
    y = row(c, "Zatrudniony od:", EMP_START + "  [tenure: 7 years - stability bonus]", y, hi=True)
    y -= 0.3*cm
    y = sec(c, "SALARY BREAKDOWN - CZERWIEC 2025", y, PAY_COLOR)
    y = row(c, "Wynagrodzenie brutto:", GROSS_SAL + " PLN", y)
    y = row(c, "Skladki ZUS pracownik:", "974.52 PLN", y)
    y = row(c, "Zaliczka na podatek:", "725.48 PLN", y)
    c.setFillColor(HexColor("#e8f5e9"))
    c.rect(1.5*cm, y - 3, w - 3*cm, 0.75*cm, fill=1, stroke=1)
    c.setFillColor(PAY_COLOR)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Wynagrodzenie NETTO / NET SALARY:  " + NET_SAL + " PLN")
    y -= 1.1*cm
    c.setFillColor(black)
    y = row(c, "Nr rachunku bankowego:", BANK_ACC, y, hi=True)
    y = footer_badge(c, y - 0.5*cm, [
        "STAGE 1: Name '" + FULL_NAME + "' matches loan application [PASS]",
        "STAGE 2: Salary tag 'Comarch SA' - consistent 3-month income pattern [BIK Prime simulation PASS]",
        "STAGE 3: Net income 5500 PLN > 3500 PLN pivot -> DTI cap = 50%  |  Proposed payment 333 PLN/mo",
        "DTI = (5500 x 15% + 333) / 5500 = 21.1%  [WELL WITHIN 50% CAP - PASS]",
        "Anti-usury check: 4000 PLN x 5% + 4000 x (90/365) x 20% = 397 PLN cap - fees within limit [PASS]"
    ], PAY_COLOR)
    footer(c)
    c.save()
    print("Generated: " + str(path))


# ===== DOC 4: PROOF OF ADDRESS =====
def gen_address():
    path = OUT_DIR / (APP_ID + "_4_faktura_adresowa.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    ADDR_COLOR = HexColor("#6c3483")
    page_header(c, "FAKTURA ZA GAZ / UTILITY BILL - PROOF OF ADDRESS", "PGNiG gas bill June 2025 - address verification", ADDR_COLOR)
    y = h - 5.8*cm
    y = sec(c, "SUPPLIER / DOSTAWCA", y, ADDR_COLOR)
    y = row(c, "Firma:", "PGNiG Obrot Detaliczny sp. z o.o.", y)
    y = row(c, "NIP:", "5272654827", y)
    y = row(c, "Adres:", "ul. Marcina Kasprzaka 25C, 01-224 Warszawa", y)
    y -= 0.3*cm
    y = sec(c, "CUSTOMER / ODBIORCA", y, ADDR_COLOR)
    y = row(c, "Imie i Nazwisko:", FULL_NAME + "  [MATCHES loan application - Stage 1 PASS]", y, hi=True)
    y = row(c, "Adres dostawy:", ADDRESS + "  [MATCHES loan application - no discrepancy]", y, hi=True)
    y = row(c, "Nr klienta:", "GZ-2847391-KRK", y)
    y -= 0.3*cm
    y = sec(c, "INVOICE DETAILS - CZERWIEC 2025", y, ADDR_COLOR)
    y = row(c, "Okres rozliczeniowy:", "01.06.2025 - 30.06.2025", y)
    y = row(c, "Zuzycie gazu:", "42.3 m3", y)
    y = row(c, "Kwota netto:", "187.45 PLN", y)
    y = row(c, "VAT (23%):", "43.11 PLN", y)
    y = row(c, "Do zaplaty:", "230.56 PLN", y)
    y = footer_badge(c, y - 0.5*cm, [
        "STAGE 1 RULE 1.2: Name '" + FULL_NAME + "' matches across all documents [PASS]",
        "CROSS-REFERENCE: Address '" + ADDRESS + "' matches loan declaration [NO DISCREPANCY]",
        "BIG REGISTRY SIMULATION: No overdue utility bills > 500 PLN | No KRD/ERIF entries [PASS]"
    ], ADDR_COLOR)
    footer(c)
    c.save()
    print("Generated: " + str(path))


# ===== DOC 5: BANK STATEMENT =====
def gen_bank():
    path = OUT_DIR / (APP_ID + "_5_wyciag_bankowy.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    BANK_COLOR = HexColor("#e05206")
    page_header(c, "WYCIAG Z KONTA / BANK STATEMENT", "ING Bank Slaski - April to June 2025 - PSD2 Open Banking", BANK_COLOR)
    y = h - 5.8*cm
    y = sec(c, "ACCOUNT HOLDER / POSIADACZ KONTA", y, BANK_COLOR)
    y = row(c, "Imie i Nazwisko:", FULL_NAME, y, hi=True)
    y = row(c, "Nr rachunku:", BANK_ACC, y, hi=True)
    y = row(c, "Bank:", "ING Bank Slaski S.A.", y)
    y -= 0.3*cm
    y = sec(c, "TRANSACTIONS / TRANSAKCJE (3-month salary verification)", y, BANK_COLOR)
    # Table header
    c.setFillColor(BANK_COLOR)
    c.rect(1.5*cm, y - 0.55*cm, w - 3*cm, 0.55*cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(2*cm, y - 0.38*cm, "DATE")
    c.drawString(4.5*cm, y - 0.38*cm, "DESCRIPTION / OPIS")
    c.drawString(12*cm, y - 0.38*cm, "AMOUNT (PLN)")
    c.drawString(16*cm, y - 0.38*cm, "BALANCE")
    y -= 0.75*cm
    txns = [
        ("2025-04-28", "WYNAGRODZENIE - Comarch SA [Stage 2 salary tag]", "+5,500.00", "8,234.50"),
        ("2025-04-30", "ZUS / Social insurance deduction", "-120.00", "8,114.50"),
        ("2025-05-05", "Czynsz / Rent - ul. Krakowska", "-1,200.00", "6,914.50"),
        ("2025-05-28", "WYNAGRODZENIE - Comarch SA [Stage 2 salary tag]", "+5,500.00", "11,234.50"),
        ("2025-05-30", "ZUS / Social insurance deduction", "-120.00", "11,114.50"),
        ("2025-06-05", "Czynsz / Rent - ul. Krakowska", "-1,200.00", "9,914.50"),
        ("2025-06-15", "Zakupy / Regular shopping", "-345.20", "9,569.30"),
        ("2025-06-28", "WYNAGRODZENIE - Comarch SA [Stage 2 salary tag]", "+5,500.00", "14,569.30"),
        ("2025-06-30", "ZUS / Social insurance deduction", "-120.00", "14,449.30"),
    ]
    for i, (d, desc, amt, bal) in enumerate(txns):
        if i % 2 == 0:
            c.setFillColor(HexColor("#fff8f0"))
            c.rect(1.5*cm, y - 3, w - 3*cm, 0.52*cm, fill=1, stroke=0)
        c.setFillColor(GRN if amt.startswith("+") else HexColor("#c0392b"))
        c.setFont("Helvetica-Bold", 7)
        c.drawString(2*cm, y, d)
        c.setFillColor(black)
        c.setFont("Helvetica", 7)
        c.drawString(4.5*cm, y, desc[:45])
        c.setFillColor(GRN if amt.startswith("+") else HexColor("#c0392b"))
        c.setFont("Helvetica-Bold", 7)
        c.drawString(12*cm, y, amt)
        c.setFillColor(black)
        c.setFont("Helvetica", 7)
        c.drawString(16*cm, y, bal)
        y -= 0.6*cm
    y = footer_badge(c, y - 0.3*cm, [
        "STAGE 2: 'WYNAGRODZENIE - Comarch SA' detected 3 consecutive months [BIK Prime simulation PASS]",
        "STAGE 2: No overdue payments | Zero BIG/KRD debt entries | BIK score 75+ simulated [PASS]",
        "STAGE 3: 3-month rolling average 5500 PLN MATCHES declared income [PASS - no income discrepancy]",
        "STAGE 4: BIK Prime (>70) + BIG debt 0 PLN + DTI 21% < 50% -> APPROVE AND UPSELL [PASS]"
    ], BANK_COLOR)
    footer(c)
    c.save()
    print("Generated: " + str(path))


# ===== MAIN =====
if __name__ == "__main__":
    print("\nGenerating DEMO-PL-PRIME-001 - All 5 stages PASS test case...")
    gen_loan_app()
    gen_id()
    gen_payslip()
    gen_address()
    gen_bank()
    print("\n5 documents generated in: " + str(OUT_DIR))
    print("\n--- DEMO-PL-PRIME-001 PROFILE ---")
    print("Applicant       : Piotr Nowak")
    print("DOB             : 1984-03-22  (Age 41)")
    print("PESEL           : " + PESEL)
    print("ID Expiry       : " + ID_EXPIRY + " (valid)")
    print("Employer        : Comarch SA (permanent, 7yr tenure)")
    print("Net Salary      : 5500 PLN  (above 3500 PLN pivot)")
    print("Loan Request    : 4000 PLN / 52 weeks")
    print("Expected DTI    : 21%  (cap: 50%)")
    print("Stage 0         : PASS - age, PESEL, non-expired ID, no PEP")
    print("Stage 1         : PASS - name consistent across all 5 documents")
    print("Stage 2         : PASS - BIK Prime 75+, BIG debt 0 PLN")
    print("Stage 3         : PASS - DTI 21% under 50% cap, cost cap met")
    print("Stage 4         : APPROVE AND UPSELL (Prime product route)")
    print("\nUpload to Admin Portal as application ID: DEMO-PL-PRIME-001")
    print("Document types: 1=loan_application, 2=identity_card, 3=income_proof, 4=proof_of_address, 5=bank_statement")
