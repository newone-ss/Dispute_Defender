"""Regulatory Policy RAG for dynamic NPCI UDIR and Visa CE 3.0 clause retrieval."""

import logging
from typing import List

from app.core.doc_loader import get_chroma_client
from app.core.schemas import PolicyCitation

logger = logging.getLogger(__name__)

_STATIC_POLICY_CITATIONS = {
    "npci.udir.pnr": [
        PolicyCitation(
            network="NPCI",
            clause_id="UDIR-2.1",
            text="Product Not Received: Proof of shipment, GPS confirmation within 100m, and OTP constitute compelling evidence.",
            source_file="npci_udir.pdf",
            policy_version="2026.1.0",
        ),
        PolicyCitation(
            network="VISA",
            clause_id="CE3.0-2.2a",
            text="Merchandise Not Received: Delivery to billing address verified via carrier tracking, signature, or doorstep GPS coordinates reverses chargeback.",
            source_file="visa_ce30.pdf",
            policy_version="2026.1.0",
        ),
    ],
    "visa.rc.13.1": [
        PolicyCitation(
            network="VISA",
            clause_id="CE3.0-13.1",
            text="Compelling Evidence 3.0: Two qualifying data points including verified doorstep GPS proximity and electronic POD shift liability to issuer.",
            source_file="visa_ce30.pdf",
            policy_version="2026.1.0",
        ),
    ],
    "npci.udir.defective": [
        PolicyCitation(
            network="NPCI",
            clause_id="UDIR-2.2b",
            text="Open Box Delivery (OBD): Delivery agent OTP entry legally certifies the cardholder physically examined and accepted contents prior to delivery completion.",
            source_file="npci_udir.pdf",
            policy_version="2026.1.0",
        ),
    ],
}


def retrieve_policy_clauses(reason_code: str) -> List[PolicyCitation]:
    """Retrieve regulatory rulebook citations for a given reason_code via ChromaDB or fallback."""
    rc = (reason_code or "npci.udir.pnr").lower().strip()
    citations: List[PolicyCitation] = list(_STATIC_POLICY_CITATIONS.get(rc, []))

    try:
        client = get_chroma_client()
        coll = client.get_or_create_collection(name="policy_documents")
        if coll.count() > 0:
            query = f"{reason_code} compelling evidence required proof delivery"
            res = coll.query(query_texts=[query], n_results=2)
            if res and res["documents"] and res["documents"][0]:
                for i, doc in enumerate(res["documents"][0]):
                    meta = res["metadatas"][0][i] if res["metadatas"] else {}
                    citations.append(
                        PolicyCitation(
                            network="NPCI/VISA",
                            clause_id=f"RAG-PASSAGE-{i + 1}",
                            text=doc[:250].strip() + "...",
                            source_file=meta.get("filename", "regulatory_kb"),
                            policy_version=meta.get("policy_version", "2026.1.0"),
                        )
                    )
    except Exception as err:
        logger.warning(f"ChromaDB policy query failed, using static registry: {err}")

    return citations
