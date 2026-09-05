"""Mock Razorpay Client to bypass KYC and real-merchant API constraints."""

import logging
import uuid

logger = logging.getLogger("mock_razorpay")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


class MockRazorpayClient:
    """Mock Razorpay client allowing development without KYC/live credentials."""

    def upload_evidence_document(self, file_path: str) -> str:
        """Simulate uploading an evidence document to Razorpay.

        Args:
            file_path: Local or relative path to the generated evidence file.

        Returns:
            A mock document identifier string (e.g., 'doc_mock123').
        """
        doc_id = f"doc_mock_{uuid.uuid4().hex[:6]}"
        logger.info(
            f"[MockRazorpay] Document uploaded successfully: "
            f"file_path='{file_path}', document_id='{doc_id}'"
        )
        return doc_id

    def contest_dispute(self, dispute_id: str, document_id: str) -> dict:
        """Simulate contesting a chargeback dispute on Razorpay.

        Args:
            dispute_id: The Razorpay dispute identifier.
            document_id: The identifier of the uploaded evidence document.

        Returns:
            A dictionary with status: 'under_review'.
        """
        logger.info(
            f"[MockRazorpay] Contesting dispute submitted: "
            f"dispute_id='{dispute_id}', document_id='{document_id}'"
        )
        return {"status": "under_review"}


# Default instantiated client for import across services
rzp_client = MockRazorpayClient()
