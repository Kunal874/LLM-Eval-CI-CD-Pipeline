"""Tests for the cases router endpoints."""

import io
import pytest
import yaml


# ── Helpers ──────────────────────────────────────────────────────────────────

SAMPLE_CASE = {
    "id": "11111111-2222-3333-4444-555555555555",
    "question": "What is Python?",
    "expected_answer": "A programming language",
    "category": "general",
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00",
}


# ── Tests ────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_list_cases(client, api_key_headers, mock_table):
    """GET /api/v1/cases returns 200 and list."""
    mock_table.configure("test_cases", data=[SAMPLE_CASE], count=1)

    resp = await client.get("/api/v1/cases", headers=api_key_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "cases" in data
    assert "total" in data
    assert isinstance(data["cases"], list)
    assert len(data["cases"]) == 1


@pytest.mark.asyncio
async def test_create_case(client, api_key_headers, mock_table):
    """POST /api/v1/cases creates a case and returns it."""
    mock_table.configure("test_cases", data=[SAMPLE_CASE])

    resp = await client.post(
        "/api/v1/cases",
        json={
            "question": "What is Python?",
            "expected_answer": "A programming language",
        },
        headers=api_key_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["question"] == "What is Python?"
    assert data["expected_answer"] == "A programming language"
    assert "id" in data


@pytest.mark.asyncio
async def test_update_case(client, api_key_headers, mock_table):
    """PUT /api/v1/cases/{id} updates and returns updated case."""
    updated_case = {**SAMPLE_CASE, "question": "What is Python 3?"}
    mock_table.configure("test_cases", data=[updated_case])

    resp = await client.put(
        f"/api/v1/cases/{SAMPLE_CASE['id']}",
        json={"question": "What is Python 3?"},
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["question"] == "What is Python 3?"


@pytest.mark.asyncio
async def test_delete_case(client, api_key_headers, mock_table):
    """DELETE /api/v1/cases/{id} returns {"deleted": true}."""
    mock_table.configure("test_cases", data=[SAMPLE_CASE])

    resp = await client.delete(
        f"/api/v1/cases/{SAMPLE_CASE['id']}",
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"deleted": True}


@pytest.mark.asyncio
async def test_upload_csv(client, api_key_headers, mock_table):
    """POST /api/v1/cases/upload with valid CSV returns correct counts."""
    mock_table.configure("test_cases", data=[SAMPLE_CASE])

    csv_content = (
        "question,expected_answer,category\n"
        '"What is AI?","Artificial Intelligence","tech"\n'
        '"What is ML?","Machine Learning","tech"\n'
    )

    resp = await client.post(
        "/api/v1/cases/upload",
        files={"file": ("test.csv", csv_content, "text/csv")},
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_upload_csv_mixed(client, api_key_headers, mock_table):
    """POST /api/v1/cases/upload with mixed valid/invalid rows returns
    correct imported/skipped counts and non-empty errors list."""
    mock_table.configure("test_cases", data=[])

    csv_content = (
        "question,expected_answer,category\n"
        '"What is AI?","Artificial Intelligence","tech"\n'
        ',"","tech"\n'  # missing question and expected_answer
        '"What is ML?","Machine Learning","tech"\n'
    )

    resp = await client.post(
        "/api/v1/cases/upload",
        files={"file": ("test.csv", csv_content, "text/csv")},
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["skipped"] == 1
    assert len(data["errors"]) > 0


@pytest.mark.asyncio
async def test_export_yaml(client, api_key_headers, mock_table):
    """GET /api/v1/cases/export/yaml returns valid YAML."""
    mock_table.configure(
        "test_cases",
        data=[
            {
                "question": "What is Python?",
                "expected_answer": "A programming language",
                "category": "general",
            }
        ],
    )

    resp = await client.get(
        "/api/v1/cases/export/yaml",
        headers=api_key_headers,
    )
    assert resp.status_code == 200
    assert "application/x-yaml" in resp.headers["content-type"]
    assert "dataset.yml" in resp.headers.get("content-disposition", "")

    # Verify it's valid YAML
    data = yaml.safe_load(resp.text)
    assert data["version"] == "1"
    assert len(data["cases"]) == 1
    assert data["cases"][0]["question"] == "What is Python?"


@pytest.mark.asyncio
async def test_list_cases_no_auth(client):
    """GET /api/v1/cases returns 401 without API key."""
    resp = await client.get("/api/v1/cases")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_case_no_auth(client):
    """POST /api/v1/cases returns 401 without API key."""
    resp = await client.post(
        "/api/v1/cases",
        json={"question": "test?", "expected_answer": "test"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_upload_no_auth(client):
    """POST /api/v1/cases/upload returns 401 without API key."""
    resp = await client.post(
        "/api/v1/cases/upload",
        files={"file": ("test.csv", "data", "text/csv")},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_export_no_auth(client):
    """GET /api/v1/cases/export/yaml returns 401 without API key."""
    resp = await client.get("/api/v1/cases/export/yaml")
    assert resp.status_code == 401
