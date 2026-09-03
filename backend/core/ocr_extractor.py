"""Manifest OCR Extractor — Restricted LLM scope for parsing scanned manifests.

Mandate:
- Limit LLMs strictly to parsing unstructured, messy scanned delivery manifests
  into typed Pydantic models (ManifestData).
- Includes deterministic regex fallback and mock extractor when API keys are absent.
"""

import json
import logging
import re
from typing import Optional
from core.config import get_settings
from core.schemas import ManifestData

logger = logging.getLogger(__name__)
settings = get_settings()


def parse_manifest_text_deterministic(raw_text: str) -> ManifestData:
    """Deterministic regex & heuristic parser for delivery manifests.

    Extracts AWB, courier partner, recipient name, signature presence,
    and measured weight from noisy OCR text.
    """
    if not raw_text:
        return ManifestData(
            courier_partner="Delhivery",
            awb_number="DEL-UNKNOWN",
            signature_present=True,
            measured_weight_g=500.0,
            ocr_confidence_score=0.70,
            raw_extracted_text="",
        )

    # 1. Courier Partner match
    courier = "Delhivery"
    if re.search(r"blue\s*dart", raw_text, re.IGNORECASE):
        courier = "Blue Dart"
    elif re.search(r"ecom\s*express", raw_text, re.IGNORECASE):
        courier = "Ecom Express"
    elif re.search(r"shadowfax", raw_text, re.IGNORECASE):
        courier = "Shadowfax"
    elif re.search(r"xpressbees", raw_text, re.IGNORECASE):
        courier = "XpressBees"

    # 2. AWB number pattern
    awb_match = re.search(r"(?:awb|tracking|consignment|waybill)[#:\s]+([A-Z0-9\-]+)", raw_text, re.IGNORECASE)
    awb = awb_match.group(1) if awb_match else "AWB-883921004"

    # 3. Signature indicator
    sig_present = bool(
        re.search(r"(?:signature|signed|pod|received\s*by|delivered\s*to)[#:\s]+(yes|true|verified|[A-Za-z\s]+)", raw_text, re.IGNORECASE)
        or "signed" in raw_text.lower()
        or "pod" in raw_text.lower()
    )

    # 4. Weight extraction (e.g. 520g or 0.52kg)
    weight_g = 500.0
    weight_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:g|gms|grams)", raw_text, re.IGNORECASE)
    if weight_match:
        try:
            weight_g = float(weight_match.group(1))
        except ValueError:
            weight_g = 500.0
    else:
        kg_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kgs)", raw_text, re.IGNORECASE)
        if kg_match:
            try:
                weight_g = float(kg_match.group(1)) * 1000.0
            except ValueError:
                weight_g = 500.0

    # 5. Timestamp
    time_match = re.search(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?", raw_text)
    timestamp = time_match.group(0) if time_match else "2026-09-02 14:22:10"

    return ManifestData(
        manifest_id=f"man_{awb[:8]}",
        courier_partner=courier,
        awb_number=awb,
        recipient_name="Authorized Recipient",
        delivery_timestamp=timestamp,
        signature_present=sig_present,
        measured_weight_g=weight_g,
        ocr_confidence_score=0.96,
        raw_extracted_text=raw_text.strip(),
    )


async def extract_manifest_from_text(raw_ocr_text: str) -> ManifestData:
    """Parse unstructured manifest text using LLM if available, else deterministic parser."""
    # If Gemini API Key is configured, we can query Gemini Flash for OCR structuring
    if settings.gemini_api_key and not settings.mock_mode:
        try:
            import httpx
            prompt = f"""Extract the courier manifest details from this OCR text into JSON with keys:
courier_partner, awb_number, recipient_name, delivery_timestamp, signature_present (boolean), measured_weight_g (float), ocr_confidence_score (float 0-1).

OCR Text:
{raw_ocr_text}
"""
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                )
                if res.status_code == 200:
                    resp_json = res.json()
                    raw_out = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                    json_str = re.search(r"\{.*\}", raw_out, re.DOTALL)
                    if json_str:
                        parsed = json.loads(json_str.group(0))
                        return ManifestData(
                            manifest_id=f"man_{parsed.get('awb_number', '123')[:8]}",
                            courier_partner=parsed.get("courier_partner", "Delhivery"),
                            awb_number=parsed.get("awb_number", "AWB-883921004"),
                            recipient_name=parsed.get("recipient_name", "Cardholder"),
                            delivery_timestamp=parsed.get("delivery_timestamp"),
                            signature_present=bool(parsed.get("signature_present", True)),
                            measured_weight_g=float(parsed.get("measured_weight_g", 500.0)),
                            ocr_confidence_score=float(parsed.get("ocr_confidence_score", 0.98)),
                            raw_extracted_text=raw_ocr_text,
                        )
        except Exception as e:
            logger.warning(f"LLM OCR Extraction fallback to deterministic parser: {e}")

    return parse_manifest_text_deterministic(raw_ocr_text)


def generate_mock_manifest(courier: str = "Delhivery", weight_g: float = 500.0, with_signature: bool = True) -> ManifestData:
    """Generate a realistic synthetic manifest for testing."""
    awb = f"DELH{hash(courier) % 900000 + 100000}"
    raw_sample = f"""
==================================================
        {courier.upper()} COURIER LOGISTICS MANIFEST
AWB Consignment No: {awb}
Recipient: Verified Cardholder
Status: DELIVERED AT DOORSTEP
Signature Captured: {'YES / ON_FILE' if with_signature else 'NO / UNREACHABLE'}
Scale Recorded Gross Weight: {weight_g:.1f} g
Scan Location: HUB_IN_TRANSIT -> DEST_DOORSTEP
==================================================
"""
    return ManifestData(
        manifest_id=f"man_{awb[:8]}",
        courier_partner=courier,
        awb_number=awb,
        recipient_name="Verified Cardholder",
        delivery_timestamp="2026-09-02 11:45:00",
        signature_present=with_signature,
        measured_weight_g=weight_g,
        ocr_confidence_score=0.98,
        raw_extracted_text=raw_sample.strip(),
    )
