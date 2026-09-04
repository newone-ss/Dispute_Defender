"""Unit tests for the new AI Engine (Gemini embeddings, dual LLM, and dispute fairness evaluation)."""

import pytest
from core.ai_engine import (
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


def test_gemini_embeddings_configuration():
    """Verify Gemini embeddings initialization and model pinning."""
    assert embeddings is not None
    assert embeddings.model == "models/embedding-004"

    # Test factory function
    emb = get_embeddings(api_key="test_custom_key")
    assert emb.model == "models/embedding-004"


def test_dual_llm_configuration():
    """Verify Gemini and OpenRouter LLM dual setup."""
    # LLM 1: Gemini 1.5 Flash
    assert gemini_llm is not None
    assert gemini_llm.model == "gemini-1.5-flash"
    assert llm_gemini is gemini_llm

    # LLM 2: OpenRouter
    assert openrouter_llm is not None
    assert openrouter_llm.openai_api_base == "https://openrouter.ai/api/v1"
    assert openrouter_llm.model_name == "meta-llama/llama-3.8b-instruct:free"
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
    assert res_accept == "ACCEPT"

    res_contest = evaluate_dispute_fairness("I changed my mind about this purchase last week.")
    assert res_contest in ("ACCEPT", "CONTEST")
