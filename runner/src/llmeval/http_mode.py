"""HTTP mode — call the user's pipeline endpoint for a single test case."""

import time
import httpx
from llmeval.models import (
    PipelineConfig,
    PipelineRequest,
    PipelineResponse,
    TestCase,
)


async def call_pipeline(
    case: TestCase,
    run_id: str,
    config: PipelineConfig,
) -> tuple[PipelineResponse | None, int, str | None]:
    """Call the user's pipeline endpoint with a test question.

    Returns: (response, latency_ms, error_message)
    response is None if the call failed.
    """
    payload = PipelineRequest(
        question=case.question,
        run_id=run_id,
        case_id=case.id,
    )

    start = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=config.timeout_seconds) as client:
            resp = await client.post(
                config.endpoint,
                json=payload.model_dump(),
                headers=config.headers,
            )
            latency_ms = int((time.monotonic() - start) * 1000)

            if resp.status_code != 200:
                return (
                    None,
                    latency_ms,
                    f"Pipeline returned HTTP {resp.status_code}: {resp.text[:200]}",
                )

            data = resp.json()
            return PipelineResponse(**data), latency_ms, None

    except httpx.TimeoutException:
        latency_ms = int((time.monotonic() - start) * 1000)
        return None, latency_ms, f"Pipeline timed out after {config.timeout_seconds}s"
    except Exception as e:
        latency_ms = int((time.monotonic() - start) * 1000)
        return None, latency_ms, f"Pipeline call failed: {str(e)}"
