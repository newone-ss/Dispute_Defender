"""FastAPI application factory for Razorpay Dispute Defender."""

import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api import dashboard, webhook
from app.config import get_config
from app.core.database import SessionLocal, init_db
from app.core.doc_loader import get_chroma_client, load_policy_documents
from app.logging_config import configure_logging
from app.policy.fairness_gate import load_scoring_policy

config = get_config()
logger = logging.getLogger("dispute_defender")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: configures structured logging, initializes SQLite and ChromaDB."""
    configure_logging(config.log_level)
    policy = load_scoring_policy(config.scoring_policy_path)
    logger.info(
        f"Starting Razorpay Dispute Defender v3.0 (policy_version={policy.get('policy_version')})",
        extra={"event": "startup", "policy_version": policy.get("policy_version")},
    )

    # Initialize SQL tables
    init_db()
    logger.info("Database tables initialized with WAL mode", extra={"event": "db_init"})

    # Warm up ChromaDB collections
    try:
        c = get_chroma_client()
        count = load_policy_documents(c)
        logger.info(
            f"ChromaDB policy collection verified with {count} chunks",
            extra={"event": "chromadb_init", "chunks": count},
        )
    except Exception as ex:
        logger.warning(
            f"ChromaDB startup warmup skipped: {ex}", extra={"event": "chromadb_warning"}
        )

    yield

    logger.info("Shutting down Razorpay Dispute Defender", extra={"event": "shutdown"})


def create_app() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title="Razorpay Dispute Defender",
        description="Deterministic Courier Telemetry Risk Manager & Hybrid RAG Chargeback Defense",
        version="3.0.0",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check for load balancers and container readiness
    @app.get("/healthz", tags=["health"])
    def health_check() -> Dict[str, str]:
        """Health check verifying database and vector store connectivity."""
        db_ok = False
        chroma_ok = False

        db = SessionLocal()
        try:
            db.execute(text("SELECT 1")).scalar()
            db_ok = True
        except Exception:
            pass
        finally:
            db.close()

        try:
            client = get_chroma_client()
            client.heartbeat()
            chroma_ok = True
        except Exception:
            pass

        healthy = db_ok and chroma_ok
        status_code = status.HTTP_200_OK if healthy else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "healthy" if healthy else "degraded",
                "database": "reachable" if db_ok else "unreachable",
                "chromadb": "reachable" if chroma_ok else "unreachable",
                "mock_mode": config.razorpay_mock_mode,
            },
        )

    # Mount API routers
    app.include_router(webhook.router, prefix="/api")
    app.include_router(webhook.router)  # root /webhook alias
    app.include_router(dashboard.router, prefix="/api")
    app.include_router(dashboard.router)  # root alias for /metrics, /disputes
    app.include_router(dashboard.router, prefix="/api/v1/dashboard")  # backward-compat

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
