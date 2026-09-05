"""Backwards-compatibility proxy for the AI Engine.

Canonical implementation is located in `app.core.ai_engine`.
"""

from app.core.ai_engine import (
    GEMINI_API_KEY,
    GEMINI_EMBEDDING_MODEL,
    GEMINI_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
    GeminiChromaEmbeddingFunction,
    embeddings,
    evaluate_dispute_fairness,
    gemini_llm,
    get_embeddings,
    get_gemini_llm,
    get_openrouter_llm,
    llm_gemini,
    llm_openrouter,
    openrouter_llm,
)

__all__ = [
    "GEMINI_API_KEY",
    "GEMINI_MODEL",
    "GEMINI_EMBEDDING_MODEL",
    "OPENROUTER_API_KEY",
    "OPENROUTER_MODEL",
    "embeddings",
    "get_embeddings",
    "GeminiChromaEmbeddingFunction",
    "llm_gemini",
    "gemini_llm",
    "get_gemini_llm",
    "llm_openrouter",
    "openrouter_llm",
    "get_openrouter_llm",
    "evaluate_dispute_fairness",
]
