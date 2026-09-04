"""Omnichannel RAG Fairness Gate — Evaluates prior customer communications.

Queries the "customer_chats" ChromaDB collection for WhatsApp/Email/Zendesk
messages related to a dispute. If a genuine prior complaint is detected
(product broken, wrong item, defective on arrival), triggers AUTO_ACCEPT
to avoid the ₹1,500 bad-faith bank penalty.

Two classification modes:
  - LLM (Gemini Flash): When GEMINI_API_KEY is configured
  - Keyword heuristic: Deterministic fallback when no LLM key is available
"""

import json
import logging
import re
from typing import Optional, List, Dict, Any

from core.config import get_settings
from core.schemas import RAGFairnessResult

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Complaint keyword patterns for deterministic fallback ──────────────────

_COMPLAINT_PATTERNS = [
    r"\b(?:broken|damaged|cracked|shattered)\b",
    r"\b(?:defective|not\s+working|malfunctioning|dead\s+on\s+arrival)\b",
    r"\b(?:wrong\s+item|wrong\s+product|wrong\s+size|wrong\s+colour|wrong\s+color)\b",
    r"\b(?:missing\s+parts?|missing\s+accessories?|missing\s+components?|incomplete)\b",
    r"\b(?:not\s+as\s+described|different\s+(?:from|than)\s+(?:what|listing|photo))\b",
    r"\b(?:refund|return|replacement|exchange)\b.*\b(?:please|want|need|request)\b",
    r"\b(?:terrible|horrible|worst|disgusted|unacceptable)\b.*\b(?:quality|condition|product)\b",
]
_COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in _COMPLAINT_PATTERNS]


def _keyword_classify(messages: List[str]) -> tuple[bool, str]:
    """Deterministic keyword-based complaint classifier.

    Returns (is_genuine_complaint, summary_text).
    """
    matched_keywords = set()
    complaint_messages = []

    for msg in messages:
        for pattern in _COMPILED_PATTERNS:
            match = pattern.search(msg)
            if match:
                matched_keywords.add(match.group(0).lower())
                complaint_messages.append(msg[:150])
                break

    if matched_keywords:
        summary = (
            f"Keyword analysis detected genuine prior complaint. "
            f"Matched indicators: {', '.join(sorted(matched_keywords))}. "
            f"Found in {len(complaint_messages)} message(s) across customer communications."
        )
        return True, summary

    return False, ""


async def _llm_classify(messages: List[str]) -> tuple[bool, str, float]:
    """LLM-based complaint classifier using Gemini Flash.

    Returns (is_genuine_complaint, summary_text, confidence).
    """
    if not settings.gemini_api_key:
        return False, "", 0.0

    try:
        import httpx

        combined = "\n---\n".join(msg[:500] for msg in messages[:10])
        prompt = f"""You are analyzing customer support communications for a chargeback dispute investigation.

Determine if the customer raised a GENUINE product complaint (defective, broken, wrong item, 
damaged, missing parts, not as described) BEFORE filing a chargeback with their bank.

Customer messages:
{combined}

Respond in JSON format:
{{
  "is_genuine_complaint": true/false,
  "confidence": 0.0-1.0,
  "summary": "Brief explanation of what was found"
}}

Only mark as genuine complaint if the customer explicitly reported a product issue.
Buyer's remorse, price complaints, or delivery timing complaints are NOT genuine product defects."""

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.gemini_api_key}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(
                url,
                json={"contents": [{"parts": [{"text": prompt}]}]},
            )
            if res.status_code == 200:
                resp_json = res.json()
                raw_out = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                json_match = re.search(r"\{.*\}", raw_out, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    return (
                        bool(parsed.get("is_genuine_complaint", False)),
                        parsed.get("summary", ""),
                        float(parsed.get("confidence", 0.5)),
                    )

    except Exception as e:
        logger.warning(f"LLM complaint classification failed: {e}")

    return False, "", 0.0


def evaluate_rag_fairness_sync(
    dispute_id: str = "",
    order_id: str = "",
) -> RAGFairnessResult:
    """Synchronous RAG fairness gate for background task pipeline.

    Queries ChromaDB for prior customer communications and classifies
    whether a genuine complaint exists using keyword analysis.
    """
    try:
        from core.doc_loader import get_chroma_client
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="customer_chats")

        if collection.count() == 0:
            return RAGFairnessResult(triggered=False, method="keyword", confidence=0.0)

        # Query by dispute_id and order_id
        query_text = f"complaint defective broken damaged wrong item {dispute_id} {order_id}"
        results = collection.query(
            query_texts=[query_text],
            n_results=10,
            where={"$or": [
                {"dispute_id": dispute_id},
                {"order_id": order_id},
            ]} if dispute_id or order_id else None,
        )

        if not results or not results["documents"] or not results["documents"][0]:
            return RAGFairnessResult(triggered=False, method="keyword", confidence=0.0)

        messages = results["documents"][0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        # Build matched chat records
        matched_chats = []
        for i, msg in enumerate(messages):
            meta = metadatas[i] if i < len(metadatas) else {}
            dist = distances[i] if i < len(distances) else 1.0
            matched_chats.append({
                "message": msg[:300],
                "channel": meta.get("channel", "unknown"),
                "timestamp": meta.get("timestamp", ""),
                "dispute_id": meta.get("dispute_id", ""),
                "similarity": round(max(0.0, 1.0 - dist), 3),
            })

        # Filter to only chats that match this dispute/order
        relevant_chats = [
            c for c in matched_chats
            if c["dispute_id"] == dispute_id
            or (order_id and c.get("order_id") == order_id)
            or c["similarity"] > 0.6
        ]

        if not relevant_chats:
            return RAGFairnessResult(
                triggered=False, method="keyword", confidence=0.0, matched_chats=matched_chats[:3]
            )

        relevant_messages = [c["message"] for c in relevant_chats]
        is_complaint, summary = _keyword_classify(relevant_messages)

        return RAGFairnessResult(
            triggered=is_complaint,
            summary=summary if is_complaint else "No genuine prior complaint detected in customer communications.",
            matched_chats=relevant_chats[:5],
            confidence=0.85 if is_complaint else 0.2,
            method="keyword",
        )

    except Exception as e:
        logger.warning(f"RAG fairness gate evaluation failed: {e}")
        return RAGFairnessResult(triggered=False, method="keyword", confidence=0.0)


async def evaluate_rag_fairness(
    dispute_id: str = "",
    order_id: str = "",
) -> RAGFairnessResult:
    """Async RAG fairness gate — uses LLM when available, keyword fallback otherwise.

    This is the primary entry point called from the webhook processing pipeline.
    """
    try:
        from core.doc_loader import get_chroma_client
        client = get_chroma_client()
        collection = client.get_or_create_collection(name="customer_chats")

        if collection.count() == 0:
            return RAGFairnessResult(triggered=False, method="keyword", confidence=0.0)

        query_text = f"complaint defective broken damaged wrong item {dispute_id} {order_id}"

        where_filter = None
        if dispute_id or order_id:
            conditions = []
            if dispute_id:
                conditions.append({"dispute_id": dispute_id})
            if order_id:
                conditions.append({"order_id": order_id})
            where_filter = {"$or": conditions} if len(conditions) > 1 else conditions[0]

        results = collection.query(
            query_texts=[query_text],
            n_results=10,
            where=where_filter,
        )

        if not results or not results["documents"] or not results["documents"][0]:
            return RAGFairnessResult(triggered=False, method="keyword", confidence=0.0)

        messages = results["documents"][0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        matched_chats = []
        for i, msg in enumerate(messages):
            meta = metadatas[i] if i < len(metadatas) else {}
            dist = distances[i] if i < len(distances) else 1.0
            matched_chats.append({
                "message": msg[:300],
                "channel": meta.get("channel", "unknown"),
                "timestamp": meta.get("timestamp", ""),
                "dispute_id": meta.get("dispute_id", ""),
                "similarity": round(max(0.0, 1.0 - dist), 3),
            })

        relevant_chats = [
            c for c in matched_chats
            if c["dispute_id"] == dispute_id
            or c["similarity"] > 0.6
        ]

        if not relevant_chats:
            return RAGFairnessResult(
                triggered=False, method="keyword", confidence=0.0, matched_chats=matched_chats[:3]
            )

        relevant_messages = [c["message"] for c in relevant_chats]

        # Try LLM classification first
        if settings.gemini_api_key and not settings.mock_mode:
            is_complaint, summary, confidence = await _llm_classify(relevant_messages)
            if summary:
                return RAGFairnessResult(
                    triggered=is_complaint,
                    summary=summary,
                    matched_chats=relevant_chats[:5],
                    confidence=confidence,
                    method="llm",
                )

        # Fall back to keyword classification
        is_complaint, summary = _keyword_classify(relevant_messages)
        return RAGFairnessResult(
            triggered=is_complaint,
            summary=summary if is_complaint else "No genuine prior complaint detected in customer communications.",
            matched_chats=relevant_chats[:5],
            confidence=0.85 if is_complaint else 0.2,
            method="keyword",
        )

    except Exception as e:
        logger.warning(f"RAG fairness gate evaluation failed: {e}")
        return RAGFairnessResult(triggered=False, method="keyword", confidence=0.0)
