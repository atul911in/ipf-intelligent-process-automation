"""
IPF IPA PoC - Loan Application Extraction Agent
Extracts declared customer fields from a loan application form document.
These fields become the reference dataset for cross-referencing supporting documents.
"""
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..core.config import settings

LOAN_APP_FIELDS = [
    "applicant_full_name",
    "date_of_birth",
    "residential_address",
    "declared_net_monthly_income",
    "declared_income_currency",
    "requested_loan_amount",
    "loan_term_weeks",
    "employment_status",
    "employer_name",
    "bank_account_number",
    "purpose_of_loan",
    "phone_number",
    "email_address",
]

MARKET_LABELS = {
    "PL": {
        "applicant_full_name": "Imie i Nazwisko",
        "date_of_birth": "Data urodzenia",
        "residential_address": "Adres zamieszkania",
        "declared_net_monthly_income": "Dochod netto miesieczny",
        "requested_loan_amount": "Kwota pozyczki",
        "loan_term_weeks": "Okres splaty (tygodnie)",
        "employer_name": "Pracodawca",
        "bank_account_number": "Numer rachunku bankowego",
    },
    "RO": {
        "applicant_full_name": "Nume complet",
        "date_of_birth": "Data nasterii",
        "residential_address": "Adresa de domiciliu",
        "declared_net_monthly_income": "Venit net lunar",
        "requested_loan_amount": "Suma solicitata",
        "loan_term_weeks": "Termen de rambursare (saptamani)",
        "employer_name": "Angajator",
        "bank_account_number": "Numar de cont bancar",
    },
    "HU": {
        "applicant_full_name": "Teljes nev",
        "date_of_birth": "Szuletesi datum",
        "residential_address": "Lakcim",
        "declared_net_monthly_income": "Netto havi jovedelem",
        "requested_loan_amount": "Igenyelt kölcson osszeg",
        "loan_term_weeks": "Futamido (het)",
        "employer_name": "Munkaltato",
        "bank_account_number": "Bankszamlaszam",
    },
    "CZ": {
        "applicant_full_name": "Cele jmeno",
        "date_of_birth": "Datum narozeni",
        "residential_address": "Adresa bydliste",
        "declared_net_monthly_income": "Cisty mesicni prijem",
        "requested_loan_amount": "Pozadovana castka uveru",
        "loan_term_weeks": "Doba splaceni (tydny)",
        "employer_name": "Zamestnavatel",
        "bank_account_number": "Cislo bankovniho uctu",
    },
}


class LoanApplicationAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )

    def extract_loan_application(self, ocr_text: str, market: str) -> dict:
        """
        Extract declared fields from a loan application form.
        Returns a dict with field_name -> {value, confidence, label}.
        """
        market_labels = MARKET_LABELS.get(market, MARKET_LABELS["PL"])

        system_prompt = f"""You are a loan application form extraction specialist for {market} market.
Extract all declared fields from the loan application form text provided.
Return a JSON object where each key is a field name and the value is an object with:
  - value: the extracted value (null if not found)
  - confidence: your confidence 0-100
  - label: the local language label for this field

Required fields to extract: {json.dumps(LOAN_APP_FIELDS)}
Local language labels for {market}: {json.dumps(market_labels)}

Return ONLY valid JSON. No markdown, no explanation."""

        user_prompt = f"""Market: {market}
Loan Application Form Text:
{ocr_text}

Extract all declared fields:"""

        try:
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ])
            content = response.content.strip()
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            result = json.loads(content)
            return result
        except Exception as e:
            return {field: {"value": None, "confidence": 0, "label": field} for field in LOAN_APP_FIELDS}
