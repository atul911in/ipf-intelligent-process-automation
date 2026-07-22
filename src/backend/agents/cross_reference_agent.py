"""
IPF IPA PoC - Cross-Reference Agent
Compares declared loan application fields against extracted supporting document fields.
Produces discrepancy records with severity ratings for reviewer display.
"""
import re
from difflib import SequenceMatcher
from typing import Optional


SEVERITY = {"HIGH": "HIGH", "MEDIUM": "MEDIUM", "LOW": "LOW"}
STATUS = {"MATCH": "MATCH", "WARNING": "WARNING", "MISMATCH": "MISMATCH", "UNVERIFIABLE": "UNVERIFIABLE"}

SEVERITY_ICONS = {
    "HIGH": "🔴",
    "MEDIUM": "🟡",
    "LOW": "🟢",
}

COMPARISON_RULES = [
    {
        "field_pair": "applicant_full_name",
        "loan_app_field": "applicant_full_name",
        "doc_fields": ["first_name", "last_name", "card_holder_name"],
        "doc_types": ["identity_card", "address_card"],
        "comparison_type": "name",
        "severity": "HIGH",
        "label": "Applicant Name",
    },
    {
        "field_pair": "date_of_birth",
        "loan_app_field": "date_of_birth",
        "doc_fields": ["date_of_birth"],
        "doc_types": ["identity_card"],
        "comparison_type": "date",
        "severity": "HIGH",
        "label": "Date of Birth",
    },
    {
        "field_pair": "residential_address",
        "loan_app_field": "residential_address",
        "doc_fields": ["customer_address", "permanent_address", "address"],
        "doc_types": ["utility_bill", "bank_statement", "address_card", "proof_of_residence"],
        "comparison_type": "address",
        "severity": "MEDIUM",
        "label": "Residential Address",
    },
    {
        "field_pair": "declared_net_monthly_income",
        "loan_app_field": "declared_net_monthly_income",
        "doc_fields": ["net_salary", "net_monthly_salary", "monthly_avg_net"],
        "doc_types": ["payslip", "income_proof", "employment_certificate"],
        "comparison_type": "income",
        "severity": "HIGH",
        "label": "Declared Net Income",
    },
    {
        "field_pair": "bank_account_number",
        "loan_app_field": "bank_account_number",
        "doc_fields": ["account_number", "iban"],
        "doc_types": ["bank_statement", "bank_account_documents"],
        "comparison_type": "account",
        "severity": "MEDIUM",
        "label": "Bank Account Number",
    },
]


def _clean_str(value) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _parse_number(value_str: str) -> Optional[float]:
    if not value_str:
        return None
    try:
        clean = re.sub(r"[^\d.,]", "", str(value_str).replace(",", "."))
        parts = clean.split(".")
        if len(parts) > 2:
            clean = "".join(parts[:-1]) + "." + parts[-1]
        return float(clean) if clean else None
    except Exception:
        return None


def _compare_names(name1: str, name2: str) -> tuple:
    """Compare two name strings. Returns (status, similarity_pct, detail)."""
    if not name1 or not name2:
        return STATUS["UNVERIFIABLE"], 0, "One or both names not available"
    n1 = " ".join(sorted(_clean_str(name1).split()))
    n2 = " ".join(sorted(_clean_str(name2).split()))
    ratio = SequenceMatcher(None, n1, n2).ratio()
    pct = int(ratio * 100)
    if ratio >= 0.85:
        return STATUS["MATCH"], pct, f"Names match ({pct}% similarity)"
    elif ratio >= 0.70:
        return STATUS["WARNING"], pct, f"Names partially match ({pct}% similarity) — verify spelling"
    else:
        return STATUS["MISMATCH"], pct, f"Names do not match ({pct}% similarity)"


def _compare_dates(date1: str, date2: str) -> tuple:
    if not date1 or not date2:
        return STATUS["UNVERIFIABLE"], 0, "Date not available in one or both documents"
    d1 = _clean_str(date1).replace("/", "-").replace(".", "-")
    d2 = _clean_str(date2).replace("/", "-").replace(".", "-")
    if d1 == d2:
        return STATUS["MATCH"], 100, "Dates match exactly"
    if d1[:10] == d2[:10]:
        return STATUS["MATCH"], 100, "Dates match"
    return STATUS["MISMATCH"], 0, f"Date mismatch: declared '{date1}' vs document '{date2}'"


def _compare_addresses(addr1: str, addr2: str) -> tuple:
    if not addr1 or not addr2:
        return STATUS["UNVERIFIABLE"], 0, "Address not available in one or both documents"
    ratio = SequenceMatcher(None, _clean_str(addr1), _clean_str(addr2)).ratio()
    pct = int(ratio * 100)
    if ratio >= 0.80:
        return STATUS["MATCH"], pct, f"Addresses match ({pct}% similarity)"
    elif ratio >= 0.60:
        return STATUS["WARNING"], pct, f"Addresses partially match ({pct}%) — verify"
    else:
        return STATUS["MISMATCH"], pct, f"Address mismatch ({pct}% similarity)"


def _compare_income(declared_str: str, doc_str: str) -> tuple:
    declared = _parse_number(declared_str)
    doc_income = _parse_number(doc_str)
    if declared is None or doc_income is None:
        return STATUS["UNVERIFIABLE"], 0, "Income figure not available in one or both sources"
    if declared == 0:
        return STATUS["UNVERIFIABLE"], 0, "Declared income is zero"
    variance = abs(declared - doc_income) / declared * 100
    if variance <= 5:
        return STATUS["MATCH"], int(100 - variance), f"Income matches (variance {variance:.1f}%)"
    elif variance <= 10:
        return STATUS["WARNING"], int(100 - variance), f"Income within tolerance (variance {variance:.1f}%)"
    else:
        return STATUS["MISMATCH"], 0, f"Income discrepancy: declared {declared_str} vs document {doc_str} ({variance:.1f}% variance)"


def _compare_accounts(acc1: str, acc2: str) -> tuple:
    if not acc1 or not acc2:
        return STATUS["UNVERIFIABLE"], 0, "Account number not available"
    # Strip spaces and hyphens for comparison
    a1 = re.sub(r"[\s\-]", "", _clean_str(acc1))
    a2 = re.sub(r"[\s\-]", "", _clean_str(acc2))
    if a1 == a2:
        return STATUS["MATCH"], 100, "Account numbers match"
    if len(a1) > 6 and a1[-8:] == a2[-8:]:
        return STATUS["MATCH"], 90, "Account numbers match (last 8 digits)"
    return STATUS["MISMATCH"], 0, f"Account number mismatch"


def _get_field_from_extractions(extractions: list, field_names: list) -> Optional[str]:
    """Find the first matching field value from a list of extractions."""
    for field_name in field_names:
        for ext in extractions:
            if ext.get("field_name") == field_name:
                val = ext.get("corrected_value") or ext.get("extracted_value")
                if val and val not in ("None", "null", ""):
                    return str(val)
    return None


def run_cross_reference(
    loan_app_data: dict,
    supporting_extractions: dict,
) -> list:
    """
    Compare loan application declared fields against supporting document extractions.

    Args:
        loan_app_data: dict of {field_name: {value, confidence, label}} from loan application
        supporting_extractions: dict of {document_id: {doc_type, extractions: list}}

    Returns:
        list of discrepancy records
    """
    discrepancies = []

    def get_loan_app_value(field_name: str) -> Optional[str]:
        field_data = loan_app_data.get(field_name, {})
        if isinstance(field_data, dict):
            return field_data.get("value")
        return field_data

    for rule in COMPARISON_RULES:
        loan_value = get_loan_app_value(rule["loan_app_field"])

        # Find matching supporting document
        doc_value = None
        source_doc_id = None
        source_doc_type = None

        for doc_id, doc_info in supporting_extractions.items():
            doc_type = doc_info.get("doc_type", "")
            if any(t in doc_type for t in rule["doc_types"]):
                found = _get_field_from_extractions(doc_info.get("extractions", []), rule["doc_fields"])
                if found:
                    doc_value = found
                    source_doc_id = doc_id
                    source_doc_type = doc_type
                    break

        # Perform comparison
        comp_type = rule["comparison_type"]
        if comp_type == "name":
            # For name, combine first_name + last_name if doc_value is just first name
            if source_doc_id:
                doc_extractions = supporting_extractions[source_doc_id].get("extractions", [])
                first = _get_field_from_extractions(doc_extractions, ["first_name"])
                last = _get_field_from_extractions(doc_extractions, ["last_name"])
                if first and last:
                    doc_value = f"{first} {last}"
                elif first:
                    doc_value = first
            status, similarity, detail = _compare_names(loan_value, doc_value)
        elif comp_type == "date":
            status, similarity, detail = _compare_dates(loan_value, doc_value)
        elif comp_type == "address":
            status, similarity, detail = _compare_addresses(loan_value, doc_value)
        elif comp_type == "income":
            status, similarity, detail = _compare_income(loan_value, doc_value)
        elif comp_type == "account":
            status, similarity, detail = _compare_accounts(loan_value, doc_value)
        else:
            status, similarity, detail = STATUS["UNVERIFIABLE"], 0, "Unknown comparison type"

        discrepancy = {
            "field_pair": rule["field_pair"],
            "label": rule["label"],
            "severity": rule["severity"],
            "severity_icon": SEVERITY_ICONS[rule["severity"]],
            "declared_value": loan_value,
            "extracted_value": doc_value,
            "source_document_id": source_doc_id,
            "source_document_type": source_doc_type,
            "status": status,
            "similarity_pct": similarity,
            "detail": detail,
            "override_explanation": None,
            "override_by": None,
        }
        discrepancies.append(discrepancy)

    return discrepancies
