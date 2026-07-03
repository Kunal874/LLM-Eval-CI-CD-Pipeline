"""API key authentication dependency for FastAPI."""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from api.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)):
    """Verify that the provided API key matches the configured key.

    Applied as a dependency on every router except /health.
    """
    if api_key != settings.llmeval_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key
