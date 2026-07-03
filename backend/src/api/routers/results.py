"""Run results endpoints — post and list per-question results for a run."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Literal
from api.db import supabase
from api.middleware import verify_api_key
from api.models import CreateResultRequest, ResultResponse

router = APIRouter(tags=["results"], dependencies=[Depends(verify_api_key)])


@router.post(
    "/runs/{run_id}/results",
    status_code=status.HTTP_201_CREATED,
)
async def create_result(run_id: str, req: CreateResultRequest):
    """Post a single per-question result for a run.

    Validates that both the run_id and case_id exist before inserting.
    """
    # Verify run exists
    run_result = (
        supabase.table("eval_runs")
        .select("id")
        .eq("id", run_id)
        .execute()
    )
    if not run_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Verify case exists
    case_result = (
        supabase.table("test_cases")
        .select("id")
        .eq("id", req.case_id)
        .execute()
    )
    if not case_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    # Insert result
    data = req.model_dump()
    data["run_id"] = run_id
    result = supabase.table("run_results").insert(data).execute()
    return {"id": result.data[0]["id"]}


@router.get("/runs/{run_id}/results")
async def list_results(
    run_id: str,
    failed_only: bool = Query(default=False),
    sort_by: Literal[
        "relevancy_score", "faithfulness_score", "latency_ms", "created_at"
    ] = Query(default="created_at"),
    order: Literal["asc", "desc"] = Query(default="asc"),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List per-question results for a run with filtering, sorting, and pagination."""
    # Verify run exists
    run_result = (
        supabase.table("eval_runs")
        .select("id")
        .eq("id", run_id)
        .execute()
    )
    if not run_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    # Build query for total count
    count_query = (
        supabase.table("run_results")
        .select("id", count="exact")
        .eq("run_id", run_id)
    )
    if failed_only:
        count_query = count_query.eq("passed", False)
    count_result = count_query.execute()
    total = count_result.count if count_result.count is not None else 0

    # Build query for results
    query = (
        supabase.table("run_results")
        .select("*")
        .eq("run_id", run_id)
    )
    if failed_only:
        query = query.eq("passed", False)

    query = query.order(sort_by, desc=(order == "desc"))
    query = query.range(offset, offset + limit - 1)
    result = query.execute()

    results = []
    for row in result.data:
        r = ResultResponse(
            id=row["id"],
            case_id=row["case_id"],
            question=row["question"],
            expected_answer=row["expected_answer"],
            actual_answer=row.get("actual_answer"),
            faithfulness_score=row.get("faithfulness_score"),
            relevancy_score=row.get("relevancy_score"),
            latency_ms=row["latency_ms"],
            cost_usd=row.get("cost_usd"),
            passed=row["passed"],
            error=row.get("error"),
        )
        results.append(r.model_dump())

    return {"results": results, "total": total}
