"""Post results to the backend API."""

import httpx
from llmeval.models import CaseResult, EvalConfig


class BackendClient:
    """Client for communicating with the LLM Eval backend API."""

    def __init__(self, config: EvalConfig):
        self.api_url = config.project.api_url.rstrip("/")
        self.headers = {
            "X-API-Key": config.project.api_key,
            "Content-Type": "application/json",
        }

    async def create_run(self, payload: dict) -> str:
        """Create a new run. Returns run_id."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/api/v1/runs",
                json=payload,
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()["id"]

    async def post_result(self, run_id: str, result: CaseResult) -> None:
        """Post a single case result to the backend."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/api/v1/runs/{run_id}/results",
                json=result.model_dump(),
                headers=self.headers,
            )
            resp.raise_for_status()

    async def complete_run(self, run_id: str, aggregates: dict) -> dict:
        """Mark a run as completed and post aggregate metrics."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.api_url}/api/v1/runs/{run_id}/complete",
                json=aggregates,
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def fail_run(self, run_id: str, error: str) -> None:
        """Mark a run as failed (when the runner itself crashes)."""
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{self.api_url}/api/v1/runs/{run_id}/fail",
                json={"error": error},
                headers=self.headers,
            )

    async def get_cases(self) -> list[dict]:
        """Fetch all test cases from the backend."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.api_url}/api/v1/cases?limit=500",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()["cases"]
