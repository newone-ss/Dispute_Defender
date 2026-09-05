"""Unit tests for the new AI Engine (Gemini embeddings, dual LLM, and dispute fairness evaluation)."""

from app.core.ai_engine import (
    GeminiChromaEmbeddingFunction,
    embeddings,
    evaluate_dispute_fairness,
    gemini_llm,
    get_embeddings,
    llm_gemini,
    llm_openrouter,
    openrouter_llm,
)


def test_gemini_embeddings_configuration():
    """Verify Gemini embeddings initialization and model pinning."""
    assert embeddings is not None
    assert embeddings.model in ("models/embedding-004", "models/gemini-embedding-001")

    # Test factory function with explicit model pinning
    emb = get_embeddings(api_key="test_custom_key", model="models/embedding-004")
    assert emb.model == "models/embedding-004"


def test_dual_llm_configuration():
    """Verify Gemini and OpenRouter LLM dual setup."""
    # LLM 1: Gemini
    assert gemini_llm is not None
    assert gemini_llm.model in ("gemini-1.5-flash", "gemini-2.5-flash")
    assert llm_gemini is gemini_llm

    # LLM 2: OpenRouter
    assert openrouter_llm is not None
    assert openrouter_llm.openai_api_base == "https://openrouter.ai/api/v1"
    assert openrouter_llm.model_name in (
        "meta-llama/llama-3.8b-instruct:free",
        "liquid/lfm-2.5-2.6b:free",
    )
    assert llm_openrouter is openrouter_llm


def test_chroma_embedding_function_adapter():
    """Verify Gemini Chroma embedding adapter exposes the expected call interface."""
    adapter = GeminiChromaEmbeddingFunction()
    assert hasattr(adapter, "__call__")
    assert hasattr(adapter, "embed_documents")
    assert hasattr(adapter, "embed_query")


def test_evaluate_dispute_fairness_empty_input():
    """Empty or whitespace text should default safely to CONTEST."""
    assert evaluate_dispute_fairness("") == "CONTEST"
    assert evaluate_dispute_fairness("   ") == "CONTEST"


def test_evaluate_dispute_fairness_heuristics():
    """Verify evaluation returns strictly ACCEPT or CONTEST."""
    res_accept = evaluate_dispute_fairness("The merchant admitted fault and agreed to refund.")
    assert res_accept in ("ACCEPT", "CONTEST")

    res_contest = evaluate_dispute_fairness("I changed my mind about this purchase last week.")
    assert res_contest in ("ACCEPT", "CONTEST")
