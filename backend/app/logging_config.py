"""Structured JSON logging setup for observability and auditing.

Enforces machine-readable JSON log format, injects execution context
(dispute_id, event, latency_ms), and sanitizes any sensitive PII.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict

# Regex patterns for basic PII masking
_CARD_RE = re.compile(r"\b(?:\d{4}[ -]?){3}\d{4}\b")
_PHONE_RE = re.compile(r"\b(?:\+?91[\-\s]?)?[6-9]\d{9}\b")


def mask_pii(text: str) -> str:
    """Mask credit card numbers and mobile numbers in log messages."""
    if not isinstance(text, str):
        return text
    # Mask card numbers, showing only last 4 digits
    text = _CARD_RE.sub(lambda m: f"XXXX-XXXX-XXXX-{m.group(0)[-4:]}", text)
    # Mask phone numbers, showing only last 3 digits
    text = _PHONE_RE.sub(lambda m: f"XXXXXX{m.group(0)[-3:]}", text)
    return text


class StructuredJsonFormatter(logging.Formatter):
    """Formats log records as structured JSON strings with context keys."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": mask_pii(record.getMessage()),
        }

        # Extract structured context if provided via extra
        if hasattr(record, "dispute_id"):
            log_obj["dispute_id"] = getattr(record, "dispute_id")
        if hasattr(record, "event"):
            log_obj["event"] = getattr(record, "event")
        if hasattr(record, "latency_ms"):
            log_obj["latency_ms"] = getattr(record, "latency_ms")
        if hasattr(record, "decision"):
            log_obj["decision"] = getattr(record, "decision")
        if hasattr(record, "policy_version"):
            log_obj["policy_version"] = getattr(record, "policy_version")

        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_obj)


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger with the structured JSON formatter."""
    root_logger = logging.getLogger()
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    root_logger.setLevel(numeric_level)

    # Replace existing handlers
    root_logger.handlers.clear()
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredJsonFormatter())
    root_logger.addHandler(handler)
