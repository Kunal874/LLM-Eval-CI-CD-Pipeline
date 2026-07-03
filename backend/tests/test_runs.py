"""Tests for the runs router endpoints."""

import pytest
from unittest.mock import MagicMock, patch


# ── Helpers ──────────────────────────────────────────────────────────────────

SAMPLE_RUN = {
    "id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "commit_hash": "abc123",
    "branch": "main",
    "triggered_by": "cli",
    "pipeline_type": "rag",
    "pipeline_endpoint": None,
    "config_snapshot": {},
    "status": "running",
    "created_at": "2024-01-01T00:00:00+00:00",
    "completed_at": None,
}

SAMPLE_AGGREGATE = {
    "id": "11111111-2222-3333-4444-555555555555",
    "run_id": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee",
    "faithfulness_avg": 0.95,
    "relevancy_avg": 0.88,
    "p50_latency_ms": 200,
    "p95_latency_ms": 500,
    "avg_cost_usd": 0.05,
    "total_cost_usd": 5.0,
    "hallucination_rate": 0.02,
    "total_cases": 100,
    "passed_cases": 95,
    "failed_cases": 5,
    "overall_passed": True,
    "created_at": "2024-01-01T00:01:00+00:00",
}


def make_mock_supabase(table_responses):
    """Create a mock supabase object that returns configured data per table."""
    mock = MagicMock()

    def table_fn(name):
        chain = MagicMock()
        data = table_responses.get(name, [])
        count = len(data) if data else 0

        # Make all chainable methods return the chain itself
        for method in ["select", "insert", "update", "delete", "eq", "order", "range", "limit", "in_"]:
            getattr(chain, method).return_value = chain

        result = MagicMock()
        result.data = data
        result.count = count
        chain.execute.return_value = result
        return chain

    mock.table = table_fn
    return mock


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_run(client, api_key_headers, mock_table):
    """POST /api/v1/runs creates and returns run id."""
    mock_table.configure("eval_runs", data=[SAMPLE_RUN])

    resp = await client.post(
        "/api/v1/runs",
        json={
            "commit_hash": "abc123",
            "branch": "main",
            "pipeline_type": "rag",
        },
        headers=api_key_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["status"] == "running"
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_runs(client, api_key_headers, mock_table):
    """GET /api/v1/runs returns paginated list."""
    mock_table.configure("eval_runs", data=[SAMPLE_RUN], count=1)

    resp = await client.get("/api/v1/runs", headers=api_key_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "runs" in data
    assert "total" in data
    assert isinstance(data["runs"], list)


@pytest.mark.asyncio
async def test_get_run_without_aggregates(client, api_key_headers, mock_table):
    """GET /api/v1/runs/{id} returns run + null aggregates when not complete."""
    mock_table.configure("eval_runs", data=[SAMPLE_RUN])
    mock_table.configure("run_aggregates", data=[])

    resp = await client.get(
        f"/api/v1/runs/{SAMPLE_RUN['id']}",
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["id"] == SAMPLE_RUN["id"]
    assert data["aggregates"] is None


@pytest.mark.asyncio
async def test_complete_run(client, api_key_headers, mock_table):
    """POST /api/v1/runs/{id}/complete returns aggregates."""
    mock_table.configure("eval_runs", data=[SAMPLE_RUN])
    mock_table.configure("run_aggregates", data=[SAMPLE_AGGREGATE])

    resp = await client.post(
        f"/api/v1/runs/{SAMPLE_RUN['id']}/complete",
        json={
            "relevancy_avg": 0.88,
            "p50_latency_ms": 200,
            "p95_latency_ms": 500,
            "total_cases": 100,
            "passed_cases": 95,
            "failed_cases": 5,
            "overall_passed": True,
        },
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["relevancy_avg"] == 0.88
    assert data["total_cases"] == 100
    assert data["overall_passed"] is True


@pytest.mark.asyncio
async def test_get_run_after_complete(client, api_key_headers, mock_table):
    """GET /api/v1/runs/{id} after complete returns run + aggregates."""
    completed_run = {**SAMPLE_RUN, "status": "completed"}
    mock_table.configure("eval_runs", data=[completed_run])
    mock_table.configure("run_aggregates", data=[SAMPLE_AGGREGATE])

    resp = await client.get(
        f"/api/v1/runs/{SAMPLE_RUN['id']}",
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["run"]["status"] == "completed"
    assert data["aggregates"] is not None
    assert data["aggregates"]["relevancy_avg"] == 0.88


@pytest.mark.asyncio
async def test_create_run_no_auth(client):
    """POST /api/v1/runs returns 401 without API key."""
    resp = await client.post(
        "/api/v1/runs",
        json={"pipeline_type": "llm"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_run_metrics(client, api_key_headers, mock_table):
    """GET /api/v1/runs/metrics returns completed runs joined with aggregates."""
    completed_run = {**SAMPLE_RUN, "status": "completed"}
    mock_table.configure("eval_runs", data=[completed_run])
    mock_table.configure("run_aggregates", data=[SAMPLE_AGGREGATE])

    resp = await client.get("/api/v1/runs/metrics", headers=api_key_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "runs" in data
    assert len(data["runs"]) == 1
    assert data["runs"][0]["id"] == SAMPLE_RUN["id"]
    assert data["runs"][0]["relevancy_avg"] == 0.88

