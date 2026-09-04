"""AI Engine for Razorpay Dispute Defender.

Provides Gemini embeddings for ChromaDB vector operations, a dual LLM setup
(Google Gemini 1.5 Flash + OpenRouter free-tier LLM), and risk/fairness
evaluation for customer chargebacks and disputes.
"""

import logging
import os
import re
from typing import List, Optional

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_openai import ChatOpenAI

# Load environment variables from .env if present
load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# API Key Configuration (relying entirely on os.getenv)
# ---------------------------------------------------------------------------
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.8b-instruct:free")


# ---------------------------------------------------------------------------
# 1. Gemini Embeddings for ChromaDB Vector Ingestion & Querying
# ---------------------------------------------------------------------------
def get_embeddings(api_key: Optional[str] = None) -> GoogleGenerativeAIEmbeddings:
    """Initialize GoogleGenerativeAIEmbeddings with models/embedding-004."""
    key = api_key or os.getenv("GEMINI_API_KEY") or "placeholder_key"
    return GoogleGenerativeAIEmbeddings(
        model="models/embedding-004",
        google_api_key=key,
    )


# Module-level embedding instance for ChromaDB vector ingestion and querying
embeddings: GoogleGenerativeAIEmbeddings = get_embeddings()


class GeminiChromaEmbeddingFunction:
    """ChromaDB-compatible embedding function wrapper for GoogleGenerativeAIEmbeddings.

    Can be passed directly as `embedding_function` to chromadb collections:
    >>> chroma_client.get_or_create_collection(
    ...     name="policy_docs",
    ...     embedding_function=GeminiChromaEmbeddingFunction()
    ... )
    """

    def __init__(self, emb: Optional[GoogleGenerativeAIEmbeddings] = None):
        self._embeddings = emb or get_embeddings()

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Embed list of document texts for ChromaDB."""
        return self._embeddings.embed_documents(input)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed list of texts."""
        return self._embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query text."""
        return self._embeddings.embed_query(query)


# ---------------------------------------------------------------------------
# 2. Dual LLM Setup (Gemini + OpenRouter)
# ---------------------------------------------------------------------------
def get_gemini_llm(api_key: Optional[str] = None) -> ChatGoogleGenerativeAI:
    """Initialize LLM 1: Google Gemini 1.5 Flash model."""
    key = api_key or os.getenv("GEMINI_API_KEY") or "placeholder_key"
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=key,
        temperature=0.1,
    )


def get_openrouter_llm(
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> ChatOpenAI:
    """Initialize LLM 2: OpenRouter free-tier model."""
    key = api_key or os.getenv("OPENROUTER_API_KEY") or "placeholder_key"
    model_name = model or os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.8b-instruct:free")
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
        model=model_name,
        temperature=0.1,
    )


# Module-level LLM instances
llm_gemini: ChatGoogleGenerativeAI = get_gemini_llm()
gemini_llm: ChatGoogleGenerativeAI = llm_gemini

llm_openrouter: ChatOpenAI = get_openrouter_llm()
openrouter_llm: ChatOpenAI = llm_openrouter


# ---------------------------------------------------------------------------
# 3. Risk Evaluation Function
# ---------------------------------------------------------------------------
def _parse_decision_output(raw_output: str) -> Optional[str]:
    """Extract ACCEPT or CONTEST decision token from LLM output."""
    if not raw_output:
        return None
    cleaned = raw_output.strip().upper()

    # Direct match
    if cleaned in ("ACCEPT", "CONTEST"):
        return cleaned

    # Word boundary match
    if re.search(r"\bACCEPT\b", cleaned):
        return "ACCEPT"
    if re.search(r"\bCONTEST\b", cleaned):
        return "CONTEST"

    return None


def evaluate_dispute_fairness(dispute_text: str) -> str:
    """Evaluate customer dispute text and decide whether to ACCEPT or CONTEST.

    Utilizes the dual LLM setup (Gemini with OpenRouter fallback) to analyze
    the customer's dispute claim and return either "ACCEPT" or "CONTEST".

    Args:
        dispute_text: The customer's claim, complaint message, or dispute explanation.

    Returns:
        "ACCEPT" if the claim demonstrates clear merchant liability or justified refund,
        "CONTEST" if the chargeback appears unjustified, fraudulent, or defendable.
    """
    if not dispute_text or not dispute_text.strip():
        logger.info("Empty dispute text received. Defaulting to CONTEST.")
        return "CONTEST"

    prompt_messages = [
        SystemMessage(
            content=(
                "You are an expert chargeback risk assessment engine for Razorpay Dispute Defender. "
                "Evaluate the customer's dispute statement to determine whether the merchant should "
                "ACCEPT the dispute (legitimate claim where merchant failed, e.g., verified defect, "
                "merchant acknowledged cancellation or non-delivery) or CONTEST the dispute "
                "(customer claim is unproven, vague, buyer remorse, suspected friendly fraud, "
                "or contradicts merchant fulfillment records).\n\n"
                "Respond with strictly ONLY one word: 'ACCEPT' or 'CONTEST'."
            )
        ),
        HumanMessage(
            content=f"Customer Dispute Claim:\n\"{dispute_text.strip()}\"\n\nDecision (ACCEPT or CONTEST):"
        ),
    ]

    # Attempt 1: Evaluate using Gemini LLM
    current_gemini_key = os.getenv("GEMINI_API_KEY")
    if current_gemini_key and current_gemini_key != "placeholder_key":
        try:
            llm = get_gemini_llm(api_key=current_gemini_key)
            response = llm.invoke(prompt_messages)
            decision = _parse_decision_output(getattr(response, "content", str(response)))
            if decision:
                logger.info(f"[AI Engine] Gemini evaluated dispute fairness: {decision}")
                return decision
        except Exception as err:
            logger.warning(f"[AI Engine] Gemini evaluation failed: {err}. Falling back to OpenRouter.")

    # Attempt 2: Evaluate using OpenRouter LLM fallback
    current_openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if current_openrouter_key and current_openrouter_key != "placeholder_key":
        try:
            llm = get_openrouter_llm(api_key=current_openrouter_key)
            response = llm.invoke(prompt_messages)
            decision = _parse_decision_output(getattr(response, "content", str(response)))
            if decision:
                logger.info(f"[AI Engine] OpenRouter evaluated dispute fairness: {decision}")
                return decision
        except Exception as err:
            logger.warning(f"[AI Engine] OpenRouter evaluation failed: {err}.")

    # Fallback heuristic: If no valid keys are set or both services are unreachable
    lower_claim = dispute_text.lower()
    accept_indicators = [
        "merchant admitted fault",
        "merchant agreed to refund",
        "double charged",
        "charged twice",
        "duplicate transaction",
        "canceled before shipment confirmed",
    ]
    if any(indicator in lower_claim for indicator in accept_indicators):
        logger.info("[AI Engine] Fallback heuristic matched legitimate dispute indicators -> ACCEPT")
        return "ACCEPT"

    logger.info("[AI Engine] Fallback heuristic defaulted to -> CONTEST")
    return "CONTEST"
