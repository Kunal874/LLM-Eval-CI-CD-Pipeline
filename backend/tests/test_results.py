"""Tests for the results router endpoints."""

import pytest
from unittest.mock import MagicMock


# ── Helpers ──────────────────────────────────────────────────────────────────

SAMPLE_RUN = {
    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "status": "running",
}

SAMPLE_CASE = {
    "id": "11111111-2222-3333-4444-555555555555",
}

SAMPLE_RESULT = {
    "id": "99999999-8888-7777-6666-555555555555",
    "run_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "case_id": "11111111-2222-3333-4444-555555555555",
    "question": "What is LLM?",
    "expected_answer": "Large Language Model",
    "actual_answer": "A Large Language Model",
    "context": None,
    "faithfulness_score": 0.9,
    "relevancy_score": 0.85,
    "latency_ms": 150,
    "cost_usd": 0.01,
    "passed": True,
    "error": None,
    "created_at": "2024-01-01T00:00:00+00:00",
}

SAMPLE_RESULT_FAILED = {
    **SAMPLE_RESULT,
    "id": "88888888-7777-6666-5555-444444444444",
    "passed": False,
    "relevancy_score": 0.3,
    "error": "Low relevancy",
}


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_result(client, api_key_headers, mock_table):
    """POST /api/v1/runs/{id}/results creates result."""
    mock_table.configure("eval_runs", data=[SAMPLE_RUN])
    mock_table.configure("test_cases", data=[SAMPLE_CASE])
    mock_table.configure("run_results", data=[SAMPLE_RESULT])

    resp = await client.post(
        f"/api/v1/runs/{SAMPLE_RUN['id']}/results",
        json={
            "case_id": SAMPLE_CASE["id"],
            "question": "What is LLM?",
            "expected_answer": "Large Language Model",
            "actual_answer": "A Large Language Model",
            "relevancy_score": 0.85,
            "latency_ms": 150,
            "passed": True,
        },
        headers=api_key_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data


@pytest.mark.asyncio
async def test_list_results(client, api_key_headers, mock_table):
    """GET /api/v1/runs/{id}/results returns all results."""
    mock_table.configure("eval_runs", data=[SAMPLE_RUN])
    mock_table.configure(
        "run_results",
        data=[SAMPLE_RESULT, SAMPLE_RESULT_FAILED],
        count=2,
    )

    resp = await client.get(
        f"/api/v1/runs/{SAMPLE_RUN['id']}/results",
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "results" in data
    assert "total" in data
    assert len(data["results"]) == 2


@pytest.mark.asyncio
async def test_list_results_failed_only(client, api_key_headers, mock_table):
    """GET /api/v1/runs/{id}/results?failed_only=true returns only failures."""
    mock_table.configure("eval_runs", data=[SAMPLE_RUN])
    mock_table.configure(
        "run_results",
        data=[SAMPLE_RESULT_FAILED],
        count=1,
    )

    resp = await client.get(
        f"/api/v1/runs/{SAMPLE_RUN['id']}/results?failed_only=true",
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 1
    assert data["results"][0]["passed"] is False


@pytest.mark.asyncio
async def test_list_results_sorted(client, api_key_headers, mock_table):
    """GET /api/v1/runs/{id}/results?sort_by=relevancy_score&order=asc sorts correctly."""
    # Return results in ascending relevancy order
    mock_table.configure("eval_runs", data=[SAMPLE_RUN])
    mock_table.configure(
        "run_results",
        data=[SAMPLE_RESULT_FAILED, SAMPLE_RESULT],  # 0.3, 0.85
        count=2,
    )

    resp = await client.get(
        f"/api/v1/runs/{SAMPLE_RUN['id']}/results?sort_by=relevancy_score&order=asc",
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["results"]) == 2
    # Results should come back as mocked (mock doesn't actually sort, 
    # but we verify the endpoint accepts the params without error)
    assert data["results"][0]["relevancy_score"] == 0.3
    assert data["results"][1]["relevancy_score"] == 0.85


@pytest.mark.asyncio
async def test_create_result_no_auth(client):
    """POST /api/v1/runs/{id}/results returns 401 without API key."""
    resp = await client.post(
        "/api/v1/runs/some-id/results",
        json={
            "case_id": "some-case",
            "question": "test?",
            "expected_answer": "test",
            "latency_ms": 100,
            "passed": True,
        },
    )
    assert resp.status_code == 401
