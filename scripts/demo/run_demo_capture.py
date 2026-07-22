"""
IPF IPA PoC - Automated Demo Walkthrough
Captures screenshots of each step using Selenium + Chrome WebDriver.
Produces: scripts/demo/screenshots/ and scripts/demo/IPF_IPA_Demo.pdf

Prerequisites:
  - All 4 services running (backend:8000, admin:8501, reviewer:8502, assessor:8503)
  - Chrome browser installed
  - Run: python scripts/demo/run_demo_capture.py

Output: screenshots saved to scripts/demo/screenshots/
        PDF deck: scripts/demo/IPF_IPA_Demo.pdf
"""
import time, os, requests, json
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black

BACKEND = "http://localhost:8000"
ADMIN_URL = "http://localhost:8501"
REVIEWER_URL = "http://localhost:8502"
ASSESSOR_URL = "http://localhost:8503"

OUT_DIR = Path("scripts/demo/screenshots")
OUT_DIR.mkdir(parents=True, exist_ok=True)
PDF_OUT = Path("scripts/demo/IPF_IPA_Demo.pdf")

# Demo application ID - use a fresh one
DEMO_APP_ID = "DEMO-PRESENTATION-001"

DEMO_STEPS = [
    {"id": "01_admin_login",       "title": "Admin Portal - Login",          "url": ADMIN_URL,      "desc": "Back-office administrators securely log in to upload customer documents"},
    {"id": "02_admin_upload",      "title": "Step 1 - Upload Loan Application","url": ADMIN_URL,     "desc": "Upload the customer signed loan application form as the reference document"},
    {"id": "03_admin_processing",  "title": "AI Processing Started",          "url": ADMIN_URL,      "desc": "AI extraction begins automatically - no manual trigger needed"},
    {"id": "04_reviewer_login",    "title": "Document Reviewer Portal",       "url": REVIEWER_URL,   "desc": "Document reviewers have a separate portal focused on verification"},
    {"id": "05_work_queue",        "title": "Work Queue - Documents Pending", "url": REVIEWER_URL,   "desc": "All documents requiring human review are queued automatically"},
    {"id": "06_app_review_panel_a","title": "Panel A - Loan Application",     "url": REVIEWER_URL,   "desc": "Declared fields from loan form with cross-reference status indicators"},
    {"id": "07_app_review_panel_b","title": "Panel B - OCR Extractions",      "url": REVIEWER_URL,   "desc": "Each supporting document with extracted fields and confidence scores"},
    {"id": "08_app_review_panel_c","title": "Panel C - Discrepancy Report",   "url": REVIEWER_URL,   "desc": "Automated cross-reference flags any inconsistencies between documents"},
    {"id": "09_audit_trail",       "title": "Audit Trail & Pipeline Flow",    "url": REVIEWER_URL,   "desc": "Full event history with colour-coded processing pipeline flowchart"},
    {"id": "10_assessor_login",    "title": "Credit Assessor Portal",         "url": ASSESSOR_URL,   "desc": "Dedicated portal for qualified credit decision makers - clean interface"},
    {"id": "11_assessor_queue",    "title": "Decision Queue",                 "url": ASSESSOR_URL,   "desc": "Applications ready for credit decision, showing score and risk level"},
    {"id": "12_app_summary",       "title": "Application Summary",            "url": ASSESSOR_URL,   "desc": "One-page summary: applicant details, credit score, discrepancies"},
    {"id": "13_credit_score",      "title": "Credit Score Assessment",        "url": ASSESSOR_URL,   "desc": "Mock bureau scoring across PL/RO/HU/CZ markets with risk breakdown"},
    {"id": "14_loan_decision",     "title": "Loan Decision",                  "url": ASSESSOR_URL,   "desc": "Assessor approves or declines - AI NEVER auto-approves any loan"},
    {"id": "15_conflict_scenario", "title": "Conflict Scenario - Flagged",    "url": REVIEWER_URL,   "desc": "Income overstatement detected - 15.3% variance flagged as HIGH risk"},
]


def setup_driver():
    opts = Options()
    opts.add_argument("--window-size=1440,900")
    opts.add_argument("--start-maximized")
    # Try to find Chrome/Edge
    for path in [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]:
        if os.path.exists(path):
            if "edge" in path.lower():
                from selenium.webdriver.edge.options import Options as EdgeOptions
                from selenium import webdriver as wd
                eopts = EdgeOptions()
                eopts.add_argument("--window-size=1440,900")
                driver = wd.Edge(options=eopts)
            else:
                opts.binary_location = path
                driver = webdriver.Chrome(options=opts)
            print(f"Using browser: {path}")
            return driver
    # Default Chrome
    driver = webdriver.Chrome(options=opts)
    return driver


def add_overlay(screenshot_path, title, desc, step_num, total):
    """Add professional title bar overlay to screenshot."""
    img = Image.open(screenshot_path).convert("RGB")
    w, h = img.size

    # Add header bar
    draw = ImageDraw.Draw(img)
    bar_h = 70
    draw.rectangle([0, 0, w, bar_h], fill=(13, 115, 119))

    try:
        font_title = ImageFont.truetype("arial.ttf", 22)
        font_step  = ImageFont.truetype("arial.ttf", 14)
        font_desc  = ImageFont.truetype("arial.ttf", 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_step  = font_title
        font_desc  = font_title

    draw.text((20, 10), f"IPF Intelligent Process Automation - PoC Demo", fill="white", font=font_title)
    draw.text((20, 40), f"Step {step_num}/{total}: {title}", fill="#d4f5f3", font=font_step)

    # Add description bar at bottom
    desc_bar_h = 44
    draw.rectangle([0, h - desc_bar_h, w, h], fill=(30, 30, 30))
    draw.text((20, h - desc_bar_h + 12), desc, fill="#ffffff", font=font_desc)

    # Add step indicator dots
    dot_x = w - 160
    dot_y = bar_h + 10
    for i in range(total):
        colour = (13, 115, 119) if i < step_num else (200, 200, 200)
        if i == step_num - 1:
            colour = (255, 193, 7)
        draw.ellipse([dot_x + i * 9, dot_y, dot_x + i * 9 + 6, dot_y + 6], fill=colour)

    out_path = screenshot_path.parent / (screenshot_path.stem + "_overlay.png")
    img.save(out_path, quality=95)
    return out_path


def create_pdf(screenshot_paths):
    """Combine screenshots into a demo PDF."""
    width, height = landscape(A4)
    c = rl_canvas.Canvas(str(PDF_OUT), pagesize=landscape(A4))

    # Title page
    c.setFillColor(HexColor("#0d7377"))
    c.rect(0, 0, width, height, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width/2, height/2 + 40, "IPF Intelligent Process Automation")
    c.setFont("Helvetica", 20)
    c.drawCentredString(width/2, height/2, "Proof of Concept - Demo Walkthrough")
    c.setFont("Helvetica", 14)
    c.drawCentredString(width/2, height/2 - 40, "Mastek AI Centre of Excellence | July 2026 | CONFIDENTIAL")
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#d4f5f3"))
    features = [
        "Multi-agent AI pipeline: Document Extraction + Cross-Reference + Credit Scoring",
        "4 Markets: Poland, Romania, Hungary, Czech Republic",
        "Human-in-the-loop: AI recommends, humans always decide",
        "3 Role-based portals: Admin | Document Reviewer | Credit Assessor",
    ]
    for i, f in enumerate(features):
        c.drawCentredString(width/2, height/2 - 80 - i*20, f"- {f}")
    c.showPage()

    # Screenshot pages
    for path in screenshot_paths:
        if path.exists():
            img = Image.open(path)
            iw, ih = img.size
            aspect = iw / ih
            pw = width - 2*cm
            ph = pw / aspect
            if ph > height - 2*cm:
                ph = height - 2*cm
                pw = ph * aspect
            x = (width - pw) / 2
            y = (height - ph) / 2
            c.drawInlineImage(str(path), x, y, pw, ph)
            c.showPage()

    c.save()
    print(f"PDF created: {PDF_OUT}")


def main():
    print("=" * 60)
    print("IPF IPA PoC - Demo Screenshot Capture")
    print("=" * 60)

    # Pre-check services
    print("\nChecking services...")
    for name, url in [("Backend", f"{BACKEND}/api/health"),
                      ("Admin", ADMIN_URL),
                      ("Reviewer", REVIEWER_URL),
                      ("Assessor", ASSESSOR_URL)]:
        try:
            r = requests.get(url, timeout=5)
            print(f"  {name}: OK (HTTP {r.status_code})")
        except Exception as e:
            print(f"  {name}: FAILED - {e}")
            print(f"  Please start {name} before running this script")

    print(f"\nCapturing {len(DEMO_STEPS)} demo screenshots...")
    print("Screenshots will be saved to:", OUT_DIR)

    try:
        driver = setup_driver()
    except Exception as e:
        print(f"\nCould not start browser: {e}")
        print("Install ChromeDriver: https://chromedriver.chromium.org/")
        print("\nFalling back to API-only screenshots (no browser)...")
        create_api_screenshots()
        return

    overlay_paths = []

    try:
        for i, step in enumerate(DEMO_STEPS, 1):
            print(f"\n[{i}/{len(DEMO_STEPS)}] {step['title']}")

            # Navigate
            driver.get(step["url"])
            time.sleep(3)  # Wait for Streamlit to render

            # Take screenshot
            ss_path = OUT_DIR / f"{step['id']}.png"
            driver.save_screenshot(str(ss_path))
            print(f"  Screenshot: {ss_path.name}")

            # Add overlay
            overlay = add_overlay(ss_path, step["title"], step["desc"], i, len(DEMO_STEPS))
            overlay_paths.append(overlay)

            time.sleep(1)

    finally:
        driver.quit()

    print(f"\nCreating PDF deck...")
    create_pdf(overlay_paths)

    print("\n" + "=" * 60)
    print("DEMO CAPTURE COMPLETE")
    print(f"Screenshots: {OUT_DIR}/")
    print(f"PDF Deck:    {PDF_OUT}")
    print("=" * 60)
    print("\nTo share: send IPF_IPA_Demo.pdf to stakeholders")
    print("To record: Use Xbox Game Bar (Win+G) while running the demo")


def create_api_screenshots():
    """Fallback: create text-based screenshot cards using Pillow only."""
    print("\nGenerating API-based demo cards (no browser required)...")
    overlay_paths = []

    for i, step in enumerate(DEMO_STEPS, 1):
        img = Image.new("RGB", (1440, 900), color=(248, 249, 250))
        draw = ImageDraw.Draw(img)

        # Header
        draw.rectangle([0, 0, 1440, 80], fill=(13, 115, 119))
        try:
            font_h = ImageFont.truetype("arial.ttf", 26)
            font_b = ImageFont.truetype("arial.ttf", 18)
            font_s = ImageFont.truetype("arial.ttf", 14)
        except Exception:
            font_h = font_b = font_s = ImageFont.load_default()

        draw.text((20, 15), "IPF Intelligent Process Automation - PoC Demo", fill="white", font=font_h)
        draw.text((20, 50), f"Step {i}/{len(DEMO_STEPS)}: {step['title']}", fill="#d4f5f3", font=font_b)

        # Content area
        draw.rectangle([60, 120, 1380, 780], fill="white",
                       outline=(13, 115, 119), width=2)

        draw.text((80, 150), step["title"], fill=(13, 115, 119), font=font_h)
        draw.text((80, 210), f"URL: {step['url']}", fill=(100, 100, 100), font=font_s)
        draw.text((80, 260), step["desc"], fill=(50, 50, 50), font=font_b)

        # Mastek branding
        draw.rectangle([0, 860, 1440, 900], fill=(30, 30, 30))
        draw.text((20, 873), "Mastek AI Centre of Excellence | IPF IPA PoC | CONFIDENTIAL",
                  fill="white", font=font_s)

        path = OUT_DIR / f"{step['id']}_card.png"
        img.save(path)
        overlay_paths.append(path)
        print(f"  Card {i}: {path.name}")

    create_pdf(overlay_paths)


if __name__ == "__main__":
    main()
