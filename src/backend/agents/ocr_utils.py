"""
IPF IPA PoC - OCR Utility Module
Handles document text extraction using Tesseract OCR.
Supports: JPEG, PNG, TIFF (via pytesseract), PDF (via pdf2image + pytesseract)
Languages: Polish (pol), Romanian (ron), Hungarian (hun), Czech (ces), English (eng)
"""
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Graceful imports - OCR is optional
try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract not installed - OCR disabled, LLM vision will be used")

try:
    from pdf2image import convert_from_bytes
    PDF2IMAGE_AVAILABLE = True
except ImportError:
    PDF2IMAGE_AVAILABLE = False
    logger.warning("pdf2image not installed - PDF OCR disabled")

# Tesseract language pack for all supported markets
TESSERACT_LANGS = "pol+ron+hun+ces+eng"


def extract_text_from_image_bytes(file_bytes: bytes) -> tuple[str, float]:
    """
    Extract text from image bytes using Tesseract OCR.
    Returns: (extracted_text, average_confidence 0-100)
    """
    if not TESSERACT_AVAILABLE:
        return "", 0.0

    try:
        image = Image.open(io.BytesIO(file_bytes))
        # Convert to RGB if necessary
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Get text with confidence data
        data = pytesseract.image_to_data(
            image,
            lang=TESSERACT_LANGS,
            output_type=pytesseract.Output.DICT
        )
        
        # Extract text and average confidence
        words = []
        confidences = []
        for i, word in enumerate(data["text"]):
            word = word.strip()
            conf = data["conf"][i]
            if word and conf > 0:
                words.append(word)
                confidences.append(float(conf))

        text = " ".join(words)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        return text, avg_confidence / 100.0  # Normalize to 0-1

    except Exception as e:
        logger.error(f"OCR error on image: {e}")
        return "", 0.0


def extract_text_from_pdf_bytes(file_bytes: bytes) -> tuple[str, float]:
    """
    Extract text from PDF bytes.
    Strategy 1: pypdf direct text extraction (works for text-based PDFs like our mocks)
    Strategy 2: pdf2image + Tesseract (for scanned/image PDFs, needs poppler)
    Returns: (extracted_text, confidence 0.0-1.0)
    """
    # Strategy 1: pypdf direct text extraction (fast, no poppler needed)
    try:
        from pypdf import PdfReader
        import io as _io
        reader = PdfReader(_io.BytesIO(file_bytes))
        pages_text = []
        for page in reader.pages[:3]:
            t = page.extract_text()
            if t:
                pages_text.append(t.strip())
        combined = "\n".join(pages_text)
        if combined and len(combined.strip()) > 20:
            logger.info(f"PDF text extracted via pypdf: {len(combined)} chars")
            return combined, 0.90  # High confidence for direct text extraction
    except Exception as e:
        logger.warning(f"pypdf extraction failed: {e}")

    # Strategy 2: pdf2image + Tesseract (for scanned PDFs)
    if TESSERACT_AVAILABLE and PDF2IMAGE_AVAILABLE:
        try:
            images = convert_from_bytes(file_bytes, dpi=300)
            all_text = []
            all_confidences = []
            for image in images[:3]:
                img_bytes = io.BytesIO()
                image.save(img_bytes, format="PNG")
                text, conf = extract_text_from_image_bytes(img_bytes.getvalue())
                if text:
                    all_text.append(text)
                    all_confidences.append(conf)
            combined_text = "\n\n".join(all_text)
            avg_conf = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            return combined_text, avg_conf
        except Exception as e:
            logger.error(f"PDF OCR error: {e}")

    return "", 0.0


def extract_text(file_bytes: bytes, content_type: str = "") -> tuple[str, float]:
    """
    Main entry point: extract text from any supported document format.
    Returns: (extracted_text, confidence 0.0-1.0)
    Falls back gracefully if OCR libraries not available.
    """
    if not file_bytes:
        return "", 0.0

    content_type = (content_type or "").lower()

    if "pdf" in content_type:
        return extract_text_from_pdf_bytes(file_bytes)
    elif any(t in content_type for t in ("jpeg", "jpg", "png", "tiff", "tif")):
        return extract_text_from_image_bytes(file_bytes)
    else:
        # Try image first, then PDF
        text, conf = extract_text_from_image_bytes(file_bytes)
        if not text:
            text, conf = extract_text_from_pdf_bytes(file_bytes)
        return text, conf


def is_ocr_available() -> bool:
    """Check if OCR is available."""
    return TESSERACT_AVAILABLE


def get_ocr_status() -> dict:
    """Return OCR availability status for health check."""
    return {
        "tesseract_available": TESSERACT_AVAILABLE,
        "pdf2image_available": PDF2IMAGE_AVAILABLE,
        "supported_languages": TESSERACT_LANGS if TESSERACT_AVAILABLE else None,
        "mode": "full_ocr" if (TESSERACT_AVAILABLE and PDF2IMAGE_AVAILABLE) else
                "image_only" if TESSERACT_AVAILABLE else
                "llm_vision_fallback"
    }

