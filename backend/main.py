"""FastAPI application entrypoint for Razorpay Dispute Defender."""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.webhook import router as webhook_router
from core.database import Base, engine
import data.models  # Ensures Dispute & Telemetry models register on Base.metadata

logger = logging.getLogger("main")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context: creates DB tables on startup."""
    logger.info("Initializing SQLite database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
    yield
    logger.info("Shutting down Razorpay Dispute Defender.")


# Initialize the FastAPI app
app = FastAPI(
    title="Razorpay Dispute Defender",
    description="Chargeback Resolution AI with Courier Telemetry & Automated Dispute Contestation",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the webhook router
app.include_router(webhook_router)
app.include_router(webhook_router, prefix="/api")


@app.get("/", tags=["health"])
def root_check():
    """Root endpoint for status check."""
    return {
        "status": "healthy",
        "service": "Razorpay Dispute Defender",
        "endpoints": ["/webhook/razorpay", "/docs"],
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
