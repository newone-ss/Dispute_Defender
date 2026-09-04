"""Reason code registry mapping network standards to defense criteria."""

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReasonCodeEntry:
    """Regulatory criteria and contestability flags for a chargeback reason code."""

    code: str
    description: str
    contestable: bool
    requires_open_box_inspection: bool
    network: str = "NPCI_VISA"


class ReasonCodeRegistry:
    """Registry of standard reason codes for NPCI UDIR and Visa CE 3.0."""

    ENTRIES: Dict[str, ReasonCodeEntry] = {
        "npci.udir.pnr": ReasonCodeEntry(
            code="npci.udir.pnr",
            description="Product Not Received — Cardholder claims non-delivery",
            contestable=True,
            requires_open_box_inspection=False,
            network="NPCI",
        ),
        "visa.rc.13.1": ReasonCodeEntry(
            code="visa.rc.13.1",
            description="Merchandise Not Received — Visa CE 3.0 compelling evidence applies",
            contestable=True,
            requires_open_box_inspection=False,
            network="VISA",
        ),
        "npci.udir.defective": ReasonCodeEntry(
            code="npci.udir.defective",
            description="Defective Merchandise — Broken or damaged goods claim",
            contestable=True,
            requires_open_box_inspection=True,
            network="NPCI",
        ),
        "visa.rc.13.3": ReasonCodeEntry(
            code="visa.rc.13.3",
            description="Not as Described or Defective Merchandise",
            contestable=True,
            requires_open_box_inspection=True,
            network="VISA",
        ),
        "visa.rc.10.4": ReasonCodeEntry(
            code="visa.rc.10.4",
            description="Fraudulent Transaction — Card-Absent Environment",
            contestable=True,
            requires_open_box_inspection=False,
            network="VISA",
        ),
        "unmapped.general": ReasonCodeEntry(
            code="unmapped.general",
            description="Unmapped Reason Code — Requires operator triage",
            contestable=False,
            requires_open_box_inspection=False,
            network="GENERIC",
        ),
    }

    # Normalization table from merchant/Razorpay inputs to canonical registry codes
    _MAPPING: Dict[str, str] = {
        "product_not_received": "npci.udir.pnr",
        "13.1": "visa.rc.13.1",
        "defective_merchandise": "npci.udir.defective",
        "damaged_goods": "npci.udir.defective",
        "13.3": "visa.rc.13.3",
        "fraudulent_transaction": "visa.rc.10.4",
        "10.4": "visa.rc.10.4",
    }

    @classmethod
    def normalize(cls, raw_reason: Optional[str]) -> Tuple[ReasonCodeEntry, bool]:
        """Normalize a raw reason string into a registered ReasonCodeEntry.

        Returns (entry, is_unmapped).
        """
        normalized_key = (raw_reason or "").strip().lower()
        canonical_code = cls._MAPPING.get(normalized_key)

        if canonical_code and canonical_code in cls.ENTRIES:
            return cls.ENTRIES[canonical_code], False

        logger.warning(
            f"Unmapped chargeback reason_code: '{raw_reason}'. Defaulting to 'unmapped.general'",
            extra={"event": "unmapped_reason_code", "raw_reason": raw_reason},
        )
        return cls.ENTRIES["unmapped.general"], True
