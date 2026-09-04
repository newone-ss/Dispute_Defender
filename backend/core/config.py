"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Central configuration — reads from .env file at startup."""

    # Razorpay credentials
    razorpay_key_id: str = "rzp_test_51ZDefenderMock"
    razorpay_key_secret: str = "secret_test_mockkey998877"
    razorpay_webhook_secret: str = "whsec_mockdisputeshield123"

    # Operating flags
    mock_mode: bool = True
    env: str = "development"

    # Database
    database_url: str = "sqlite:///./data/mock_db/disputes.db"

    # ChromaDB vector store
    chromadb_path: str = "./data/mock_db/chroma_db"

    # GPS geofence thresholds (meters)
    geofence_primary_radius_m: float = 100.0     # Full points
    geofence_secondary_radius_m: float = 500.0   # 80% points
    geofence_tertiary_radius_m: float = 2000.0   # Linear falloff

    # LLM Vision / OCR optional keys
    gemini_api_key: str = ""
    openai_api_key: str = ""

    # Financial penalty constants
    bank_penalty_fee_inr: float = 1500.0  # ₹1,500 penalty per lost/unjustified chargeback contest

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton — avoids re-reading .env on every request."""
    return Settings()
