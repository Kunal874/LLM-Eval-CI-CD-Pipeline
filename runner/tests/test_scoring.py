"""Tests for RAGAS scoring logic.

Mocks the RAGAS evaluate function — no real LLM calls are made in tests.
"""

import pytest
from unittest.mock import patch, MagicMock
from llmeval.scoring import score_result
from llmeval.models import PipelineResponse, TestCase


# ── Fixtures ─────────────────────────────────────────────────────────────────

SAMPLE_CASE = TestCase(
    id="case-001",
    question="What is the refund policy?",
    expected_answer="30-day refund window",
    category="general",
)

RESPONSE_WITH_CONTEXT = PipelineResponse(
    answer="Refunds are available within 30 days.",
    context=["Our policy allows 30-day refunds."],
)

RESPONSE_WITHOUT_CONTEXT = PipelineResponse(
    answer="Refunds are available within 30 days.",
    context=None,
)


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("llmeval.scoring.evaluate")
@patch("llmeval.scoring.Dataset")
async def test_score_result_llm_mode(mock_dataset, mock_evaluate):
    """score_result returns (None, float, None) when pipeline_type="llm"."""
    mock_dataset.from_dict.return_value = MagicMock()
    mock_evaluate.return_value = {"answer_relevancy": 0.85}

    faith, relevancy, cost = await score_result(
        SAMPLE_CASE,
        RESPONSE_WITHOUT_CONTEXT,
        pipeline_type="llm",
        judge_model="gpt-4o-mini",
        judge_api_key="sk-test",
    )

    assert faith is None  # No faithfulness for LLM mode
    assert relevancy == pytest.approx(0.85)
    assert cost is None


@pytest.mark.asyncio
@patch("llmeval.scoring.evaluate")
@patch("llmeval.scoring.Dataset")
async def test_score_result_rag_mode(mock_dataset, mock_evaluate):
    """score_result returns (float, float, None) when pipeline_type="rag"
    and context is present."""
    mock_dataset.from_dict.return_value = MagicMock()

    # First call: relevancy, second call: faithfulness
    mock_evaluate.side_effect = [
        {"answer_relevancy": 0.88},
        {"faithfulness": 0.92},
    ]

    faith, relevancy, cost = await score_result(
        SAMPLE_CASE,
        RESPONSE_WITH_CONTEXT,
        pipeline_type="rag",
        judge_model="gpt-4o-mini",
        judge_api_key="sk-test",
    )

    assert faith == pytest.approx(0.92)
    assert relevancy == pytest.approx(0.88)
    assert cost is None


@pytest.mark.asyncio
@patch("llmeval.scoring.evaluate")
@patch("llmeval.scoring.Dataset")
async def test_score_result_exception_non_fatal(mock_dataset, mock_evaluate):
    """score_result returns (None, None, None) when RAGAS raises an exception
    (failure is non-fatal)."""
    mock_dataset.from_dict.return_value = MagicMock()
    mock_evaluate.side_effect = RuntimeError("RAGAS internal error")

    faith, relevancy, cost = await score_result(
        SAMPLE_CASE,
        RESPONSE_WITH_CONTEXT,
        pipeline_type="rag",
        judge_model="gpt-4o-mini",
        judge_api_key="sk-test",
    )

    # Both should be None because the exception was caught
    assert relevancy is None
    assert faith is None
    assert cost is None
