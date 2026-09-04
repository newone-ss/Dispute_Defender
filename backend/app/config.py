"""Central configuration management loaded via pydantic-settings.

Validates application environment, ensures fail-fast security constraints in production,
and centralizes all filesystem and service connection tunables.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Central configuration singleton for Dispute Defender."""

    # Application environment
    app_env: str = "development"
    log_level: str = "INFO"

    # Transactional database
    database_url: str = "sqlite:///./data/mock_db/disputes.db"

    # Declarative YAML scoring policy
    scoring_policy_path: str = "./app/policy/scoring_policy.yaml"

    # ChromaDB vector storage directory
    chromadb_path: str = "./data/mock_db/chroma_db"

    # Razorpay API credentials
    razorpay_key_id: str = "rzp_test_51ZDefenderMock"
    razorpay_key_secret: str = "secret_test_mockkey998877"
    razorpay_webhook_secret: str = "whsec_mockdisputeshield123"

    # Operational toggles
    razorpay_mock_mode: bool = True
    admin_override_token: str = "admin_secret_token_override_99"

    # Optional Google Gemini key for manifest OCR and chat RAG
    gemini_api_key: Optional[str] = None

    # Worker configuration
    audit_worker_poll_interval_seconds: float = 2.0
    audit_job_lease_seconds: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_production_security(self) -> "Config":
        """Fail fast if critical authentication keys are missing in production."""
        is_prod = self.app_env.lower() in ("production", "prod")
        if is_prod and not self.razorpay_mock_mode:
            if not self.razorpay_webhook_secret or self.razorpay_webhook_secret.startswith(
                "whsec_mock"
            ):
                raise ValueError("Production requires a valid, non-mock RAZORPAY_WEBHOOK_SECRET")
            if not self.razorpay_key_id or self.razorpay_key_id.startswith("rzp_test_"):
                raise ValueError("Production requires a valid, live RAZORPAY_KEY_ID")
            if not self.razorpay_key_secret or "mock" in self.razorpay_key_secret.lower():
                raise ValueError("Production requires a valid, live RAZORPAY_KEY_SECRET")
        return self

    def resolve_path(self, relative_or_absolute_path: str) -> Path:
        """Resolve a filesystem path safely relative to the backend root."""
        p = Path(relative_or_absolute_path)
        if p.is_absolute():
            return p.resolve()
        backend_root = Path(__file__).resolve().parent.parent
        return (backend_root / p).resolve()


@lru_cache(maxsize=1)
def get_config() -> Config:
    """Return cached application configuration singleton."""
    return Config()
