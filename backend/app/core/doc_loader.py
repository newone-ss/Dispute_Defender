"""ChromaDB Document Loader — Ingests regulatory policies and customer chat transcripts.

Embedding Model: Pinned to sentence-transformers/all-MiniLM-L6-v2 via ChromaDB default embedding pipeline.
CLI Usage: `python -m app.core.doc_loader --reindex` to force wipe and re-index.
"""

import argparse
import logging
import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.api import ClientAPI

from app.config import get_config

logger = logging.getLogger(__name__)
config = get_config()


def get_chroma_client() -> ClientAPI:
    """Return persistent ChromaDB client for vector storage."""
    db_path = config.resolve_path(config.chromadb_path)
    os.makedirs(db_path, exist_ok=True)
    return chromadb.PersistentClient(path=str(db_path))


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 60) -> List[str]:
    """Split text into overlapping token/word chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks or [text.strip()]


def load_policy_documents(
    client: Optional[ClientAPI] = None, force_reindex: bool = False
) -> int:
    """Ingest Visa CE 3.0 and NPCI UDIR regulatory texts into ChromaDB."""
    client = client or get_chroma_client()
    if force_reindex:
        try:
            client.delete_collection("policy_documents")
        except Exception:
            pass

    coll = client.get_or_create_collection(
        name="policy_documents",
        metadata={"description": "Visa CE 3.0 & NPCI UDIR regulatory passages"},
    )

    if coll.count() > 0 and not force_reindex:
        return coll.count()

    kb_dir = config.resolve_path("app/data/knowledge_base")
    policy_files = [
        ("npci_udir.pdf", "NPCI UDIR Framework v3.2"),
        ("visa_ce30.pdf", "Visa CE 3.0 Rules 2025"),
    ]

    total = 0
    for filename, source_label in policy_files:
        filepath = kb_dir / filename
        if not filepath.exists():
            continue
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            raw = f.read()

        chunks = chunk_text(raw, chunk_size=350, overlap=50)
        ids = [f"{filename}__c_{i}" for i in range(len(chunks))]
        metas = [
            {"source": source_label, "filename": filename, "policy_version": "2026.1.0"}
            for _ in chunks
        ]
        coll.add(documents=chunks, ids=ids, metadatas=metas)
        total += len(chunks)

    return total


def load_customer_chats(
    client: Optional[ClientAPI] = None,
    chat_records: Optional[List[Dict[str, Any]]] = None,
    force_reindex: bool = False,
) -> int:
    """Index omnichannel customer communication transcripts."""
    client = client or get_chroma_client()
    if force_reindex:
        try:
            client.delete_collection("customer_chats")
        except Exception:
            pass

    coll = client.get_or_create_collection(name="customer_chats")
    if not chat_records:
        return coll.count()

    ids, docs, metas = [], [], []
    for i, r in enumerate(chat_records):
        msg = r.get("message", "").strip()
        if not msg:
            continue
        cid = f"chat_{r.get('dispute_id', 'gen')}_{i}"
        ids.append(cid)
        docs.append(msg)
        metas.append(
            {
                "dispute_id": r.get("dispute_id", ""),
                "channel": r.get("channel", "whatsapp"),
                "timestamp": r.get("timestamp", ""),
                "order_id": r.get("order_id", ""),
            }
        )

    if ids:
        coll.upsert(documents=docs, ids=ids, metadatas=metas)
    return len(ids)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ChromaDB policy & chat transcript ingestor")
    parser.add_argument(
        "--reindex", action="store_true", help="Force wipe and re-index collections"
    )
    args = parser.parse_args()

    c = get_chroma_client()
    n = load_policy_documents(c, force_reindex=args.reindex)
    print(f"[OK] ChromaDB policy_documents loaded with {n} chunks (reindex={args.reindex})")
