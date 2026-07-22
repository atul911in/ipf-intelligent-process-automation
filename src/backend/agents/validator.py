"""
IPF IPA PoC - Validation Engine
Market-specific document validation rules.
"""
import re
from datetime import datetime, date


def validate_field(field_name: str, value: str, market: str, context: dict = None) -> dict:
    """
    Validate a single extracted field against market rules.
    Returns: {status: PASS/FAIL/WARNING, reason: str}
    """
    if value is None or value == "":
        return {"status": "FAIL", "reason": "Field is empty or not extracted"}

    validators = {
        "pesel": validate_pesel,
        "cnp": validate_cnp,
        "rodne_cislo": validate_rodne_cislo,
        "expiry_date": validate_expiry_date,
        "date_of_birth": validate_age_minimum,
        "document_number": lambda v, m: validate_doc_number(v, m),
    }

    validator = validators.get(field_name)
    if validator:
        return validator(value, market)

    # Name matching (if context provided)
    if field_name in ("first_name", "last_name") and context and "application_name" in context:
        return validate_name_match(value, context["application_name"])

    # Address matching
    if "address" in field_name and context and "application_address" in context:
        return validate_address_match(value, context["application_address"])

    # Income matching
    if "net_salary" in field_name or "net_monthly" in field_name:
        if context and "declared_income" in context:
            return validate_income_match(value, context["declared_income"])

    return {"status": "PASS", "reason": "No specific validation rule"}


def validate_pesel(value: str, market: str) -> dict:
    """Validate Polish PESEL number (11 digits with checksum)."""
    if market != "PL":
        return {"status": "PASS", "reason": "Not applicable"}

    clean = re.sub(r'[^0-9]', '', value)
    if len(clean) != 11:
        return {"status": "FAIL", "reason": f"PESEL must be 11 digits, got {len(clean)}"}

    # Checksum validation
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    total = sum(int(clean[i]) * weights[i] for i in range(10))
    checksum = (10 - (total % 10)) % 10
    if checksum != int(clean[10]):
        return {"status": "FAIL", "reason": "PESEL checksum invalid"}

    return {"status": "PASS", "reason": "Valid PESEL"}


def validate_cnp(value: str, market: str) -> dict:
    """Validate Romanian CNP (13 digits)."""
    if market != "RO":
        return {"status": "PASS", "reason": "Not applicable"}

    clean = re.sub(r'[^0-9]', '', value)
    if len(clean) != 13:
        return {"status": "FAIL", "reason": f"CNP must be 13 digits, got {len(clean)}"}

    # Basic structure: S YY MM DD RR NNN C
    sex_digit = int(clean[0])
    if sex_digit not in (1, 2, 5, 6):
        return {"status": "FAIL", "reason": f"Invalid sex digit: {sex_digit}"}

    month = int(clean[3:5])
    if month < 1 or month > 12:
        return {"status": "FAIL", "reason": f"Invalid month in CNP: {month}"}

    day = int(clean[5:7])
    if day < 1 or day > 31:
        return {"status": "FAIL", "reason": f"Invalid day in CNP: {day}"}

    return {"status": "PASS", "reason": "Valid CNP format"}


def validate_rodne_cislo(value: str, market: str) -> dict:
    """Validate Czech Rodne cislo (birth number: YYMMDD/NNNN)."""
    if market != "CZ":
        return {"status": "PASS", "reason": "Not applicable"}

    clean = re.sub(r'[^0-9]', '', value)
    if len(clean) not in (9, 10):
        return {"status": "FAIL", "reason": f"Rodne cislo must be 9 or 10 digits, got {len(clean)}"}

    # For 10-digit: must be divisible by 11
    if len(clean) == 10:
        if int(clean) % 11 != 0:
            return {"status": "FAIL", "reason": "Rodne cislo fails mod-11 check"}

    month = int(clean[2:4])
    # Women have month + 50
    if month > 50:
        month -= 50
    if month < 1 or month > 12:
        return {"status": "FAIL", "reason": f"Invalid month in rodne cislo: {month}"}

    return {"status": "PASS", "reason": "Valid rodne cislo format"}


def validate_expiry_date(value: str, market: str) -> dict:
    """Check document is not expired."""
    try:
        expiry = datetime.strptime(value, "%Y-%m-%d").date()
        if expiry < date.today():
            return {"status": "FAIL", "reason": f"Document expired on {value}"}
        return {"status": "PASS", "reason": "Document not expired"}
    except ValueError:
        return {"status": "WARNING", "reason": f"Could not parse date: {value}"}


def validate_age_minimum(value: str, market: str) -> dict:
    """Check customer is at least 18 years old."""
    try:
        dob = datetime.strptime(value, "%Y-%m-%d").date()
        age = (date.today() - dob).days // 365
        if age < 18:
            return {"status": "FAIL", "reason": f"Customer is {age} years old (minimum 18)"}
        return {"status": "PASS", "reason": f"Customer is {age} years old"}
    except ValueError:
        return {"status": "WARNING", "reason": f"Could not parse date: {value}"}


def validate_doc_number(value: str, market: str) -> dict:
    """Validate document number format per market."""
    patterns = {
        "PL": r'^[A-Z]{3}\d{6}$',
        "RO": r'^\d{9}$',
        "CZ": r'^\d{9}$',
        "HU": r'^[A-Z0-9]{6,9}$'
    }
    pattern = patterns.get(market)
    if pattern and not re.match(pattern, value):
        return {"status": "WARNING", "reason": f"Document number format unexpected for {market}"}
    return {"status": "PASS", "reason": "Document number format valid"}


def validate_name_match(extracted_name: str, application_name: str) -> dict:
    """Fuzzy match names (simple ratio)."""
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, extracted_name.lower(), application_name.lower()).ratio()
    if ratio >= 0.85:
        return {"status": "PASS", "reason": f"Name match: {ratio*100:.0f}%"}
    elif ratio >= 0.70:
        return {"status": "WARNING", "reason": f"Name partial match: {ratio*100:.0f}%"}
    else:
        return {"status": "FAIL", "reason": f"Name mismatch: {ratio*100:.0f}% (extracted: {extracted_name})"}


def validate_address_match(doc_address: str, app_address: str) -> dict:
    """Basic address comparison."""
    from difflib import SequenceMatcher
    ratio = SequenceMatcher(None, doc_address.lower(), app_address.lower()).ratio()
    if ratio >= 0.80:
        return {"status": "PASS", "reason": f"Address match: {ratio*100:.0f}%"}
    else:
        return {"status": "FAIL", "reason": f"Address mismatch: {ratio*100:.0f}%"}


def validate_income_match(doc_income_str: str, declared_income: float) -> dict:
    """Check income discrepancy within 10%."""
    try:
        # Extract numeric value from string
        clean = re.sub(r'[^0-9.]', '', doc_income_str.replace(',', ''))
        doc_income = float(clean)
        if declared_income == 0:
            return {"status": "WARNING", "reason": "Declared income is zero"}
        discrepancy = abs(doc_income - declared_income) / declared_income * 100
        if discrepancy <= 10:
            return {"status": "PASS", "reason": f"Income within threshold ({discrepancy:.1f}% difference)"}
        else:
            return {"status": "FAIL", "reason": f"Income discrepancy {discrepancy:.1f}% exceeds 10% threshold (doc: {doc_income}, declared: {declared_income})"}
    except (ValueError, ZeroDivisionError):
        return {"status": "WARNING", "reason": f"Could not parse income value: {doc_income_str}"}
