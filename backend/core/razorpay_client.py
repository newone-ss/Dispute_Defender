"""Razorpay API client with Document upload, Contest, and Accept endpoints.

Includes MOCK_MODE toggle for safe, zero-cost development and simulation testing.
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class RazorpayClient:
    """HTTP client wrapping Razorpay's Documents and Disputes API."""

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self):
        self.auth = (settings.razorpay_key_id, settings.razorpay_key_secret)
        self.mock_mode = (
            settings.mock_mode
            or settings.env == "development"
            or settings.razorpay_key_id.startswith("rzp_test_")
        )

    async def upload_document(
        self,
        document_text: str,
        filename: str = "npci_udir_evidence.md",
        purpose: str = "dispute_evidence",
    ) -> Dict[str, Any]:
        """Upload compiled representment evidence to Razorpay Documents API.

        POST /v1/documents
        """
        if self.mock_mode:
            mock_doc_id = f"doc_mock_{abs(hash(document_text)) % 900000 + 100000}"
            logger.info(f"[MOCK_MODE] Uploaded document {filename} -> {mock_doc_id}")
            return {
                "id": mock_doc_id,
                "entity": "document",
                "purpose": purpose,
                "name": filename,
                "size": len(document_text.encode("utf-8")),
                "mime_type": "text/markdown",
                "mock_mode": True,
            }

        url = f"{self.BASE_URL}/documents"
        files = {
            "file": (filename, document_text.encode("utf-8"), "text/markdown"),
        }
        data = {"purpose": purpose}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, data=data, files=files, auth=self.auth)
            response.raise_for_status()
            return response.json()

    def upload_document_sync(
        self,
        document_text: str,
        filename: str = "npci_udir_evidence.md",
        purpose: str = "dispute_evidence",
    ) -> Dict[str, Any]:
        """Synchronous version of document upload for background tasks."""
        if self.mock_mode:
            mock_doc_id = f"doc_mock_{abs(hash(document_text)) % 900000 + 100000}"
            logger.info(f"[MOCK_MODE] Uploaded document {filename} -> {mock_doc_id}")
            return {
                "id": mock_doc_id,
                "entity": "document",
                "purpose": purpose,
                "name": filename,
                "mock_mode": True,
            }

        url = f"{self.BASE_URL}/documents"
        files = {
            "file": (filename, document_text.encode("utf-8"), "text/markdown"),
        }
        data = {"purpose": purpose}

        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, data=data, files=files, auth=self.auth)
            response.raise_for_status()
            return response.json()

    async def contest_dispute(
        self,
        dispute_id: str,
        evidence_text: str,
        document_ids: Optional[List[str]] = None,
        summary: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit evidence to contest a dispute via Razorpay Disputes API.

        PATCH /v1/disputes/{id}/contest
        Payload includes action: "submit", evidence, and document references.
        """
        if self.mock_mode:
            logger.info(f"[MOCK_MODE] Successfully submitted contest for dispute {dispute_id}")
            return {
                "id": dispute_id,
                "entity": "dispute",
                "status": "under_review",
                "action": "submit",
                "document_ids": document_ids or [],
                "mock_mode": True,
            }

        url = f"{self.BASE_URL}/disputes/{dispute_id}/contest"
        payload = {
            "action": "submit",
            "summary": summary or "NPCI UDIR Representment with verified OTP and GPS courier telemetry.",
            "shipping_proof": evidence_text,
            "billing_proof": evidence_text,
        }
        if document_ids:
            payload["documents"] = document_ids

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(url, json=payload, auth=self.auth)
            response.raise_for_status()
            return response.json()

    def contest_dispute_sync(
        self,
        dispute_id: str,
        evidence_text: str,
        document_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Synchronous version of contest API for background tasks."""
        if self.mock_mode:
            logger.info(f"[MOCK_MODE] Synced contest submit for {dispute_id}")
            return {
                "id": dispute_id,
                "status": "under_review",
                "action": "submit",
                "mock_mode": True,
            }

        url = f"{self.BASE_URL}/disputes/{dispute_id}/contest"
        payload = {
            "action": "submit",
            "summary": "NPCI UDIR Representment with verified OTP and GPS courier telemetry.",
            "shipping_proof": evidence_text,
            "billing_proof": evidence_text,
        }
        if document_ids:
            payload["documents"] = document_ids

        with httpx.Client(timeout=30.0) as client:
            response = client.patch(url, json=payload, auth=self.auth)
            response.raise_for_status()
            return response.json()

    async def accept_dispute(self, dispute_id: str) -> Dict[str, Any]:
        """Accept a dispute to release liability and avoid the ₹1,500 bank penalty.

        POST /v1/disputes/{id}/accept
        """
        if self.mock_mode:
            logger.info(f"[MOCK_MODE] Successfully accepted dispute {dispute_id} (released liability)")
            return {
                "id": dispute_id,
                "entity": "dispute",
                "status": "accepted",
                "mock_mode": True,
            }

        url = f"{self.BASE_URL}/disputes/{dispute_id}/accept"
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, auth=self.auth)
            response.raise_for_status()
            return response.json()

    def accept_dispute_sync(self, dispute_id: str) -> Dict[str, Any]:
        """Synchronous version of accept API for background tasks."""
        if self.mock_mode:
            logger.info(f"[MOCK_MODE] Synced accept for {dispute_id}")
            return {"id": dispute_id, "status": "accepted", "mock_mode": True}

        url = f"{self.BASE_URL}/disputes/{dispute_id}/accept"
        with httpx.Client(timeout=30.0) as client:
            response = client.post(url, auth=self.auth)
            response.raise_for_status()
            return response.json()


# Singleton client
razorpay_client = RazorpayClient()
