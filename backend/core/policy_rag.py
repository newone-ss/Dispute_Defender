"""Policy RAG — Retrieves regulatory evidence requirements per reason_code.

Queries the "policy_documents" ChromaDB collection with the dispute's reason_code
and delivery_type to dynamically fetch the required evidence checklist from
Visa CE 3.0 and NPCI UDIR rulebooks.
"""

import json
import logging
from typing import Optional, List

from core.config import get_settings
from core.schemas import PolicyChecklistItem, PolicyChecklistOut

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Static evidence registry (deterministic fallback) ──────────────────────

_STATIC_CHECKLISTS = {
    "product_not_received": {
        "items": [
            PolicyChecklistItem(
                evidence_type="shipping_proof",
                description="Courier AWB tracking number with carrier delivery confirmation",
                required=True,
                regulatory_source="NPCI UDIR Section 2.1 / Visa CE 3.0 Section 2.2a",
            ),
            PolicyChecklistItem(
                evidence_type="gps_geofence",
                description="GPS-verified delivery within 100m of cardholder billing address",
                required=True,
                regulatory_source="NPCI UDIR Section 2.1 / Visa CE 3.0 Section 6.2",
            ),
            PolicyChecklistItem(
                evidence_type="otp_verification",
                description="Doorstep OTP verification matching cardholder registered mobile",
                required=True,
                regulatory_source="NPCI UDIR Section 2.1",
            ),
            PolicyChecklistItem(
                evidence_type="delivery_signature",
                description="Signed proof of delivery (POD) or electronic acknowledgement",
                required=True,
                regulatory_source="NPCI UDIR Section 2.1 / Visa CE 3.0 Section 2.2a",
            ),
            PolicyChecklistItem(
                evidence_type="weight_reconciliation",
                description="Weight measurement at origin hub vs delivery point within 5% tolerance",
                required=False,
                regulatory_source="NPCI UDIR Section 2.1",
            ),
        ],
        "citations": [
            "NPCI UDIR Section 2.1: Product Not Received — 7 working day response window",
            "Visa CE 3.0 Section 2.3: GPS + OTP + Tracking = Strong Compelling Evidence",
        ],
    },
    "defective_merchandise": {
        "items": [
            PolicyChecklistItem(
                evidence_type="customer_communication",
                description="Customer support interaction history (no prior complaint before chargeback)",
                required=True,
                regulatory_source="NPCI UDIR Section 2.2 / Visa CE 3.0 Section 3.2c",
            ),
            PolicyChecklistItem(
                evidence_type="quality_inspection",
                description="Quality control inspection report from fulfillment center",
                required=True,
                regulatory_source="Visa CE 3.0 Section 3.2a",
            ),
            PolicyChecklistItem(
                evidence_type="obd_verification",
                description="Open Box Delivery OTP proves physical inspection at doorstep (if OBD)",
                required=False,
                regulatory_source="NPCI UDIR Section 3.2 / Visa CE 3.0 Section 3.2b",
            ),
            PolicyChecklistItem(
                evidence_type="return_offered",
                description="Return merchandise authorization (RMA) offered but not used",
                required=False,
                regulatory_source="Visa CE 3.0 Section 3.2a",
            ),
        ],
        "citations": [
            "NPCI UDIR Section 2.2: Defective Merchandise — 10 working day response",
            "NPCI UDIR Section 3.2: OBD OTP constitutes legal proof of inspection",
            "Visa CE 3.0 Section 3.2b: OBD OTP = Strong Compelling Evidence",
        ],
    },
    "fraudulent_transaction": {
        "items": [
            PolicyChecklistItem(
                evidence_type="device_fingerprint",
                description="Device ID matching checkout session and TWO prior undisputed transactions",
                required=True,
                regulatory_source="Visa CE 3.0 Section 5.2b",
            ),
            PolicyChecklistItem(
                evidence_type="gps_geofence",
                description="Delivery to cardholder's registered address with GPS verification",
                required=True,
                regulatory_source="Visa CE 3.0 Section 5.2c",
            ),
            PolicyChecklistItem(
                evidence_type="otp_verification",
                description="OTP sent to cardholder's registered mobile number",
                required=True,
                regulatory_source="Visa CE 3.0 Section 5.2d / NPCI UDIR Section 2.3",
            ),
            PolicyChecklistItem(
                evidence_type="ip_address",
                description="IP address matching cardholder's historical pattern",
                required=False,
                regulatory_source="Visa CE 3.0 Section 5.2a",
            ),
        ],
        "citations": [
            "NPCI UDIR Section 2.3: Fraudulent Transaction — 5 working day response",
            "Visa CE 3.0 Section 5.3: Two qualifying data points + delivery confirmation reverses chargeback",
        ],
    },
}


def get_policy_checklist(
    reason_code: str,
    delivery_type: str = "STANDARD",
    use_rag: bool = True,
) -> PolicyChecklistOut:
    """Retrieve the evidence checklist for a given reason_code.

    Strategy:
    1. If ChromaDB has policy_documents, query for reason_code + delivery_type
       to enrich the checklist with regulatory citations.
    2. Fall back to the static registry for the structured checklist items.
    """
    # Normalize
    rc = (reason_code or "product_not_received").lower().strip()
    dt = (delivery_type or "STANDARD").upper().strip()

    # Start with static checklist
    static = _STATIC_CHECKLISTS.get(rc, _STATIC_CHECKLISTS.get("product_not_received"))
    items = list(static["items"])
    citations = list(static["citations"])
    retrieval_confidence = 0.85  # Static baseline

    # Attempt RAG enrichment from ChromaDB
    if use_rag:
        try:
            from core.doc_loader import get_chroma_client
            client = get_chroma_client()
            collection = client.get_or_create_collection(name="policy_documents")

            if collection.count() > 0:
                query_text = f"{reason_code} {delivery_type} evidence requirements compelling evidence"
                results = collection.query(query_texts=[query_text], n_results=5)

                if results and results["documents"] and results["documents"][0]:
                    rag_citations = []
                    distances = results.get("distances", [[]])[0]
                    for i, doc in enumerate(results["documents"][0]):
                        source = ""
                        if results.get("metadatas") and results["metadatas"][0]:
                            source = results["metadatas"][0][i].get("source", "")
                        snippet = doc[:200].strip()
                        rag_citations.append(f"[{source}] {snippet}...")

                    citations.extend(rag_citations)

                    # Average similarity score
                    if distances:
                        avg_dist = sum(distances) / len(distances)
                        retrieval_confidence = max(0.0, min(1.0, 1.0 - avg_dist))

                    logger.info(
                        f"Policy RAG: Retrieved {len(rag_citations)} passages for "
                        f"reason_code={rc}, delivery_type={dt}, confidence={retrieval_confidence:.2f}"
                    )

        except Exception as e:
            logger.warning(f"Policy RAG query failed, using static checklist: {e}")

    # OBD-specific adjustments
    if dt == "OPEN_BOX" and rc == "defective_merchandise":
        # Elevate OBD verification to required
        for item in items:
            if item.evidence_type == "obd_verification":
                item.required = True
                item.description = (
                    "Open Box Delivery OTP — Customer physically inspected item at doorstep "
                    "before entering OTP. This constitutes LEGAL PROOF of acceptance per NPCI UDIR Section 3.2."
                )

    return PolicyChecklistOut(
        reason_code=rc,
        delivery_type=dt,
        checklist=items,
        regulatory_citations=citations,
        retrieval_confidence=round(retrieval_confidence, 3),
    )
