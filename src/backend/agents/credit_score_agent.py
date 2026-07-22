"""
IPF IPA PoC - Mock Credit Scoring Agent
Simulates bureau-style credit scoring using extracted document data.
Covers: Poland (BIK), Romania (Biroul de Credit), Hungary (BISZ/KHR), Czech (CBCB)

Scoring model:
  - Income adequacy     (0-300 pts)
  - Employment stability (0-200 pts)
  - Identity validity   (0-200 pts)
  - Document consistency (0-200 pts)
  - Age/eligibility     (0-100 pts)
  Total: 0-1000 pts

Risk bands:
  800-1000: EXCELLENT  (green)
  650-799:  GOOD       (light green)
  500-649:  FAIR       (amber)
  350-499:  POOR       (orange)
  0-349:    HIGH RISK  (red)
"""
import re
from datetime import datetime, date
from typing import Optional


MARKET_THRESHOLDS = {
    "PL": {"min_income": 2500, "currency": "PLN", "bureau": "BIK (Mock)", "min_age": 18, "max_age": 70},
    "RO": {"min_income": 1500, "currency": "RON", "bureau": "Biroul de Credit (Mock)", "min_age": 18, "max_age": 70},
    "HU": {"min_income": 150000, "currency": "HUF", "bureau": "BISZ/KHR (Mock)", "min_age": 18, "max_age": 70},
    "CZ": {"min_income": 20000, "currency": "CZK", "bureau": "CBCB (Mock)", "min_age": 18, "max_age": 70},
}

RISK_BANDS = [
    (800, 1000, "EXCELLENT", "🟢", "#00C851"),
    (650, 799,  "GOOD",      "🟢", "#28a745"),
    (500, 649,  "FAIR",      "🟡", "#ffc107"),
    (350, 499,  "POOR",      "🟠", "#fd7e14"),
    (0,   349,  "HIGH RISK", "🔴", "#dc3545"),
]


def _parse_income(value_str: str) -> Optional[float]:
    if not value_str:
        return None
    try:
        clean = re.sub(r"[^\d.,]", "", str(value_str).replace(",", "."))
        # Handle formats like "5,230.00" or "5230.00"
        parts = clean.split(".")
        if len(parts) > 2:
            clean = "".join(parts[:-1]) + "." + parts[-1]
        return float(clean)
    except Exception:
        return None


def _parse_age(dob_str: str) -> Optional[int]:
    if not dob_str:
        return None
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        return (date.today() - dob).days // 365
    except Exception:
        return None


def _get_field(extractions: list, field_name: str) -> Optional[str]:
    for e in extractions:
        if e.get("field_name") == field_name:
            val = e.get("corrected_value") or e.get("extracted_value")
            if val and val not in ("None", "null", ""):
                return str(val)
    return None


def compute_credit_score(
    extractions: list,
    validations: list,
    market: str,
    declared_income: Optional[float] = None
) -> dict:
    """
    Compute a mock credit score from extracted document data.
    Returns a full scoring breakdown for display in the Credit Assessor UI.
    """
    thresholds = MARKET_THRESHOLDS.get(market, MARKET_THRESHOLDS["PL"])
    score = 0
    breakdown = []
    flags = []

    # --- 1. Income Adequacy (0-300 pts) ---
    income_str = (
        _get_field(extractions, "net_salary") or
        _get_field(extractions, "net_monthly_salary") or
        _get_field(extractions, "gross_salary") or
        ""
    )
    income_val = _parse_income(income_str) or declared_income
    min_inc = thresholds["min_income"]
    currency = thresholds["currency"]

    if income_val:
        if income_val >= min_inc * 3:
            pts = 300; label = f"High income ({income_val:,.0f} {currency})"
        elif income_val >= min_inc * 2:
            pts = 220; label = f"Good income ({income_val:,.0f} {currency})"
        elif income_val >= min_inc:
            pts = 140; label = f"Adequate income ({income_val:,.0f} {currency})"
        elif income_val >= min_inc * 0.7:
            pts = 70; label = f"Below threshold ({income_val:,.0f} {currency})"
            flags.append(f"Income {income_val:,.0f} {currency} below minimum {min_inc:,} {currency}")
        else:
            pts = 0; label = f"Income too low ({income_val:,.0f} {currency})"
            flags.append(f"Income significantly below minimum threshold")
        score += pts
        breakdown.append({"category": "Income Adequacy", "score": pts, "max": 300,
                          "detail": label, "pct": round(pts/300*100)})
    else:
        flags.append("Income data not available from documents")
        breakdown.append({"category": "Income Adequacy", "score": 0, "max": 300,
                          "detail": "Income not extracted", "pct": 0})

    # --- 2. Employment Stability (0-200 pts) ---
    employer = (
        _get_field(extractions, "employer_name") or
        _get_field(extractions, "employer_ico") or ""
    )
    contract_type = _get_field(extractions, "employment_type") or _get_field(extractions, "contract_type") or ""
    start_date_str = _get_field(extractions, "employment_start_date") or ""

    emp_score = 0
    emp_detail = []
    if employer:
        emp_score += 80; emp_detail.append(f"Employed at: {employer[:40]}")
    else:
        flags.append("Employment details not verified")
        emp_detail.append("No employer found in documents")

    if any(kw in contract_type.lower() for kw in ["neurcit", "nieokresl", "nedeterminat", "permanent", "indefinit", "hatarozatlan"]):
        emp_score += 80; emp_detail.append("Permanent contract")
    elif contract_type:
        emp_score += 40; emp_detail.append(f"Contract: {contract_type[:30]}")

    if start_date_str:
        try:
            start = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            years = (date.today() - start).days / 365
            if years >= 3:
                emp_score += 40; emp_detail.append(f"Tenure: {years:.1f} years")
            elif years >= 1:
                emp_score += 20; emp_detail.append(f"Tenure: {years:.1f} years")
        except Exception:
            pass

    emp_score = min(emp_score, 200)
    score += emp_score
    breakdown.append({"category": "Employment Stability", "score": emp_score, "max": 200,
                      "detail": "; ".join(emp_detail) if emp_detail else "Not assessed",
                      "pct": round(emp_score/200*100)})

    # --- 3. Identity Validity (0-200 pts) ---
    id_score = 0
    id_details = []

    # Check document expiry
    expiry_str = _get_field(extractions, "expiry_date")
    if expiry_str:
        val_result = next((v for v in validations if v.get("field_name") == "expiry_date"), None)
        if val_result and val_result.get("validation", {}).get("status") == "PASS":
            id_score += 80; id_details.append("ID document valid and not expired")
        else:
            id_score += 0; id_details.append("ID document EXPIRED")
            flags.append("Identity document is expired")
    else:
        id_details.append("Expiry date not found")

    # Check national ID number validity
    id_field = _get_field(extractions, "pesel") or _get_field(extractions, "cnp") or _get_field(extractions, "rodne_cislo")
    if id_field:
        id_val = next((v for v in validations if v.get("field_name") in ("pesel","cnp","rodne_cislo")), None)
        if id_val and id_val.get("validation", {}).get("status") == "PASS":
            id_score += 80; id_details.append(f"National ID validated")
        else:
            id_score += 20; id_details.append("National ID format warning")
            flags.append("National ID number failed checksum validation")
    else:
        id_details.append("National ID not extracted")

    # Check age
    dob_str = _get_field(extractions, "date_of_birth")
    age = _parse_age(dob_str)
    if age:
        min_age = thresholds["min_age"]; max_age = thresholds["max_age"]
        if min_age <= age <= max_age:
            id_score += 40; id_details.append(f"Age {age} — eligible")
        else:
            id_score += 0
            flags.append(f"Age {age} outside eligible range {min_age}-{max_age}")
            id_details.append(f"Age {age} — outside range")

    id_score = min(id_score, 200)
    score += id_score
    breakdown.append({"category": "Identity Validity", "score": id_score, "max": 200,
                      "detail": "; ".join(id_details), "pct": round(id_score/200*100)})

    # --- 4. Document Consistency (0-200 pts) ---
    doc_score = 200
    doc_details = []
    consistency_fails = [v for v in validations if v.get("validation", {}).get("status") == "FAIL"]
    addr_fails = [v for v in consistency_fails if "address" in v.get("field_name","")]
    income_fails = [v for v in consistency_fails if "income" in v.get("field_name","") or "salary" in v.get("field_name","")]
    name_fails = [v for v in consistency_fails if "name" in v.get("field_name","")]

    if addr_fails:
        doc_score -= 80; doc_details.append("Address mismatch between documents")
        flags.append("Address inconsistency detected across documents")
    if income_fails:
        doc_score -= 60; doc_details.append("Income discrepancy (>10% variance)")
        flags.append("Income discrepancy exceeds 10% threshold")
    if name_fails:
        doc_score -= 60; doc_details.append("Name mismatch between documents")
        flags.append("Name inconsistency detected")

    if doc_score == 200:
        doc_details.append("All documents consistent")

    doc_score = max(doc_score, 0)
    score += doc_score
    breakdown.append({"category": "Document Consistency", "score": doc_score, "max": 200,
                      "detail": "; ".join(doc_details), "pct": round(doc_score/200*100)})

    # --- 5. Age & Eligibility bonus (0-100 pts) ---
    if age:
        if 25 <= age <= 55:
            age_pts = 100; age_detail = f"Prime credit age ({age})"
        elif 18 <= age <= 65:
            age_pts = 60; age_detail = f"Eligible age ({age})"
        else:
            age_pts = 20; age_detail = f"Edge of eligible range ({age})"
    else:
        age_pts = 0; age_detail = "Age not determined"

    score += age_pts
    breakdown.append({"category": "Age & Eligibility", "score": age_pts, "max": 100,
                      "detail": age_detail, "pct": round(age_pts/100*100)})

    # --- Determine risk band ---
    total = min(max(score, 0), 1000)
    risk_label = "HIGH RISK"; risk_icon = "🔴"; risk_colour = "#dc3545"
    for lo, hi, label, icon, colour in RISK_BANDS:
        if lo <= total <= hi:
            risk_label = label; risk_icon = icon; risk_colour = colour
            break

    # --- Recommendation ---
    if total >= 650 and not flags:
        recommendation = "APPROVE"
    elif total >= 500 or (total >= 400 and len(flags) <= 1):
        recommendation = "REFER"
    else:
        recommendation = "DECLINE"

    return {
        "score": total,
        "score_pct": round(total / 10),
        "risk_band": risk_label,
        "risk_icon": risk_icon,
        "risk_colour": risk_colour,
        "recommendation": recommendation,
        "bureau_name": thresholds["bureau"],
        "market": market,
        "breakdown": breakdown,
        "flags": flags,
        "disclaimer": "MOCK SCORE — for demonstration only. Replace with live bureau API in production."
    }
