"""
IPF IPA PoC - Document Processing Agent
Handles OCR extraction, field parsing, confidence scoring, and validation.
Uses OpenAI GPT-4o-mini for intelligent field extraction.
"""
import json
from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from ..core.config import settings


# Document schemas for field extraction
SCHEMAS = {
    "PL": {
        "identity_card": ["first_name", "last_name", "pesel", "document_number", "date_of_birth", "expiry_date", "sex", "nationality", "issuing_authority"],
        "utility_bill": ["provider_name", "customer_name", "customer_address", "invoice_date", "amount_due", "invoice_number", "billing_period"],
        "payslip": ["employer_name", "employee_name", "pay_period", "gross_salary", "net_salary", "employee_pesel", "position"]
    },
    "RO": {
        "identity_card": ["first_name", "last_name", "cnp", "document_number", "document_series", "date_of_birth", "expiry_date", "sex", "address"],
        "utility_bill": ["provider_name", "customer_name", "customer_address", "invoice_date", "amount_due", "invoice_number"],
        "payslip": ["employer_name", "employee_name", "pay_period", "gross_salary", "net_salary", "employee_cnp", "position"]
    },
    "HU": {
        "identity_card": ["first_name", "last_name", "personal_id_number", "document_number", "date_of_birth", "expiry_date", "mothers_name", "sex"],
        "address_card": ["card_holder_name", "personal_id_number", "permanent_address", "issue_date", "card_number"],
        "income_proof": ["employer_name", "employee_name", "gross_monthly_salary", "net_monthly_salary", "employment_start_date", "issue_date"]
    },
    "CZ": {
        "identity_card": ["first_name", "last_name", "rodne_cislo", "document_number", "date_of_birth", "expiry_date", "permanent_address", "sex"],
        "income_proof": ["employer_name", "employee_name", "gross_salary", "net_salary", "pay_period", "position"],
        "proof_of_residence": ["document_title", "holder_name", "address", "issue_date"]
    }
}


class DocumentAgent:
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            temperature=0
        )

    def extract_fields(self, ocr_text: str, document_type: str, market: str) -> list[dict]:
        """
        Extract structured fields from OCR text using LLM.
        Returns list of {field_name, value, confidence}.
        """
        schema_fields = SCHEMAS.get(market, {}).get(document_type, [])
        if not schema_fields:
            schema_fields = SCHEMAS.get(market, {}).get("identity_card", [])

        system_prompt = f"""You are a document extraction specialist for {market} market documents.
Extract the following fields from the document text provided.
For each field, provide:
- field_name: the field identifier
- value: the extracted value (null if not found)
- confidence: your confidence 0-100 that the extraction is correct

Required fields: {json.dumps(schema_fields)}

Return ONLY valid JSON array. No markdown, no explanation.
Example: [{{"field_name": "first_name", "value": "Jan", "confidence": 95}}]"""

        user_prompt = f"""Document type: {document_type}
Market: {market}

Document text:
{ocr_text}

Extract all required fields as JSON array:"""

        response = self.llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ])

        try:
            # Parse JSON response
            content = response.content.strip()
            if content.startswith("`"):
                content = content.split("`")[1]
                if content.startswith("json"):
                    content = content[4:]
            fields = json.loads(content)
            return fields
        except (json.JSONDecodeError, IndexError):
            # Fallback: return empty fields with zero confidence
            return [{"field_name": f, "value": None, "confidence": 0} for f in schema_fields]

    def extract_from_image(self, image_base64: str, document_type: str, market: str) -> list[dict]:
        """
        Extract fields directly from a document image using GPT-4o vision.
        """
        schema_fields = SCHEMAS.get(market, {}).get(document_type, [])
        if not schema_fields:
            schema_fields = ["first_name", "last_name", "document_number", "date_of_birth", "expiry_date"]

        system_prompt = f"""You are a document extraction specialist for {market} market.
Extract these fields from the document image: {json.dumps(schema_fields)}
For each field return: field_name, value (null if not found), confidence (0-100).
Return ONLY a valid JSON array."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=[
                {"type": "text", "text": f"Extract fields from this {document_type} document ({market} market):"},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
            ])
        ]

        # Use gpt-4o for vision (not mini)
        vision_llm = ChatOpenAI(model="gpt-4o", api_key=settings.OPENAI_API_KEY, temperature=0)
        response = vision_llm.invoke(messages)

        try:
            content = response.content.strip()
            if content.startswith("`"):
                content = content.split("`")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except (json.JSONDecodeError, IndexError):
            return [{"field_name": f, "value": None, "confidence": 0} for f in schema_fields]

    def generate_recommendation(self, application_id: str, all_extractions: list,
                                 all_validations: list) -> dict:
        """
        Generate a loan recommendation based on all document extractions.
        Returns: {recommendation: APPROVE/DECLINE/REFER, reasons: [...], confidence: int}
        """
        prompt = f"""Based on the following document extraction and validation results for loan application {application_id}, 
generate a recommendation. You are an AI assistant - the final decision will ALWAYS be made by a human.

Extraction Results:
{json.dumps(all_extractions, indent=2)}

Validation Results:
{json.dumps(all_validations, indent=2)}

Provide your recommendation as JSON:
{{
  "recommendation": "APPROVE" or "DECLINE" or "REFER",
  "reasons": ["reason 1", "reason 2"],
  "risk_indicators": ["indicator 1"],
  "confidence": 0-100
}}

IMPORTANT: This is a RECOMMENDATION only. A human credit assessor will make the final decision.
Return ONLY valid JSON."""

        response = self.llm.invoke([HumanMessage(content=prompt)])

        try:
            content = response.content.strip()
            if content.startswith("`"):
                content = content.split("`")[1]
                if content.startswith("json"):
                    content = content[4:]
            return json.loads(content)
        except (json.JSONDecodeError, IndexError):
            return {"recommendation": "REFER", "reasons": ["Unable to generate recommendation"], "confidence": 0}
