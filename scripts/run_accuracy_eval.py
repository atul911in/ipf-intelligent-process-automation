"""
IPF IPA PoC - Accuracy Evaluation Harness
Tests the document extraction pipeline against ground-truth JSON fixtures.

Usage:
    python scripts/run_accuracy_eval.py                    # All markets
    python scripts/run_accuracy_eval.py --market PL        # Poland only
    python scripts/run_accuracy_eval.py --market CZ --verbose

Output:
    - Per-field accuracy report
    - Per-document accuracy report
    - Overall accuracy score
    - Saves results to test-data/eval-results/
"""
import json
import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# --- Config ---
BASE_DIR = Path(__file__).parent.parent / "test-data"
RESULTS_DIR = BASE_DIR / "eval-results"
RESULTS_DIR.mkdir(exist_ok=True)

MARKETS = ["poland", "romania", "hungary", "czech"]
CATEGORIES = ["identity", "address", "income", "bank", "residence"]


def load_ground_truth(market_dir: str, category: str) -> list:
    path = BASE_DIR / market_dir / category / "ground-truth.json"
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        print(f"  Warning: Could not load {path}: {e}")
        return []


def load_mock_pdf(market_dir: str, category: str, doc_id: str) -> tuple:
    """Load a generated mock PDF for OCR testing."""
    pdf_path = BASE_DIR / market_dir / category / "generated" / f"{doc_id}.pdf"
    if not pdf_path.exists():
        return None, None
    with open(pdf_path, "rb") as f:
        return f.read(), "application/pdf"


def compare_field_value(extracted: str, expected: str) -> tuple:
    """
    Compare extracted vs expected field value.
    Returns: (is_match: bool, similarity: float, method: str)
    """
    if extracted is None and expected is None:
        return True, 1.0, "both_null"
    if extracted is None or expected is None:
        return False, 0.0, "one_null"

    extracted_clean = str(extracted).strip().lower()
    expected_clean = str(expected).strip().lower()

    # Exact match
    if extracted_clean == expected_clean:
        return True, 1.0, "exact"

    # Fuzzy match (similarity >= 0.85 = pass)
    similarity = SequenceMatcher(None, extracted_clean, expected_clean).ratio()
    if similarity >= 0.85:
        return True, similarity, "fuzzy"

    return False, similarity, "mismatch"


def evaluate_extraction(extracted_fields: list, ground_truth: dict) -> dict:
    """
    Compare extracted fields against ground truth.
    Returns accuracy metrics for a single document.
    """
    gt_flat = {}
    for key, value in ground_truth.items():
        if isinstance(value, (str, int, float, bool)) and key not in ("document_id", "document_type", "market", "language", "source_description", "expected_confidence", "notes"):
            gt_flat[key] = str(value)

    total_fields = len(gt_flat)
    if total_fields == 0:
        return {"accuracy": 0.0, "fields_total": 0, "fields_matched": 0, "details": []}

    matched = 0
    details = []

    for field_name, expected_value in gt_flat.items():
        # Find extracted value for this field
        extracted_value = None
        for ef in extracted_fields:
            if ef.get("field_name") == field_name or ef.get("field_name", "").replace("_", " ") == field_name.replace("_", " "):
                extracted_value = ef.get("value") or ef.get("extracted_value")
                break

        is_match, similarity, method = compare_field_value(extracted_value, expected_value)
        if is_match:
            matched += 1

        details.append({
            "field": field_name,
            "expected": expected_value,
            "extracted": extracted_value,
            "match": is_match,
            "similarity": round(similarity, 3),
            "method": method
        })

    accuracy = matched / total_fields if total_fields > 0 else 0.0
    return {
        "accuracy": round(accuracy, 3),
        "fields_total": total_fields,
        "fields_matched": matched,
        "details": details
    }


def run_ocr_extraction(file_bytes: bytes, content_type: str, document_type: str, market: str) -> list:
    """Run the actual OCR + LLM extraction pipeline."""
    try:
        from src.backend.agents.ocr_utils import extract_text
        from src.backend.agents.document_agent import DocumentAgent

        # Step 1: OCR
        ocr_text, confidence = extract_text(file_bytes, content_type)

        # Step 2: LLM extraction
        agent = DocumentAgent()
        input_text = ocr_text if ocr_text else f"[Mock PDF document type: {document_type}, market: {market}]"
        fields = agent.extract_fields(input_text, document_type, market)
        return fields
    except ImportError as e:
        print(f"  Note: Could not import extraction pipeline: {e}")
        return []
    except Exception as e:
        print(f"  Extraction error: {e}")
        return []


def run_eval(market_filter: str = None, verbose: bool = False, use_llm: bool = False) -> dict:
    """Run the full accuracy evaluation."""
    print("\n" + "="*60)
    print("IPF IPA PoC - Accuracy Evaluation")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if use_llm:
        print("Mode: LIVE (OCR + LLM extraction)")
    else:
        print("Mode: DRY RUN (ground-truth field matching only)")
    print("="*60)

    all_results = []
    summary_by_market = {}

    markets_to_eval = [market_filter.lower()] if market_filter else MARKETS

    for market_dir in markets_to_eval:
        market_results = []
        print(f"\n[{market_dir.upper()}]")

        for category in CATEGORIES:
            docs = load_ground_truth(market_dir, category)
            if not docs:
                continue

            print(f"  {category}: {len(docs)} documents")

            for doc in docs:
                doc_id = doc.get("document_id", "unknown")
                doc_type = doc.get("document_type", "identity_card")
                market_code = doc.get("market", market_dir[:2].upper())
                gt = doc.get("ground_truth", {})

                if use_llm:
                    # Run live extraction
                    file_bytes, content_type = load_mock_pdf(market_dir, category, doc_id)
                    if file_bytes:
                        extracted_fields = run_ocr_extraction(file_bytes, content_type, doc_type, market_code)
                    else:
                        print(f"    Skipping {doc_id}: no PDF found")
                        continue
                else:
                    # Dry run: simulate extraction from ground truth (validates eval logic)
                    extracted_fields = [
                        {"field_name": k, "value": v, "confidence": 90}
                        for k, v in gt.items()
                        if isinstance(v, (str, int, float))
                    ]

                eval_result = evaluate_extraction(extracted_fields, gt)
                result = {
                    "document_id": doc_id,
                    "market": market_code,
                    "category": category,
                    "document_type": doc_type,
                    "notes": doc.get("notes", ""),
                    **eval_result
                }
                market_results.append(result)
                all_results.append(result)

                acc_str = f"{eval_result['accuracy']*100:.0f}%"
                match_str = f"{eval_result['fields_matched']}/{eval_result['fields_total']}"
                status = "PASS" if eval_result["accuracy"] >= 0.90 else "WARN" if eval_result["accuracy"] >= 0.70 else "FAIL"
                print(f"    {doc_id}: {acc_str} ({match_str} fields) [{status}]")

                if verbose:
                    for d in eval_result["details"]:
                        icon = "OK" if d["match"] else "XX"
                        print(f"      {icon} {d['field']}: expected='{d['expected']}' extracted='{d['extracted']}' ({d['similarity']:.2f})")

        if market_results:
            avg_acc = sum(r["accuracy"] for r in market_results) / len(market_results)
            total_fields = sum(r["fields_total"] for r in market_results)
            matched_fields = sum(r["fields_matched"] for r in market_results)
            summary_by_market[market_dir] = {
                "documents": len(market_results),
                "avg_accuracy": round(avg_acc, 3),
                "total_fields": total_fields,
                "matched_fields": matched_fields,
                "field_accuracy": round(matched_fields / total_fields, 3) if total_fields else 0
            }

    # Overall summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for market, stats in summary_by_market.items():
        print(f"  {market.upper()}: {stats['avg_accuracy']*100:.0f}% avg accuracy | "
              f"{stats['matched_fields']}/{stats['total_fields']} fields | "
              f"{stats['documents']} documents")

    if all_results:
        overall_acc = sum(r["accuracy"] for r in all_results) / len(all_results)
        total_f = sum(r["fields_total"] for r in all_results)
        matched_f = sum(r["fields_matched"] for r in all_results)
        print(f"\n  OVERALL: {overall_acc*100:.0f}% avg accuracy | {matched_f}/{total_f} fields | {len(all_results)} documents")
        target_met = "PASS (>=90%)" if overall_acc >= 0.90 else f"BELOW TARGET (need 90%, got {overall_acc*100:.0f}%)"
        print(f"  PoC Exit Criterion: {target_met}")

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = RESULTS_DIR / f"eval_{timestamp}.json"
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": timestamp,
            "mode": "live" if use_llm else "dry_run",
            "market_filter": market_filter,
            "summary": summary_by_market,
            "documents": all_results
        }, f, indent=2, ensure_ascii=False)

    print(f"\n  Results saved: {results_file.name}")
    print("="*60)

    return {"summary": summary_by_market, "documents": all_results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="IPF PoC Accuracy Evaluation")
    parser.add_argument("--market", type=str, help="Market to evaluate (poland, romania, hungary, czech)")
    parser.add_argument("--verbose", action="store_true", help="Show per-field results")
    parser.add_argument("--live", action="store_true", help="Run live LLM extraction (requires OPENAI_API_KEY)")
    args = parser.parse_args()

    if args.live:
        from dotenv import load_dotenv
        load_dotenv()

    run_eval(market_filter=args.market, verbose=args.verbose, use_llm=args.live)
