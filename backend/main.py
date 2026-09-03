"""FastAPI application entrypoint for Razorpay Dispute Defender.

Mounts routers for webhooks and the React frontend dashboard,
configures CORS, and initializes the SQLite database on startup.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import init_db
from api import webhook, dashboard

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("dispute_defender")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: initializes DB tables upon startup."""
    logger.info("🛡️  Starting Razorpay Dispute Defender — Initializing SQLite database...")
    init_db()
    logger.info("✅ SQLite database and tables verified ready.")
    yield
    logger.info("🛑 Razorpay Dispute Defender shutdown complete.")


app = FastAPI(
    title="Razorpay Dispute Defender",
    description="Track 2: AI Risk Manager — Deterministic Telemetry & Chargeback Defense System",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS configuration for React frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(webhook.router)
app.include_router(dashboard.router)


@app.get("/health")
def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "razorpay-dispute-defender",
        "version": "2.0.0",
        "mock_mode": True,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
