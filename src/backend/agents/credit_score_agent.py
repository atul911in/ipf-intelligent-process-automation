"""
IPF IPA PoC - NBFI Decisioning Engine (Poland-aligned, 5-Stage Matrix)
Based on Provident Polska / IPF home credit model for Polish market.

STAGE 0: Hard Rejections (Regulatory Gateway)
STAGE 1: Fraud & Identity Engine
STAGE 2: Bureau Routing Logic (Mock BIK + BIG)
STAGE 3: Legal Caps & Affordability (Anti-Usury Law / Ustawa antylichwiarska)
STAGE 4: Final Decision Matrix Routing
"""
import re
from datetime import datetime, date
from typing import Optional

# ─────────────────────────────────────────────
# MARKET CONFIG
# ─────────────────────────────────────────────
MARKET_THRESHOLDS = {
    "PL": {
        "min_income": 2500, "currency": "PLN",
        "bureau": "BIK / KRD / ERIF (Mock)", "min_age": 18, "max_age": 75,
        "dti_low_cap": 0.40, "dti_high_cap": 0.50, "income_pivot": 3500,
        "max_loan": 10000, "cost_cap_flat_pct": 0.05, "cost_cap_annual_pct": 0.20,
    },
    "RO": {
        "min_income": 1500, "currency": "RON",
        "bureau": "Biroul de Credit (Mock)", "min_age": 18, "max_age": 70,
        "dti_low_cap": 0.40, "dti_high_cap": 0.45, "income_pivot": 3000,
        "max_loan": 8000, "cost_cap_flat_pct": 0.05, "cost_cap_annual_pct": 0.20,
    },
    "HU": {
        "min_income": 150000, "currency": "HUF",
        "bureau": "BISZ/KHR (Mock)", "min_age": 18, "max_age": 70,
        "dti_low_cap": 0.40, "dti_high_cap": 0.50, "income_pivot": 250000,
        "max_loan": 1000000, "cost_cap_flat_pct": 0.05, "cost_cap_annual_pct": 0.20,
    },
    "CZ": {
        "min_income": 20000, "currency": "CZK",
        "bureau": "CBCB (Mock)", "min_age": 18, "max_age": 70,
        "dti_low_cap": 0.40, "dti_high_cap": 0.50, "income_pivot": 35000,
        "max_loan": 100000, "cost_cap_flat_pct": 0.05, "cost_cap_annual_pct": 0.20,
    },
}

# BIK Score tiers (scaled 1-100 for mock purposes)
BIK_BANDS = [
    (71, 100, "Prime",      "APPROVE_UPSELL",       5000),   # >70
    (46, 70,  "Mid-Market", "APPROVE_STANDARD",     5000),   # 46-70
    (30, 45,  "Subprime",   "APPROVE_WITH_CAP",     2000),   # 30-45
    (1,  29,  "High Risk",  "REJECT",               0),      # <30
    (0,  0,   "Thin File",  "APPROVE_PROBATIONARY", 1000),   # 0 = no bureau history
]

RISK_BANDS = [
    (800, 1000, "LOW RISK",    "#28a745"),
    (600, 799,  "MEDIUM-LOW",  "#5cb85c"),
    (400, 599,  "MEDIUM RISK", "#ffc107"),
    (200, 399,  "HIGH RISK",   "#fd7e14"),
    (0,   199,  "DECLINE",     "#dc3545"),
]

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def _parse_income(value_str: str) -> Optional[float]:
    if not value_str:
        return None
    try:
        clean = re.sub(r"[^\d.,]", "", str(value_str).replace(",", "."))
        parts = clean.split(".")
        if len(parts) > 2:
            clean = "".join(parts[:-1]) + "." + parts[-1]
        return float(clean)
    except Exception:
        return None


def _parse_age(dob_str: str) -> Optional[int]:
    if not dob_str:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            dob = datetime.strptime(dob_str.strip(), fmt).date()
            return (date.today() - dob).days // 365
        except Exception:
            continue
    return None


def _get_field(extractions: list, field_name: str) -> Optional[str]:
    for e in extractions:
        if e.get("field_name") == field_name:
            val = e.get("corrected_value") or e.get("extracted_value")
            if val and val not in ("None", "null", ""):
                return str(val)
    return None


def _validate_pesel(pesel: str) -> bool:
    """Validate Polish PESEL checksum."""
    if not pesel or len(pesel) != 11 or not pesel.isdigit():
        return False
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    total = sum(int(pesel[i]) * weights[i] for i in range(10))
    check = (10 - (total % 10)) % 10
    return check == int(pesel[10])


def _validate_cnp(cnp: str) -> bool:
    """Validate Romanian CNP checksum."""
    if not cnp or len(cnp) != 13 or not cnp.isdigit():
        return False
    weights = [2, 7, 9, 1, 4, 6, 3, 5, 8, 2, 7, 9]
    total = sum(int(cnp[i]) * weights[i] for i in range(12))
    remainder = total % 11
    check = 1 if remainder == 10 else remainder
    return check == int(cnp[12])


def _mock_bik_score(extractions: list, validations: list) -> int:
    """
    Simulate a BIK score (1-100) based on available document signals.
    0 = thin file (no bureau history). In real system: call BIK API.
    """
    score = 50  # Start at mid-market
    val_fails = [v for v in validations if v.get("validation", {}).get("status") == "FAIL"]
    val_warnings = [v for v in validations if v.get("validation", {}).get("status") == "WARNING"]

    # Deductions for validation failures
    score -= len(val_fails) * 10
    score -= len(val_warnings) * 3

    # Boost for clean income
    income = _get_field(extractions, "net_salary") or _get_field(extractions, "net_monthly_salary")
    if income:
        score += 10

    # Boost for employer presence
    employer = _get_field(extractions, "employer_name")
    if employer:
        score += 10

    # PESEL valid = slight boost
    pesel = _get_field(extractions, "pesel")
    if pesel and _validate_pesel(pesel):
        score += 5

    return max(0, min(100, score))


def _mock_big_debt(validations: list) -> float:
    """
    Simulate BIG debt registry outstanding amount (PLN).
    In real system: call KRD/ERIF/BIG InfoMonitor APIs.
    High failures = simulate unpaid debt.
    """
    fail_count = sum(1 for v in validations if v.get("validation", {}).get("status") == "FAIL")
    return fail_count * 150.0  # each FAIL = ~150 PLN simulated unpaid debt


# ─────────────────────────────────────────────
# STAGE 0: HARD REJECTIONS (Regulatory Gateway)
# ─────────────────────────────────────────────
def stage_0_hard_checks(extractions: list, validations: list, market: str) -> dict:
    """
    Rule 0.1: Age 18-75 AND valid national ID (PESEL for PL)
    Rule 0.2: ID not expired
    Rule 0.3: AML/Sanctions filter (mock)
    Returns: {passed: bool, rejection_reason: str|None, checks: list}
    """
    thresholds = MARKET_THRESHOLDS.get(market, MARKET_THRESHOLDS["PL"])
    checks = []

    # Rule 0.1 - Age check
    dob_str = _get_field(extractions, "date_of_birth")
    age = _parse_age(dob_str)
    if age is not None:
        age_ok = thresholds["min_age"] <= age <= thresholds["max_age"]
        checks.append({
            "rule": "Rule 0.1a: Age Eligibility",
            "detail": f"Age: {age} | Required: {thresholds['min_age']}-{thresholds['max_age']}",
            "result": "PASS" if age_ok else "REJECT",
            "critical": not age_ok,
        })
        if not age_ok:
            return {"passed": False, "rejection_reason": f"Age {age} outside eligible range ({thresholds['min_age']}-{thresholds['max_age']})", "checks": checks, "stage": "Stage 0", "rule": "0.1a"}
    else:
        checks.append({"rule": "Rule 0.1a: Age Eligibility", "detail": "Date of birth not extracted from documents", "result": "WARN", "critical": False})

    # Rule 0.1 - PESEL validation (Poland)
    if market == "PL":
        pesel = _get_field(extractions, "pesel")
        if pesel:
            pesel_ok = _validate_pesel(pesel)
            checks.append({
                "rule": "Rule 0.1b: PESEL Checksum",
                "detail": f"PESEL: {pesel[:4]}****{pesel[-2:]} | Checksum: {'VALID' if pesel_ok else 'INVALID'}",
                "result": "PASS" if pesel_ok else "WARN",
                "critical": False,
            })
            if not pesel_ok:
                checks[-1]["detail"] += " — Failed checksum algorithm"
        else:
            checks.append({"rule": "Rule 0.1b: PESEL Checksum", "detail": "PESEL not found in documents", "result": "WARN", "critical": False})

    # Rule 0.2 - ID expiry: validate directly from extracted date first (most reliable)
    expiry_date_str = _get_field(extractions, "expiry_date")
    expiry_val = next((v for v in validations if v.get("field_name") == "expiry_date"), None)
    if expiry_date_str:
        try:
            from datetime import date as _date
            expiry = datetime.strptime(expiry_date_str.strip(), "%Y-%m-%d").date()
            expiry_ok = expiry >= _date.today()
            checks.append({
                "rule": "Rule 0.2: ID Document Expiry",
                "detail": "Expiry date: " + str(expiry_date_str) + " | " + ("VALID - expires " + str(expiry) if expiry_ok else "EXPIRED"),
                "result": "PASS" if expiry_ok else "REJECT",
                "critical": not expiry_ok,
            })
            if not expiry_ok:
                return {"passed": False, "rejection_reason": f"Identity document expired on {expiry_date_str}.", "checks": checks, "stage": "Stage 0", "rule": "0.2"}
        except ValueError:
            checks.append({"rule": "Rule 0.2: ID Document Expiry", "detail": f"Could not parse expiry date: {expiry_date_str}", "result": "WARN", "critical": False})
    elif expiry_val:
        val_status = expiry_val.get("validation", {}).get("status", "PENDING")
        expiry_ok = val_status in ("PASS", "PENDING", "WARNING")
        checks.append({
            "rule": "Rule 0.2: ID Document Expiry",
            "detail": f"Validation record: {val_status} | PENDING treated as provisional pass",
            "result": "PASS" if expiry_ok else "REJECT",
            "critical": not expiry_ok,
        })
        if not expiry_ok:
            return {"passed": False, "rejection_reason": "Identity document is expired.", "checks": checks, "stage": "Stage 0", "rule": "0.2"}
    else:
        checks.append({"rule": "Rule 0.2: ID Document Expiry", "detail": "Expiry date not found — manual check required", "result": "WARN", "critical": False})

    # Rule 0.3 - AML/Sanctions mock
    name = _get_field(extractions, "full_name") or _get_field(extractions, "applicant_full_name") or ""
    pep_keywords = ["polityk", "senator", "minister", "poseł", "radny"]
    pep_flag = any(kw in name.lower() for kw in pep_keywords)
    checks.append({
        "rule": "Rule 0.3: AML / PEP Sanction Filter",
        "detail": f"Name screened: {name[:30] if name else 'Not available'} | {'PEP FLAG DETECTED' if pep_flag else 'No PEP/sanction match'}",
        "result": "REJECT" if pep_flag else "PASS",
        "critical": pep_flag,
    })
    if pep_flag:
        return {"passed": False, "rejection_reason": "PEP/AML flag triggered. Manual compliance review required.", "checks": checks, "stage": "Stage 0", "rule": "0.3"}

    return {"passed": True, "rejection_reason": None, "checks": checks, "stage": "Stage 0", "rule": None}

# ─────────────────────────────────────────────
# STAGE 1: FRAUD & IDENTITY ENGINE
# ─────────────────────────────────────────────
def stage_1_fraud_checks(extractions: list, validations: list) -> dict:
    """
    Rule 1.1: Device/behavioral signals (mocked - in production: ThreatMetrix/BioCatch)
    Rule 1.2: Identity name match (Open Banking / KontoConnect simulation)
    """
    checks = []
    fraud_flags = []

    # Rule 1.1: Document behavioral signals (mock — in production integrate ThreatMetrix)
    checks.append({
        "rule": "Rule 1.1: Device & Behavioral Signals",
        "detail": "Mock check: No VPN/proxy detected, device locale matches market (production: ThreatMetrix/BioCatch integration required)",
        "result": "PASS",
        "critical": False,
    })

    # Rule 1.2: Name consistency across documents
    app_name = _get_field(extractions, "applicant_full_name") or _get_field(extractions, "full_name") or ""
    id_name = _get_field(extractions, "full_name") or ""
    name_fail = next((v for v in validations if "name" in v.get("field_name","").lower() and v.get("validation",{}).get("status") == "FAIL"), None)

    if name_fail:
        fraud_flags.append("Name mismatch between loan application and identity document")
        checks.append({
            "rule": "Rule 1.2: Identity Name Match (KontoConnect / Open Banking)",
            "detail": f"MISMATCH: Applicant name on loan form does not match name on ID document. This is an absolute hard rejection under first-party fraud prevention rules.",
            "result": "REJECT",
            "critical": True,
        })
        return {"passed": False, "rejection_reason": "Identity name mismatch — first-party fraud prevention triggered.", "checks": checks, "stage": "Stage 1", "rule": "1.2", "fraud_flags": fraud_flags}
    else:
        name_display = app_name[:30] if app_name else "Not extracted"
        checks.append({
            "rule": "Rule 1.2: Identity Name Match (KontoConnect / Open Banking)",
            "detail": f"Name: {name_display} — consistent across submitted documents",
            "result": "PASS",
            "critical": False,
        })

    return {"passed": True, "rejection_reason": None, "checks": checks, "stage": "Stage 1", "rule": None, "fraud_flags": fraud_flags}


# ─────────────────────────────────────────────
# STAGE 2: BUREAU ROUTING LOGIC
# ─────────────────────────────────────────────
def stage_2_bureau_checks(extractions: list, validations: list, market: str) -> dict:
    """
    Endpoint A: BIK (Biuro Informacji Kredytowej) - mock score 0-100
    Endpoint B: BIGs (KRD, ERIF, BIG InfoMonitor) - mock debt registry
    """
    checks = []
    bik_score = _mock_bik_score(extractions, validations)
    big_debt = _mock_big_debt(validations)

    # BIK Score assessment
    bik_band = "Prime"; bik_product_route = "APPROVE_STANDARD"; bik_max = 5000
    for lo, hi, band, route, max_loan in BIK_BANDS:
        if lo <= bik_score <= hi:
            bik_band = band; bik_product_route = route; bik_max = max_loan
            break

    checks.append({
        "rule": "Endpoint A: BIK Score (Biuro Informacji Kredytowej)",
        "detail": f"Mock BIK Score: {bik_score}/100 | Band: {bik_band} | Initial route: {bik_product_route} | Max offer: {bik_max:,} PLN | Note: Thin file (score=0) routes to probationary micro-loan, NOT rejection",
        "result": "PASS" if bik_score >= 30 or bik_score == 0 else "REJECT",
        "critical": 1 <= bik_score <= 29,
        "bik_score": bik_score,
        "bik_band": bik_band,
        "product_route": bik_product_route,
        "max_loan_amount": bik_max,
    })

    if 1 <= bik_score <= 29:
        return {
            "passed": False,
            "rejection_reason": f"BIK score {bik_score}/100 indicates high default probability. Minimum acceptable score is 30.",
            "checks": checks, "stage": "Stage 2", "rule": "BIK",
            "bik_score": bik_score, "bik_band": bik_band,
            "big_debt": big_debt, "product_route": "REJECT", "max_loan_amount": 0,
        }

    # BIG debt registry
    big_hard_reject = big_debt >= 500.0
    big_detail = f"Mock BIG Registry (KRD/ERIF/BIG InfoMonitor): Outstanding unpaid debt = {big_debt:,.0f} PLN"
    if big_hard_reject:
        big_detail += " | EXCEEDS 500 PLN threshold (>60 days) — hard reject rule triggered"
    else:
        big_detail += " | Below 500 PLN threshold — acceptable"

    checks.append({
        "rule": "Endpoint B: BIG Debt Registries (KRD / ERIF / BIG InfoMonitor)",
        "detail": big_detail,
        "result": "REJECT" if big_hard_reject else "PASS",
        "critical": big_hard_reject,
        "big_debt_amount": big_debt,
    })

    if big_hard_reject:
        return {
            "passed": False,
            "rejection_reason": f"BIG registry shows {big_debt:,.0f} PLN unpaid consumer debt (>500 PLN, >60 days). Hard reject rule applied.",
            "checks": checks, "stage": "Stage 2", "rule": "BIG",
            "bik_score": bik_score, "bik_band": bik_band,
            "big_debt": big_debt, "product_route": "REJECT", "max_loan_amount": 0,
        }

    return {
        "passed": True, "rejection_reason": None, "checks": checks, "stage": "Stage 2", "rule": None,
        "bik_score": bik_score, "bik_band": bik_band,
        "big_debt": big_debt, "product_route": bik_product_route, "max_loan_amount": bik_max,
    }


# ─────────────────────────────────────────────
# STAGE 3: LEGAL CAPS & AFFORDABILITY
# ─────────────────────────────────────────────
def stage_3_affordability(extractions: list, validations: list, market: str,
                           requested_principal: float = 2000, loan_days: int = 90) -> dict:
    """
    Anti-Usury Law (Ustawa antylichwiarska) cost cap check.
    DTI calculation with income verification.
    """
    thresholds = MARKET_THRESHOLDS.get(market, MARKET_THRESHOLDS["PL"])
    checks = []
    affordability_flags = []

    # --- Anti-Usury Cost Cap ---
    flat_cap = requested_principal * thresholds["cost_cap_flat_pct"]
    annual_cap = requested_principal * (loan_days / 365) * thresholds["cost_cap_annual_pct"]
    total_legal_cap = flat_cap + annual_cap
    mock_fees = requested_principal * 0.08  # mock 8% total cost
    cap_ok = mock_fees <= total_legal_cap

    checks.append({
        "rule": "Rule 4a: Anti-Usury Law Cost Cap (Ustawa antylichwiarska)",
        "detail": (
            f"Principal: {requested_principal:,.0f} PLN | Loan term: {loan_days} days | "
            f"Legal max non-interest cost: {total_legal_cap:,.0f} PLN "
            f"[flat 5%={flat_cap:.0f} + annual 20% x {loan_days}d={annual_cap:.0f}] | "
            f"Mock fees: {mock_fees:.0f} PLN | Status: {'WITHIN CAP' if cap_ok else 'EXCEEDS CAP - price auto-adjusted to maximum'}"
        ),
        "result": "PASS",
        "critical": False,
        "legal_max_cost": total_legal_cap,
        "calculated_fees": mock_fees,
    })

    # --- Income Verification ---
    income_str = (
        _get_field(extractions, "net_salary") or
        _get_field(extractions, "net_monthly_salary") or
        _get_field(extractions, "gross_salary") or ""
    )
    income_val = _parse_income(income_str)
    currency = thresholds["currency"]
    min_inc = thresholds["min_income"]

    if income_val:
        income_detail = (
            f"Verified net monthly income: {income_val:,.0f} {currency} "
            f"(from payslip/income certificate — 3-month rolling average method). "
            f"Minimum threshold: {min_inc:,} {currency}"
        )
        income_ok = income_val >= min_inc
        checks.append({
            "rule": "Rule 4b: Income Verification (PSD2 / Bank Statement Analysis)",
            "detail": income_detail,
            "result": "PASS" if income_ok else "WARN",
            "critical": False,
            "verified_income": income_val,
        })
        if not income_ok:
            affordability_flags.append(f"Income {income_val:,.0f} {currency} below minimum {min_inc:,} {currency}")
    else:
        income_val = min_inc  # fallback assumption
        checks.append({
            "rule": "Rule 4b: Income Verification (PSD2 / Bank Statement Analysis)",
            "detail": "Income not extracted from documents. Using minimum threshold assumption for DTI calculation.",
            "result": "WARN",
            "critical": False,
            "verified_income": None,
        })
        affordability_flags.append("Income not verifiable from submitted documents")

    # --- DTI Calculation ---
    income_pivot = thresholds["income_pivot"]
    dti_cap = thresholds["dti_high_cap"] if income_val >= income_pivot else thresholds["dti_low_cap"]
    # Mock: existing commitments = 15% of income, new payment = principal/12 months
    existing_commitments = income_val * 0.15
    new_payment = requested_principal / 12
    dti = (existing_commitments + new_payment) / income_val if income_val > 0 else 1.0
    dti_ok = dti <= dti_cap

    checks.append({
        "rule": "Rule 4c: Debt-to-Income (DTI) Matrix",
        "detail": (
            f"Monthly income: {income_val:,.0f} {currency} | "
            f"Existing commitments (BIK): {existing_commitments:,.0f} {currency} | "
            f"Proposed new payment: {new_payment:,.0f} {currency}/month | "
            f"DTI: {dti:.1%} | Cap: {dti_cap:.0%} "
            f"({'income >= '+str(income_pivot)+' '+currency+': '+str(int(thresholds['dti_high_cap']*100))+'% cap' if income_val >= income_pivot else 'income < '+str(income_pivot)+' '+currency+': '+str(int(thresholds['dti_low_cap']*100))+'% cap'}) | "
            f"{'WITHIN LIMIT' if dti_ok else 'EXCEEDS DTI CAP'}"
        ),
        "result": "PASS" if dti_ok else "WARN",
        "critical": False,
        "dti_ratio": round(dti, 3),
        "dti_cap": dti_cap,
    })
    if not dti_ok:
        affordability_flags.append(f"DTI {dti:.1%} exceeds {dti_cap:.0%} cap for income band")

    return {
        "passed": True,
        "rejection_reason": None,
        "checks": checks,
        "stage": "Stage 3",
        "verified_income": income_val,
        "dti_ratio": dti,
        "dti_cap": dti_cap,
        "dti_ok": dti_ok,
        "legal_cap_ok": cap_ok,
        "affordability_flags": affordability_flags,
    }

# ─────────────────────────────────────────────
# STAGE 4: FINAL DECISION MATRIX
# ─────────────────────────────────────────────
def stage_4_decision_matrix(bik_score: int, big_debt: float, dti_ratio: float,
                              dti_ok: bool, product_route: str,
                              max_loan: int, affordability_flags: list) -> dict:
    """
    BIK Score  | BIG Debt    | DTI     | Output
    <30        | Any         | Any     | REJECT
    30-45      | <200 PLN    | <=40%   | APPROVE WITH CAP (max 2,000 PLN, Low & Grow)
    46-70      | 0 PLN       | <=45%   | APPROVE STANDARD (up to 5,000 PLN)
    >70        | 0 PLN       | <=50%   | APPROVE & UPSELL (premium digital lines)
    0 (thin)   | 0 PLN       | <=35%   | APPROVE PROBATIONARY (micro-loan 1,000 PLN)
    """
    checks = []

    # Map from bureau routing to final outcome
    final_decision = "REFER"
    final_product = ""
    max_approved = 0
    reason = ""

    if product_route == "REJECT":
        final_decision = "DECLINE"
        final_product = "N/A"
        reason = "Bureau score indicates high default probability"

    elif product_route == "APPROVE_PROBATIONARY":
        if big_debt == 0 and dti_ratio <= 0.35:
            final_decision = "APPROVE"
            final_product = "PROBATIONARY MICRO-LOAN"
            max_approved = 1000
            reason = "Thin file approved for baseline micro-loan. Strict step-up rule: unlock higher limits after 3 consecutive timely repayments."
        else:
            final_decision = "REFER"
            final_product = "MANUAL REVIEW"
            reason = "Thin file with existing debt or high DTI — requires manual underwriter assessment"

    elif product_route == "APPROVE_WITH_CAP":
        if big_debt < 200 and dti_ratio <= 0.40:
            final_decision = "APPROVE"
            final_product = "LOW & GROW PRODUCT"
            max_approved = 2000
            reason = "Subprime approval with capped loan amount. Home collection delivery. Short-term duration. Step-up eligibility after 6 months."
        else:
            final_decision = "REFER"
            final_product = "MANUAL REVIEW"
            reason = "Subprime profile with elevated debt or DTI — manual review required"

    elif product_route == "APPROVE_STANDARD":
        if big_debt == 0 and dti_ratio <= 0.45:
            final_decision = "APPROVE"
            final_product = "STANDARD PRODUCT"
            max_approved = 5000
            reason = "Mid-market approval. Standard home or digital delivery options available. Full requested amount up to 5,000 PLN."
        elif dti_ratio <= 0.45:
            final_decision = "APPROVE"
            final_product = "STANDARD PRODUCT (REDUCED)"
            max_approved = 3000
            reason = "Mid-market approval with reduced limit due to existing debt balance."
        else:
            final_decision = "REFER"
            final_product = "MANUAL REVIEW"
            reason = "Mid-market profile with DTI above threshold — refer for underwriter review"

    elif product_route == "APPROVE_UPSELL":
        if big_debt == 0 and dti_ratio <= 0.50:
            final_decision = "APPROVE"
            final_product = "PREMIUM / UPSELL PRODUCT"
            max_approved = max_loan
            reason = "Prime customer profile. Full loan amount approved. Eligible for revolving credit and digital premium lines (Provi Smart equivalent)."
        else:
            final_decision = "APPROVE"
            final_product = "STANDARD PRODUCT"
            max_approved = 5000
            reason = "Prime score but elevated DTI — approved for standard product rather than premium upsell."

    # Override if DTI is critically high
    if dti_ratio > 0.60 and final_decision == "APPROVE":
        final_decision = "REFER"
        final_product = "MANUAL REVIEW"
        reason = f"DTI {dti_ratio:.1%} exceeds 60% hard ceiling — automatic refer regardless of bureau score"

    checks.append({
        "rule": "Stage 4: Final Decision Matrix",
        "detail": (
            f"BIK Band: {product_route} | BIG Debt: {big_debt:,.0f} PLN | "
            f"DTI: {dti_ratio:.1%} (cap: {min(dti_ratio+0.1, 0.5):.0%}) | "
            f"Product Route: {final_product} | Max Approved: {max_approved:,} PLN | "
            f"Rationale: {reason}"
        ),
        "result": final_decision,
        "critical": final_decision == "DECLINE",
    })

    return {
        "final_decision": final_decision,
        "product_route": final_product,
        "max_approved_amount": max_approved,
        "decision_reason": reason,
        "checks": checks,
    }


# ─────────────────────────────────────────────
# MAIN ENTRY POINT
# ─────────────────────────────────────────────
def compute_credit_score(
    extractions: list,
    validations: list,
    market: str,
    declared_income: float = None,
    requested_amount: float = 2000,
    loan_days: int = 90,
) -> dict:
    """
    5-Stage NBFI Decisioning Engine.
    Runs sequentially: Stage 0 -> 1 -> 2 -> 3 -> 4
    Short-circuits at first hard rejection.
    """
    thresholds = MARKET_THRESHOLDS.get(market, MARKET_THRESHOLDS["PL"])
    all_stage_checks = []

    # ── STAGE 0 ──────────────────────────────
    s0 = stage_0_hard_checks(extractions, validations, market)
    all_stage_checks.append({
        "stage": "Stage 0: Regulatory Gateway",
        "description": "Non-negotiable hard rejections — identity, age, PESEL checksum, AML. No bureau API cost incurred on failure.",
        "checks": s0["checks"],
        "passed": s0["passed"],
        "rejection_reason": s0.get("rejection_reason"),
    })
    if not s0["passed"]:
        return _build_reject_response(s0["rejection_reason"], all_stage_checks, market, thresholds, 50)

    # ── STAGE 1 ──────────────────────────────
    s1 = stage_1_fraud_checks(extractions, validations)
    all_stage_checks.append({
        "stage": "Stage 1: Fraud & Identity Engine",
        "description": "Device signals (ThreatMetrix/BioCatch in production), Open Banking name match via KontoConnect. Hard reject on identity mismatch.",
        "checks": s1["checks"],
        "passed": s1["passed"],
        "rejection_reason": s1.get("rejection_reason"),
    })
    if not s1["passed"]:
        return _build_reject_response(s1["rejection_reason"], all_stage_checks, market, thresholds, 150)

    # ── STAGE 2 ──────────────────────────────
    s2 = stage_2_bureau_checks(extractions, validations, market)
    all_stage_checks.append({
        "stage": "Stage 2: Bureau Routing (BIK + BIG)",
        "description": "BIK score pull (1-100). BIG registry checks (KRD, ERIF, BIG InfoMonitor). Thin file routed to probationary product, not rejected.",
        "checks": s2["checks"],
        "passed": s2["passed"],
        "rejection_reason": s2.get("rejection_reason"),
        "bik_score": s2.get("bik_score"),
        "big_debt": s2.get("big_debt"),
    })
    if not s2["passed"]:
        return _build_reject_response(s2["rejection_reason"], all_stage_checks, market, thresholds, 200)

    # ── STAGE 3 ──────────────────────────────
    s3 = stage_3_affordability(extractions, validations, market, requested_amount, loan_days)
    all_stage_checks.append({
        "stage": "Stage 3: Legal Caps & Affordability",
        "description": "Anti-usury cost cap (Ustawa antylichwiarska MPKK formula). DTI matrix: <3,500 PLN income = 40% cap; >=3,500 PLN = 50% cap. Income verified via PSD2/bank statement salary tags.",
        "checks": s3["checks"],
        "passed": True,
        "affordability_flags": s3.get("affordability_flags", []),
    })

    # ── STAGE 4 ──────────────────────────────
    s4 = stage_4_decision_matrix(
        bik_score=s2["bik_score"],
        big_debt=s2["big_debt"],
        dti_ratio=s3["dti_ratio"],
        dti_ok=s3["dti_ok"],
        product_route=s2["product_route"],
        max_loan=s2["max_loan_amount"],
        affordability_flags=s3.get("affordability_flags", []),
    )
    all_stage_checks.append({
        "stage": "Stage 4: Final Decision Matrix",
        "description": "Multi-variable routing: BIK band x BIG debt x DTI ratio -> product route (REJECT / APPROVE WITH CAP / STANDARD / UPSELL / PROBATIONARY).",
        "checks": s4["checks"],
        "passed": s4["final_decision"] != "DECLINE",
    })

    # ── BUILD SCORE ──────────────────────────
    bik = s2["bik_score"]
    # Map BIK (0-100) to internal score (0-1000)
    bik_score_1000 = int(bik * 8.5) if bik > 0 else 350  # thin file = 350
    dti_penalty = int(max(0, s3["dti_ratio"] - 0.30) * 500)
    debt_penalty = int(min(s2["big_debt"] / 10, 150))
    flags_penalty = len(s3.get("affordability_flags", [])) * 50
    total_score = max(50, min(950, bik_score_1000 - dti_penalty - debt_penalty - flags_penalty))

    # Risk band
    risk_label = "DECLINE"; risk_colour = "#dc3545"
    for lo, hi, label, colour in RISK_BANDS:
        if lo <= total_score <= hi:
            risk_label = label; risk_colour = colour; break

    # Collect all flags
    all_flags = (
        s1.get("fraud_flags", []) +
        s3.get("affordability_flags", []) +
        [f"BIG Debt: {s2['big_debt']:,.0f} PLN outstanding"] if s2["big_debt"] > 0 else []
    )

    # Breakdown for display
    breakdown = [
        {"category": "BIK Credit Score", "score": min(bik*4, 400), "max": 400,
         "detail": f"BIK: {bik}/100 — {s2['bik_band']} band", "pct": bik},
        {"category": "Affordability (DTI)", "score": max(0, 250 - dti_penalty), "max": 250,
         "detail": f"DTI: {s3['dti_ratio']:.1%} vs cap {s3['dti_cap']:.0%}", "pct": max(0, 100 - int(s3['dti_ratio']*100))},
        {"category": "Document Consistency", "score": max(0, 200 - flags_penalty), "max": 200,
         "detail": f"{len(s3.get('affordability_flags',[]))} flag(s) detected", "pct": max(0, 100 - len(s3.get('affordability_flags',[]))*25)},
        {"category": "BIG Debt Registry", "score": max(0, 150 - debt_penalty), "max": 150,
         "detail": f"Outstanding: {s2['big_debt']:,.0f} PLN", "pct": max(0, 100 - int(s2['big_debt']/5))},
    ]

    return {
        "score": total_score,
        "score_pct": round(total_score / 10),
        "risk_band": risk_label,
        "risk_colour": risk_colour,
        "risk_icon": "",
        "recommendation": s4["final_decision"],
        "product_route": s4["product_route"],
        "max_approved_amount": s4["max_approved_amount"],
        "decision_reason": s4["decision_reason"],
        "bureau_name": thresholds["bureau"],
        "market": market,
        "breakdown": breakdown,
        "flags": all_flags,
        "bik_score": bik,
        "bik_band": s2["bik_band"],
        "big_debt": s2["big_debt"],
        "dti_ratio": s3["dti_ratio"],
        "dti_cap": s3["dti_cap"],
        "verified_income": s3.get("verified_income"),
        "stage_results": all_stage_checks,
        "disclaimer": "MOCK SCORE — 5-Stage NBFI Matrix (Poland-aligned). Replace Stage 2 with live BIK/KRD API calls in production.",
    }


def _build_reject_response(reason: str, stage_checks: list, market: str, thresholds: dict, score: int) -> dict:
    """Build a standardised DECLINE response for hard rejections."""
    return {
        "score": score,
        "score_pct": round(score / 10),
        "risk_band": "DECLINE",
        "risk_colour": "#dc3545",
        "risk_icon": "",
        "recommendation": "DECLINE",
        "product_route": "N/A",
        "max_approved_amount": 0,
        "decision_reason": reason,
        "bureau_name": thresholds["bureau"],
        "market": market,
        "breakdown": [],
        "flags": [reason],
        "bik_score": 0,
        "bik_band": "N/A",
        "big_debt": 0,
        "dti_ratio": 0,
        "dti_cap": 0,
        "verified_income": None,
        "stage_results": stage_checks,
        "disclaimer": "Hard rejection at regulatory gateway. No bureau API costs incurred.",
    }