"""
DEMO-PL-PRIME-002: Mid-Market customer - all 5 stages PASS, outcome: APPROVE STANDARD
Applicant: Anna Wojcik - Mid-market BIK band (46-70), clean record, good DTI
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, black, white

OUT_DIR = Path("test-data/demo-cases/generated")
OUT_DIR.mkdir(parents=True, exist_ok=True)

APP_ID = "DEMO-PL-PRIME-002"
FULL_NAME = "Anna Wojcik"
DOB = "1990-07-14"
AGE = 35
PESEL = "90071456789"
ID_NUM = "BKP 334812"
ID_EXPIRY = "2031-07-14"
ADDRESS = "ul. Florianska 22/3, 31-021 Krakow"
EMPLOYER = "Tesco Polska sp. z o.o."
CONTRACT = "Umowa o prace na czas nieokreslony"
EMP_START = "2020-02-01"
NET_SAL = "4200.00"
GROSS_SAL = "5500.00"
BANK_ACC = "PL82 1140 2004 0000 3102 7659 1234"
LOAN_AMT = "3500.00"
LOAN_WEEKS = "40"
PURPOSE = "Zakup sprzetu AGD"

HDR = HexColor("#003189")
GRN = HexColor("#28A745")
BLU = HexColor("#0277bd")

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
    c.drawString(2*cm, h - 3.8*cm, "Application ID: " + APP_ID + "  |  Market: Poland (PL)  |  Product: Standard Home Credit")
    c.setFillColor(BLU)
    c.rect(0, h - 5.2*cm, w, 0.9*cm, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(2*cm, h - 4.85*cm, "[DEMO-PL-PRIME-002] All 5 decisioning stages PASS | Expected: APPROVE STANDARD | Mid-Market BIK band 46-70")

def row(c, label, value, y, hi=False):
    w = A4[0]
    if hi:
        c.setFillColor(HexColor("#e3f2fd"))
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

def gen_loan_app():
    path = OUT_DIR / (APP_ID + "_1_loan_application.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    page_header(c, "LOAN APPLICATION FORM / WNIOSEK KREDYTOWY", "Customer self-declaration - all fields consistent", HDR)
    y = h - 5.8*cm
    y = sec(c, "SECTION A: PERSONAL DETAILS", y)
    y = row(c, "Full Name / Imie i Nazwisko:", FULL_NAME, y, hi=True)
    y = row(c, "Date of Birth / Data urodzenia:", DOB, y)
    y = row(c, "Age / Wiek:", str(AGE) + " years  [Stage 0: PASS - within 18-75]", y, hi=True)
    y = row(c, "PESEL Number:", PESEL + "  [Stage 0: checksum PASS]", y, hi=True)
    y = row(c, "National ID / Dowod Osobisty:", ID_NUM, y)
    y = row(c, "ID Expiry / Data waznosci:", ID_EXPIRY + "  [Stage 0: PASS - expires 2031]", y, hi=True)
    y = row(c, "Address / Adres zamieszkania:", ADDRESS, y, hi=True)
    y = row(c, "Phone / Telefon:", "+48 512 876 543", y)
    y = row(c, "Email:", "anna.wojcik@wp.pl", y)
    y -= 0.3*cm
    y = sec(c, "SECTION B: EMPLOYMENT AND INCOME", y)
    y = row(c, "Employer / Pracodawca:", EMPLOYER, y, hi=True)
    y = row(c, "Contract / Rodzaj umowy:", CONTRACT, y, hi=True)
    y = row(c, "Employment Start:", EMP_START + "  [5 years tenure]", y)
    y = row(c, "Net Monthly Income:", NET_SAL + " PLN  [Stage 3: income > 3500 PLN -> DTI cap 50%]", y, hi=True)
    y = row(c, "Bank Account / Rachunek:", BANK_ACC, y, hi=True)
    y -= 0.3*cm
    y = sec(c, "SECTION C: LOAN REQUEST", y)
    y = row(c, "Loan Amount / Kwota kredytu:", LOAN_AMT + " PLN  [within Standard 5000 PLN limit]", y, hi=True)
    y = row(c, "Loan Term / Okres kredytu:", LOAN_WEEKS + " weeks", y)
    y = row(c, "Purpose / Cel:", PURPOSE, y)
    y = footer_badge(c, y - 0.5*cm, [
        "STAGE 0: Age 35 PASS | PESEL checksum PASS | ID valid until 2031 PASS | No PEP flag PASS",
        "STAGE 1: Name 'Anna Wojcik' - consistent across all supporting documents",
        "STAGE 3: Net income 4200 PLN (>3500 PLN pivot) -> DTI cap 50% | Proposed payment 87.50 PLN/wk"
    ], GRN)
    footer(c)
    c.save()
    print("Generated: " + str(path))


def gen_id():
    path = OUT_DIR / (APP_ID + "_2_dowod_osobisty.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    TEAL = HexColor("#0d7377")
    page_header(c, "DOWOD OSOBISTY / NATIONAL IDENTITY CARD", "Polish government-issued ID", TEAL)
    y = h - 5.8*cm
    y = sec(c, "IDENTITY DOCUMENT / DOKUMENT TOZSAMOSCI", y, TEAL)
    c.setFillColor(HexColor("#e0f7fa"))
    c.rect(2*cm, y - 5.5*cm, w - 4*cm, 5.5*cm, fill=1, stroke=1)
    c.setFillColor(TEAL)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2.5*cm, y - 0.7*cm, "RZECZPOSPOLITA POLSKA - DOWOD OSOBISTY")
    c.setFillColor(black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.5*cm, y - 1.5*cm, "Imie i Nazwisko:  " + FULL_NAME)
    c.setFont("Helvetica", 9)
    c.drawString(2.5*cm, y - 2.1*cm, "Data urodzenia:  " + DOB)
    c.drawString(2.5*cm, y - 2.7*cm, "Nr PESEL:  " + PESEL)
    c.drawString(2.5*cm, y - 3.3*cm, "Nr dokumentu:  " + ID_NUM)
    c.drawString(2.5*cm, y - 3.9*cm, "Adres zameldowania:  " + ADDRESS)
    c.setFillColor(GRN)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.5*cm, y - 4.7*cm, "Data waznosci / Expiry:  " + ID_EXPIRY + "  [STATUS: VALID - NOT EXPIRED]")
    y -= 6.5*cm
    y = footer_badge(c, y, [
        "STAGE 0 RULE 0.1: Age 35 within 18-75 [PASS]",
        "STAGE 0 RULE 0.1b: PESEL " + PESEL + " format verified [PASS]",
        "STAGE 0 RULE 0.2: ID expires 2031-07-14 - document VALID [PASS]",
        "STAGE 0 RULE 0.3: Name 'Anna Wojcik' - no PEP/AML flag [PASS]",
        "STAGE 1 RULE 1.2: Name on ID MATCHES loan application [PASS]"
    ], TEAL)
    footer(c)
    c.save()
    print("Generated: " + str(path))


def gen_payslip():
    path = OUT_DIR / (APP_ID + "_3_pasek_wynagrodzen.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    PAY_COLOR = HexColor("#1565c0")
    page_header(c, "PASEK WYNAGRODZEN / PAYSLIP - JUNE 2025", "Monthly salary - Stage 1 name match and Stage 3 income verification", PAY_COLOR)
    y = h - 5.8*cm
    y = sec(c, "EMPLOYER / PRACODAWCA", y, PAY_COLOR)
    y = row(c, "Pracodawca:", EMPLOYER, y, hi=True)
    y = row(c, "NIP:", "5260204822", y)
    y = row(c, "Adres:", "ul. Kapelanka 54, 30-347 Krakow", y)
    y -= 0.3*cm
    y = sec(c, "EMPLOYEE / PRACOWNIK", y, PAY_COLOR)
    y = row(c, "Imie i Nazwisko:", FULL_NAME + "  [MATCHES loan application - Stage 1 PASS]", y, hi=True)
    y = row(c, "PESEL:", PESEL, y)
    y = row(c, "Rodzaj umowy:", CONTRACT, y, hi=True)
    y = row(c, "Zatrudniony od:", EMP_START + "  [5 years tenure]", y, hi=True)
    y -= 0.3*cm
    y = sec(c, "SALARY BREAKDOWN - CZERWIEC 2025", y, PAY_COLOR)
    y = row(c, "Wynagrodzenie brutto:", GROSS_SAL + " PLN", y)
    y = row(c, "Skladki ZUS pracownik:", "745.20 PLN", y)
    y = row(c, "Zaliczka na podatek:", "554.80 PLN", y)
    c.setFillColor(HexColor("#e3f2fd"))
    c.rect(1.5*cm, y - 3, w - 3*cm, 0.75*cm, fill=1, stroke=1)
    c.setFillColor(PAY_COLOR)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(2*cm, y, "Wynagrodzenie NETTO / NET SALARY:  " + NET_SAL + " PLN")
    y -= 1.1*cm
    c.setFillColor(black)
    y = row(c, "Nr rachunku bankowego:", BANK_ACC, y, hi=True)
    y = footer_badge(c, y - 0.5*cm, [
        "STAGE 1: Name 'Anna Wojcik' matches loan application [PASS]",
        "STAGE 2: Salary from 'Tesco Polska' - 3-month consistent pattern [BIK mid-market simulation PASS]",
        "STAGE 3: Net 4200 PLN > 3500 PLN pivot -> DTI cap = 50%",
        "DTI = (4200 x 15% + 291) / 4200 = 21.9%  [WELL WITHIN 50% CAP - PASS]",
        "Anti-usury check: 3500 PLN x 5% + 3500 x (90/365) x 20% = 347 PLN cap - fees within limit [PASS]"
    ], PAY_COLOR)
    footer(c)
    c.save()
    print("Generated: " + str(path))


def gen_address():
    path = OUT_DIR / (APP_ID + "_4_faktura_adresowa.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    ADDR_COLOR = HexColor("#558b2f")
    page_header(c, "FAKTURA ZA PRAD / ELECTRICITY BILL - PROOF OF ADDRESS", "Tauron PE bill June 2025", ADDR_COLOR)
    y = h - 5.8*cm
    y = sec(c, "SUPPLIER / DOSTAWCA", y, ADDR_COLOR)
    y = row(c, "Firma:", "TAURON Polska Energia S.A.", y)
    y = row(c, "NIP:", "9542583988", y)
    y = row(c, "Adres:", "ul. ks. Piotra Skargi 45, 40-950 Katowice", y)
    y -= 0.3*cm
    y = sec(c, "CUSTOMER / ODBIORCA", y, ADDR_COLOR)
    y = row(c, "Imie i Nazwisko:", FULL_NAME + "  [MATCHES loan application - Stage 1 PASS]", y, hi=True)
    y = row(c, "Adres obiektu:", ADDRESS + "  [MATCHES loan application - no discrepancy]", y, hi=True)
    y = row(c, "Nr klienta:", "TP-48291736-KRK", y)
    y -= 0.3*cm
    y = sec(c, "INVOICE DETAILS - CZERWIEC 2025", y, ADDR_COLOR)
    y = row(c, "Okres rozliczeniowy:", "01.06.2025 - 30.06.2025", y)
    y = row(c, "Zuzycie energii:", "138.4 kWh", y)
    y = row(c, "Kwota netto:", "95.20 PLN", y)
    y = row(c, "VAT (23%):", "21.90 PLN", y)
    y = row(c, "Do zaplaty:", "117.10 PLN", y)
    y = footer_badge(c, y - 0.5*cm, [
        "STAGE 1 RULE 1.2: Name 'Anna Wojcik' matches across all documents [PASS]",
        "CROSS-REFERENCE: Address '" + ADDRESS + "' MATCHES declaration [NO DISCREPANCY]",
        "BIG REGISTRY: No overdue utility bills > 500 PLN | Zero KRD/ERIF entries [PASS]"
    ], ADDR_COLOR)
    footer(c)
    c.save()
    print("Generated: " + str(path))


def gen_bank():
    path = OUT_DIR / (APP_ID + "_5_wyciag_bankowy.pdf")
    c = canvas.Canvas(str(path), pagesize=A4)
    w, h = A4
    BANK_COLOR = HexColor("#6a1b9a")
    page_header(c, "WYCIAG Z KONTA / BANK STATEMENT", "mBank S.A. - April to June 2025 - PSD2 Open Banking", BANK_COLOR)
    y = h - 5.8*cm
    y = sec(c, "ACCOUNT HOLDER / POSIADACZ KONTA", y, BANK_COLOR)
    y = row(c, "Imie i Nazwisko:", FULL_NAME, y, hi=True)
    y = row(c, "Nr rachunku:", BANK_ACC, y, hi=True)
    y = row(c, "Bank:", "mBank S.A.", y)
    y -= 0.3*cm
    y = sec(c, "TRANSACTIONS - 3-month salary verification", y, BANK_COLOR)
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
        ("2025-04-25", "WYNAGRODZENIE - Tesco Polska [salary tag]", "+4,200.00", "5,843.20"),
        ("2025-04-30", "ZUS emerytalny", "-98.40", "5,744.80"),
        ("2025-05-05", "Czynsz / Rent - Florianska", "-1,100.00", "4,644.80"),
        ("2025-05-25", "WYNAGRODZENIE - Tesco Polska [salary tag]", "+4,200.00", "8,284.80"),
        ("2025-05-30", "ZUS emerytalny", "-98.40", "8,186.40"),
        ("2025-06-05", "Czynsz / Rent - Florianska", "-1,100.00", "7,086.40"),
        ("2025-06-12", "Zakupy spozywcze / Groceries", "-287.60", "6,798.80"),
        ("2025-06-25", "WYNAGRODZENIE - Tesco Polska [salary tag]", "+4,200.00", "10,498.80"),
        ("2025-06-30", "ZUS emerytalny", "-98.40", "10,400.40"),
    ]
    for i, (d, desc, amt, bal) in enumerate(txns):
        if i % 2 == 0:
            c.setFillColor(HexColor("#f3e5f5"))
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
        "STAGE 2: 'WYNAGRODZENIE - Tesco Polska' detected 3 consecutive months [BIK mid-market PASS]",
        "STAGE 2: No overdue payments | Zero BIG/KRD entries | BIK score 55 (mid-market band 46-70) [PASS]",
        "STAGE 3: 3-month avg 4200 PLN MATCHES declared income [PASS - no discrepancy]",
        "STAGE 4: BIK 55 + BIG debt 0 PLN + DTI 21.9% < 45% -> APPROVE STANDARD up to 5000 PLN [PASS]"
    ], BANK_COLOR)
    footer(c)
    c.save()
    print("Generated: " + str(path))


if __name__ == "__main__":
    print("\nGenerating DEMO-PL-PRIME-002 - Mid-Market all 5 stages PASS...")
    gen_loan_app()
    gen_id()
    gen_payslip()
    gen_address()
    gen_bank()
    print("\n5 documents generated in: " + str(OUT_DIR))
    print("\n--- DEMO-PL-PRIME-002 PROFILE ---")
    print("Applicant       : Anna Wojcik")
    print("DOB             : 1990-07-14  (Age 35)")
    print("PESEL           : " + PESEL)
    print("ID Expiry       : " + ID_EXPIRY + " (valid)")
    print("Employer        : Tesco Polska (permanent, 5yr tenure)")
    print("Net Salary      : 4200 PLN  (above 3500 PLN pivot)")
    print("Loan Request    : 3500 PLN / 40 weeks")
    print("Expected DTI    : 21.9%  (cap: 50%)")
    print("Stage 0         : PASS - age 35, PESEL, non-expired ID 2031, no PEP")
    print("Stage 1         : PASS - name consistent across all 5 documents")
    print("Stage 2         : PASS - BIK mid-market 55, BIG debt 0 PLN")
    print("Stage 3         : PASS - DTI 21.9% under 50% cap, cost cap met")
    print("Stage 4         : APPROVE STANDARD (Mid-market product route)")
    print("\nUpload as: DEMO-PL-PRIME-002")
    print("Doc types: 1=loan_application, 2=identity_card, 3=income_proof, 4=proof_of_address, 5=bank_statement")
