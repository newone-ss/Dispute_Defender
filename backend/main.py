"""Root FastAPI entrypoint for Razorpay Dispute Defender.

Re-exports the application factory and app instance from `app.main` for clean CLI invocations
(e.g., `uvicorn main:app` or `python main.py`).
"""

import uvicorn

from app.main import app, create_app

__all__ = ["app", "create_app"]

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
