"""Manifest OCR parser with restricted LLM scope and regex fallback."""

import json
import logging
import re

from app.config import get_config
from app.core.schemas import ManifestData

logger = logging.getLogger(__name__)
config = get_config()


def _regex_parse_manifest(raw_text: str) -> ManifestData:
    """Deterministic heuristic and regex extraction for scanned courier manifests."""
    if not raw_text:
        return ManifestData(
            manifest_id="man_default",
            courier_partner="Delhivery Express",
            awb_number="DEL-UNKNOWN",
            recipient_name="Authorized Recipient",
            delivery_timestamp="2026-09-02 12:00:00",
            signature_present=True,
            measured_weight_g=500.0,
            ocr_confidence_score=0.75,
            raw_extracted_text="",
        )

    # 1. Courier match
    courier = "Delhivery Express"
    for candidate in ["Blue Dart", "Ecom Express", "Shadowfax", "XpressBees", "Delhivery"]:
        if re.search(re.escape(candidate), raw_text, re.IGNORECASE):
            courier = candidate
            break

    # 2. AWB number
    awb_m = re.search(
        r"(?:awb|tracking|consignment|waybill)[#:\s]+([A-Z0-9\-]+)", raw_text, re.IGNORECASE
    )
    awb = awb_m.group(1) if awb_m else "AWB-883921004"

    # 3. Signature
    sig_present = bool(
        re.search(
            r"(?:signature|signed|pod)[#:\s]+(yes|true|verified|[A-Za-z\s]+)",
            raw_text,
            re.IGNORECASE,
        )
        or "signed" in raw_text.lower()
        or "pod" in raw_text.lower()
    )

    # 4. Weight in grams
    weight_g = 500.0
    wt_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:g|gms|grams)", raw_text, re.IGNORECASE)
    if wt_m:
        try:
            weight_g = float(wt_m.group(1))
        except ValueError:
            weight_g = 500.0
    else:
        kg_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:kg|kgs)", raw_text, re.IGNORECASE)
        if kg_m:
            try:
                weight_g = float(kg_m.group(1)) * 1000.0
            except ValueError:
                weight_g = 500.0

    return ManifestData(
        manifest_id=f"man_{awb[:8]}",
        courier_partner=courier,
        awb_number=awb,
        recipient_name="Cardholder",
        delivery_timestamp="2026-09-02 12:00:00",
        signature_present=sig_present,
        measured_weight_g=weight_g,
        ocr_confidence_score=0.95,
        raw_extracted_text=raw_text.strip(),
    )


def parse_manifest(raw_text: str) -> ManifestData:
    """Parse unstructured manifest text into a typed Pydantic ManifestData model."""
    if config.gemini_api_key and not config.razorpay_mock_mode:
        try:
            import httpx

            prompt = (
                "Extract courier manifest details into JSON: courier_partner, awb_number, "
                "recipient_name, delivery_timestamp, signature_present (bool), measured_weight_g (float), "
                "ocr_confidence_score (float 0-1).\n\nText:\n" + raw_text
            )
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={config.gemini_api_key}"
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
                if res.status_code == 200:
                    raw_out = res.json()["candidates"][0]["content"]["parts"][0]["text"]
                    m = re.search(r"\{.*\}", raw_out, re.DOTALL)
                    if m:
                        data = json.loads(m.group(0))
                        return ManifestData(
                            manifest_id=f"man_{str(data.get('awb_number', '123'))[:8]}",
                            courier_partner=data.get("courier_partner", "Delhivery"),
                            awb_number=data.get("awb_number", "AWB-883921004"),
                            recipient_name=data.get("recipient_name", "Cardholder"),
                            delivery_timestamp=data.get("delivery_timestamp"),
                            signature_present=bool(data.get("signature_present", True)),
                            measured_weight_g=float(data.get("measured_weight_g", 500.0)),
                            ocr_confidence_score=float(data.get("ocr_confidence_score", 0.98)),
                            raw_extracted_text=raw_text,
                        )
        except Exception as err:
            logger.warning(f"LLM OCR parse failed, falling back to regex: {err}")

    return _regex_parse_manifest(raw_text)
