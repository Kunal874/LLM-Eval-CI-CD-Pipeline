"""Test cases endpoints — CRUD, CSV/JSON upload, and YAML export."""

import csv
import io
import json

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import Response
from api.db import supabase
from api.middleware import verify_api_key
from api.models import (
    CreateCaseRequest,
    UpdateCaseRequest,
    CaseResponse,
    UploadResponse,
)

router = APIRouter(tags=["cases"], dependencies=[Depends(verify_api_key)])


@router.get("/cases")
async def list_cases(
    category: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List test cases with optional category filter and pagination."""
    # Count query
    count_query = supabase.table("test_cases").select("id", count="exact")
    if category:
        count_query = count_query.eq("category", category)
    count_result = count_query.execute()
    total = count_result.count if count_result.count is not None else 0

    # Data query
    query = supabase.table("test_cases").select("*")
    if category:
        query = query.eq("category", category)
    query = query.order("created_at", desc=True)
    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    cases = []
    for row in result.data:
        c = CaseResponse(
            id=row["id"],
            question=row["question"],
            expected_answer=row["expected_answer"],
            category=row["category"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        cases.append(c.model_dump())

    return {"cases": cases, "total": total}


@router.post("/cases", status_code=status.HTTP_201_CREATED)
async def create_case(req: CreateCaseRequest):
    """Create a single test case."""
    data = req.model_dump()
    result = supabase.table("test_cases").insert(data).execute()
    row = result.data[0]
    return CaseResponse(
        id=row["id"],
        question=row["question"],
        expected_answer=row["expected_answer"],
        category=row["category"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    ).model_dump()


@router.put("/cases/{case_id}")
async def update_case(case_id: str, req: UpdateCaseRequest):
    """Update a test case. At least one field must be provided."""
    update_data = req.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No fields provided for update",
        )

    result = (
        supabase.table("test_cases")
        .update(update_data)
        .eq("id", case_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    row = result.data[0]
    return CaseResponse(
        id=row["id"],
        question=row["question"],
        expected_answer=row["expected_answer"],
        category=row["category"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    ).model_dump()


@router.delete("/cases/{case_id}")
async def delete_case(case_id: str):
    """Delete a test case by ID."""
    result = (
        supabase.table("test_cases")
        .delete()
        .eq("id", case_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    return {"deleted": True}


@router.post("/cases/upload")
async def upload_cases(file: UploadFile = File(...)):
    """Upload test cases from a CSV or JSON file.

    CSV format (with header row):
        question,expected_answer,category

    JSON format:
        [{"question": "...", "expected_answer": "...", "category": "general"}, ...]

    Skips rows missing question or expected_answer. Does NOT fail the entire
    upload if some rows are invalid.
    """
    content = await file.read()
    text = content.decode("utf-8")

    imported = 0
    skipped = 0
    errors: list[str] = []

    rows_to_insert: list[dict] = []

    # Determine format from filename or content-type
    filename = file.filename or ""
    is_json = filename.lower().endswith(".json") or (
        file.content_type and "json" in file.content_type
    )

    if is_json:
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid JSON: {e}",
            )

        if not isinstance(data, list):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="JSON must be an array of objects",
            )

        for i, item in enumerate(data, start=1):
            if not isinstance(item, dict):
                skipped += 1
                errors.append(f"Row {i}: not a valid object")
                continue

            question = item.get("question", "").strip() if item.get("question") else ""
            expected = (
                item.get("expected_answer", "").strip()
                if item.get("expected_answer")
                else ""
            )

            if not question or not expected:
                skipped += 1
                errors.append(
                    f"Row {i}: missing question or expected_answer"
                )
                continue

            rows_to_insert.append(
                {
                    "question": question,
                    "expected_answer": expected,
                    "category": item.get("category", "general").strip()
                    or "general",
                }
            )
    else:
        # Parse as CSV
        reader = csv.DictReader(io.StringIO(text))
        for i, row in enumerate(reader, start=2):  # start=2 because row 1 is header
            question = row.get("question", "").strip() if row.get("question") else ""
            expected = (
                row.get("expected_answer", "").strip()
                if row.get("expected_answer")
                else ""
            )

            if not question or not expected:
                skipped += 1
                errors.append(
                    f"Row {i}: missing question or expected_answer"
                )
                continue

            rows_to_insert.append(
                {
                    "question": question,
                    "expected_answer": expected,
                    "category": row.get("category", "general").strip()
                    or "general",
                }
            )

    # Bulk insert valid rows
    if rows_to_insert:
        supabase.table("test_cases").insert(rows_to_insert).execute()
        imported = len(rows_to_insert)

    return UploadResponse(
        imported=imported,
        skipped=skipped,
        errors=errors,
    ).model_dump()


@router.get("/cases/export/yaml")
async def export_cases_yaml():
    """Export all test cases as a downloadable YAML file."""
    result = (
        supabase.table("test_cases")
        .select("question, expected_answer, category")
        .order("created_at", desc=False)
        .execute()
    )

    export_data = {
        "version": "1",
        "cases": [
            {
                "question": row["question"],
                "expected_answer": row["expected_answer"],
                "category": row["category"],
            }
            for row in result.data
        ],
    }

    yaml_content = yaml.dump(
        export_data,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": 'attachment; filename="dataset.yml"'
        },
    )
