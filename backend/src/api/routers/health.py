"""Health check endpoint — no authentication required."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Return service health status. Always returns 200."""
    return {"status": "ok", "version": "0.1.0"}
