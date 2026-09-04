"""Razorpay Documents and Disputes API client with mock mode safety toggle."""

import logging
from typing import Optional

import httpx

from app.config import get_config
from app.core.schemas import AcceptAck, ContestAck, DocumentRef

logger = logging.getLogger(__name__)
config = get_config()


class RazorpayClientError(Exception):
    """Base exception for Razorpay HTTP client failures."""


class RazorpayAuthError(RazorpayClientError):
    """Authentication or signature failure with Razorpay API."""


class RazorpayAPIError(RazorpayClientError):
    """Non-2xx response from Razorpay endpoints."""


class RazorpayClient:
    """Client for Razorpay Documents and Disputes APIs."""

    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(self):
        self.auth = (config.razorpay_key_id, config.razorpay_key_secret)
        self.mock_mode = (
            config.razorpay_mock_mode
            or config.app_env == "development"
            or config.razorpay_key_id.startswith("rzp_test_")
        )

    def upload_evidence(self, packet: str, filename: str = "npci_udir_evidence.md") -> DocumentRef:
        """Upload compiled representment evidence markdown to Razorpay Documents API."""
        if self.mock_mode:
            mock_id = f"doc_mock_{abs(hash(packet)) % 900000 + 100000}"
            logger.info(
                f"[MOCK] Uploaded evidence document {filename} -> {mock_id}",
                extra={"event": "razorpay_mock_upload", "doc_id": mock_id, "mock": True},
            )
            return DocumentRef(id=mock_id, name=filename, mock=True)

        url = f"{self.BASE_URL}/documents"
        files = {"file": (filename, packet.encode("utf-8"), "text/markdown")}
        data = {"purpose": "dispute_evidence"}

        try:
            with httpx.Client(timeout=25.0) as client:
                res = client.post(url, data=data, files=files, auth=self.auth)
                if res.status_code in (401, 403):
                    raise RazorpayAuthError("Razorpay credentials rejected")
                res.raise_for_status()
                parsed = res.json()
                return DocumentRef(id=parsed.get("id"), name=filename, mock=False)
        except httpx.HTTPStatusError as err:
            raise RazorpayAPIError(
                f"Document upload failed with status {err.response.status_code}"
            ) from err
        except Exception as err:
            raise RazorpayClientError(f"Network error during document upload: {err}") from err

    def contest(
        self, dispute_id: str, document_id: Optional[str] = None, summary: Optional[str] = None
    ) -> ContestAck:
        """Submit evidence to contest a dispute via Razorpay Disputes API."""
        if self.mock_mode:
            logger.info(
                f"[MOCK] Contested dispute {dispute_id} with document {document_id}",
                extra={"dispute_id": dispute_id, "event": "razorpay_mock_contest", "mock": True},
            )
            return ContestAck(
                dispute_id=dispute_id,
                status="under_review",
                document_ids=[document_id] if document_id else [],
                mock=True,
            )

        url = f"{self.BASE_URL}/disputes/{dispute_id}/contest"
        payload = {
            "action": "submit",
            "summary": summary
            or "NPCI UDIR Representment with physical OTP & GPS courier telemetry.",
        }
        if document_id:
            payload["documents"] = [document_id]

        try:
            with httpx.Client(timeout=25.0) as client:
                res = client.patch(url, json=payload, auth=self.auth)
                if res.status_code in (401, 403):
                    raise RazorpayAuthError("Razorpay credentials rejected")
                res.raise_for_status()
                return ContestAck(
                    dispute_id=dispute_id,
                    status="under_review",
                    document_ids=[document_id] if document_id else [],
                    mock=False,
                )
        except httpx.HTTPStatusError as err:
            raise RazorpayAPIError(
                f"Contest API failed with status {err.response.status_code}"
            ) from err
        except Exception as err:
            raise RazorpayClientError(f"Network error during dispute contest: {err}") from err

    def accept(self, dispute_id: str) -> AcceptAck:
        """Accept a dispute to release liability and avoid the ₹1,500 bank penalty."""
        if self.mock_mode:
            logger.info(
                f"[MOCK] Accepted dispute {dispute_id} (released liability)",
                extra={"dispute_id": dispute_id, "event": "razorpay_mock_accept", "mock": True},
            )
            return AcceptAck(dispute_id=dispute_id, status="accepted", mock=True)

        url = f"{self.BASE_URL}/disputes/{dispute_id}/accept"
        try:
            with httpx.Client(timeout=25.0) as client:
                res = client.post(url, auth=self.auth)
                if res.status_code in (401, 403):
                    raise RazorpayAuthError("Razorpay credentials rejected")
                res.raise_for_status()
                return AcceptAck(dispute_id=dispute_id, status="accepted", mock=False)
        except httpx.HTTPStatusError as err:
            raise RazorpayAPIError(
                f"Accept API failed with status {err.response.status_code}"
            ) from err
        except Exception as err:
            raise RazorpayClientError(f"Network error during dispute accept: {err}") from err


razorpay_client = RazorpayClient()
