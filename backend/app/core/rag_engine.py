"""Omnichannel Support RAG search for customer tickets and chat logs."""

import logging
from typing import List

from app.core.doc_loader import get_chroma_client
from app.core.schemas import ChatHit

logger = logging.getLogger(__name__)


def search_support_tickets(dispute_id: str, query: str = "") -> List[ChatHit]:
    """Retrieve prior customer communications from ChromaDB customer_chats collection."""
    try:
        client = get_chroma_client()
        coll = client.get_or_create_collection(name="customer_chats")
        if coll.count() == 0:
            return []

        search_text = query or f"complaint damaged defective broken missing wrong item {dispute_id}"
        results = coll.query(
            query_texts=[search_text],
            n_results=5,
            where={"dispute_id": dispute_id} if dispute_id else None,
        )

        if not results or not results["documents"] or not results["documents"][0]:
            return []

        hits: List[ChatHit] = []
        docs = results["documents"][0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, text in enumerate(docs):
            dist = distances[i] if i < len(distances) else 0.5
            similarity = round(max(0.0, 1.0 - dist), 3)
            meta = metas[i] if i < len(metas) else {}
            hits.append(
                ChatHit(
                    source=meta.get("channel", "support_chat"),
                    text=text[:300],
                    score=similarity,
                    timestamp=meta.get("timestamp"),
                )
            )

        return hits

    except Exception as err:
        logger.warning(f"ChromaDB chat query failed: {err}")
        return []
