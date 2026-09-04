"""ChromaDB Document Loader — Ingests policy PDFs and omnichannel chat logs.

Manages two ChromaDB collections:
  - "policy_documents": Visa/NPCI rulebook passages for evidence checklist retrieval
  - "customer_chats": WhatsApp/Email/Zendesk transcripts for omnichannel fairness gate
"""

import json
import logging
import os
import re
from typing import List, Dict, Any, Optional

import chromadb

from core.config import get_settings 

logger = logging.getLogger(__name__)
settings = get_settings()

_BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_KNOWLEDGE_BASE_DIR = os.path.join(_BACKEND_ROOT, "data", "knowledge_base")
_CHROMADB_PATH = settings.chromadb_path
if not os.path.isabs(_CHROMADB_PATH):
    _CHROMADB_PATH = os.path.normpath(os.path.join(_BACKEND_ROOT, _CHROMADB_PATH))


def get_chroma_client() -> chromadb.ClientAPI:
    """Return a persistent ChromaDB client at the configured path."""
    os.makedirs(_CHROMADB_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=_CHROMADB_PATH)


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> List[str]:
    """Split text into overlapping chunks of approximately `chunk_size` tokens (words)."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks if chunks else [text.strip()]


def load_policy_documents(client: Optional[chromadb.ClientAPI] = None) -> int:
    """Load Visa/NPCI policy text files from knowledge_base/ into ChromaDB.

    Returns the number of chunks ingested.
    """
    if client is None:
        client = get_chroma_client()

    collection = client.get_or_create_collection(
        name="policy_documents",
        metadata={"description": "Visa CE 3.0 and NPCI UDIR regulatory policy passages"},
    )

    # Skip if already populated
    if collection.count() > 0:
        logger.info(f"Policy documents collection already has {collection.count()} chunks. Skipping re-ingestion.")
        return collection.count()

    total_chunks = 0
    policy_files = [
        ("npci_udir.pdf", "NPCI UDIR Framework"),
        ("visa_ce30.pdf", "Visa CE 3.0 Rules"),
    ]

    for filename, source_label in policy_files:
        filepath = os.path.join(_KNOWLEDGE_BASE_DIR, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Policy file not found: {filepath}")
            continue

        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        chunks = _chunk_text(raw_text, chunk_size=400, overlap=60)
        ids = [f"{filename}__chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": source_label, "filename": filename, "chunk_index": i} for i in range(len(chunks))]

        collection.add(documents=chunks, ids=ids, metadatas=metadatas)
        total_chunks += len(chunks)
        logger.info(f"Ingested {len(chunks)} chunks from {filename} into policy_documents collection")

    return total_chunks


def load_customer_chats(
    client: Optional[chromadb.ClientAPI] = None,
    chat_records: Optional[List[Dict[str, Any]]] = None,
) -> int:
    """Load omnichannel customer chat transcripts into ChromaDB.

    Args:
        client: ChromaDB client instance.
        chat_records: List of dicts with keys: dispute_id, order_id, channel, message, timestamp.

    Returns the number of chat records ingested.
    """
    if client is None:
        client = get_chroma_client()

    collection = client.get_or_create_collection(
        name="customer_chats",
        metadata={"description": "WhatsApp, Email, and Zendesk customer communication transcripts"},
    )

    if chat_records is None:
        chat_records = []

    if not chat_records:
        logger.info("No chat records provided for ingestion.")
        return 0

    # Deduplicate by id
    existing_count = collection.count()

    ids = []
    documents = []
    metadatas = []

    for i, record in enumerate(chat_records):
        chat_id = f"chat_{record.get('dispute_id', 'unknown')}_{record.get('channel', 'unknown')}_{i}"
        message = record.get("message", "")
        if not message.strip():
            continue

        ids.append(chat_id)
        documents.append(message)
        metadatas.append({
            "dispute_id": record.get("dispute_id", ""),
            "order_id": record.get("order_id", ""),
            "channel": record.get("channel", "unknown"),
            "timestamp": record.get("timestamp", ""),
            "customer_name": record.get("customer_name", "Customer"),
        })

    if ids:
        collection.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info(f"Upserted {len(ids)} chat records into customer_chats collection (was {existing_count})")

    return len(ids)


def reset_collections(client: Optional[chromadb.ClientAPI] = None) -> None:
    """Delete and recreate all ChromaDB collections for a clean re-seed."""
    if client is None:
        client = get_chroma_client()

    for name in ["policy_documents", "customer_chats"]:
        try:
            client.delete_collection(name)
            logger.info(f"Deleted ChromaDB collection: {name}")
        except Exception:
            pass

    logger.info("All ChromaDB collections reset.")
