"""Tests for HTTP mode pipeline interaction.

Uses respx to mock HTTP calls — no real HTTP calls are made in tests.
"""

import pytest
import respx
import httpx
from llmeval.http_mode import call_pipeline
from llmeval.models import PipelineConfig, PipelineResponse, TestCase


# ── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_CASE = TestCase(
    id="case-001",
    question="What is the refund policy?",
    expected_answer="30-day refund window",
    category="general",
)

PIPELINE_CONFIG = PipelineConfig(
    type="rag",
    endpoint="http://mock-pipeline:9000/query",
    timeout_seconds=5,
    headers={"Authorization": "Bearer test-token"},
)

RUN_ID = "run-abc-123"


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@respx.mock
async def test_call_pipeline_success():
    """call_pipeline returns (PipelineResponse, latency_ms, None) on HTTP 200."""
    respx.post("http://mock-pipeline:9000/query").mock(
        return_value=httpx.Response(
            200,
            json={
                "answer": "Refunds are available within 30 days.",
                "context": ["Our policy allows 30-day refunds."],
                "metadata": {"source": "faq"},
            },
        )
    )

    response, latency_ms, error = await call_pipeline(
        SAMPLE_CASE, RUN_ID, PIPELINE_CONFIG
    )

    assert error is None
    assert isinstance(response, PipelineResponse)
    assert response.answer == "Refunds are available within 30 days."
    assert response.context == ["Our policy allows 30-day refunds."]
    assert response.metadata == {"source": "faq"}
    assert latency_ms >= 0


@pytest.mark.asyncio
@respx.mock
async def test_call_pipeline_http_error():
    """call_pipeline returns (None, latency_ms, error_str) on HTTP 500."""
    respx.post("http://mock-pipeline:9000/query").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    response, latency_ms, error = await call_pipeline(
        SAMPLE_CASE, RUN_ID, PIPELINE_CONFIG
    )

    assert response is None
    assert latency_ms >= 0
    assert error is not None
    assert "500" in error


@pytest.mark.asyncio
@respx.mock
async def test_call_pipeline_timeout():
    """call_pipeline returns (None, latency_ms, error_str) on timeout."""
    respx.post("http://mock-pipeline:9000/query").mock(
        side_effect=httpx.ReadTimeout("Connection timed out")
    )

    response, latency_ms, error = await call_pipeline(
        SAMPLE_CASE, RUN_ID, PIPELINE_CONFIG
    )

    assert response is None
    assert latency_ms >= 0
    assert error is not None
    assert "timed out" in error.lower()


@pytest.mark.asyncio
@respx.mock
async def test_call_pipeline_sends_correct_payload():
    """Correct request payload is sent: {question, run_id, case_id}."""
    route = respx.post("http://mock-pipeline:9000/query").mock(
        return_value=httpx.Response(
            200,
            json={"answer": "test", "context": []},
        )
    )

    await call_pipeline(SAMPLE_CASE, RUN_ID, PIPELINE_CONFIG)

    assert route.called
    request = route.calls[0].request
    import json

    body = json.loads(request.content)
    assert body["question"] == "What is the refund policy?"
    assert body["run_id"] == "run-abc-123"
    assert body["case_id"] == "case-001"


@pytest.mark.asyncio
@respx.mock
async def test_call_pipeline_sends_custom_headers():
    """Custom headers from config are included in the request."""
    route = respx.post("http://mock-pipeline:9000/query").mock(
        return_value=httpx.Response(
            200,
            json={"answer": "test", "context": []},
        )
    )

    await call_pipeline(SAMPLE_CASE, RUN_ID, PIPELINE_CONFIG)

    assert route.called
    request = route.calls[0].request
    assert request.headers["authorization"] == "Bearer test-token"
