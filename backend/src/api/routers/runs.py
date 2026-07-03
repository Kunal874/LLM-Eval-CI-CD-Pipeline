"""Eval runs endpoints — create, list, detail, complete, and fail runs."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from api.db import supabase
from api.middleware import verify_api_key
from api.models import (
    CreateRunRequest,
    CompleteRunRequest,
    FailRunRequest,
    RunResponse,
    RunDetailResponse,
    AggregateResponse,
    RunMetricResponse,
)

router = APIRouter(tags=["runs"], dependencies=[Depends(verify_api_key)])


@router.post("/runs", status_code=status.HTTP_201_CREATED)
async def create_run(req: CreateRunRequest):
    """Create a new eval run. Returns the new run id, status, and created_at."""
    data = req.model_dump()
    result = supabase.table("eval_runs").insert(data).execute()
    row = result.data[0]
    return {
        "id": row["id"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


@router.get("/runs")
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    """List eval runs ordered by created_at DESC with pagination.

    Joins run_aggregates to include overall_passed per run.
    """
    # Get total count
    count_result = (
        supabase.table("eval_runs")
        .select("id", count="exact")
        .execute()
    )
    total = count_result.count if count_result.count is not None else 0

    # Get paginated runs
    result = (
        supabase.table("eval_runs")
        .select("*")
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    runs = []
    for row in result.data:
        run = RunResponse(
            id=row["id"],
            commit_hash=row.get("commit_hash"),
            branch=row.get("branch"),
            triggered_by=row["triggered_by"],
            pipeline_type=row["pipeline_type"],
            status=row["status"],
            created_at=row["created_at"],
            completed_at=row.get("completed_at"),
        )
        runs.append(run.model_dump())

    return {"runs": runs, "total": total}


@router.get("/runs/metrics")
async def get_run_metrics(
    limit: int = Query(default=20, ge=1, le=50),
):
    """Get completed eval runs joined with their aggregate metrics."""
    runs_result = (
        supabase.table("eval_runs")
        .select("*")
        .eq("status", "completed")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    if not runs_result.data:
        return {"runs": []}

    runs_data = runs_result.data
    run_ids = [r["id"] for r in runs_data]

    aggs_result = (
        supabase.table("run_aggregates")
        .select("*")
        .in_("run_id", run_ids)
        .execute()
    )
    aggs_by_run_id = {a["run_id"]: a for a in (aggs_result.data or [])}

    metrics = []
    for r in runs_data:
        agg = aggs_by_run_id.get(r["id"])
        if not agg:
            continue
        metric = RunMetricResponse(
            id=r["id"],
            commit_hash=r.get("commit_hash"),
            branch=r.get("branch"),
            created_at=r["created_at"],
            status=r["status"],
            overall_passed=agg["overall_passed"],
            faithfulness_avg=agg.get("faithfulness_avg"),
            relevancy_avg=agg["relevancy_avg"],
            p50_latency_ms=agg["p50_latency_ms"],
            p95_latency_ms=agg["p95_latency_ms"],
            avg_cost_usd=agg.get("avg_cost_usd"),
            hallucination_rate=agg.get("hallucination_rate"),
            total_cases=agg["total_cases"],
            passed_cases=agg["passed_cases"],
            failed_cases=agg["failed_cases"],
        )
        metrics.append(metric.model_dump())

    return {"runs": metrics}


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get a single run with its aggregates (if completed)."""
    result = (
        supabase.table("eval_runs")
        .select("*")
        .eq("id", run_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    row = result.data[0]
    run = RunResponse(
        id=row["id"],
        commit_hash=row.get("commit_hash"),
        branch=row.get("branch"),
        triggered_by=row["triggered_by"],
        pipeline_type=row["pipeline_type"],
        status=row["status"],
        created_at=row["created_at"],
        completed_at=row.get("completed_at"),
    )

    # Fetch aggregates
    agg_result = (
        supabase.table("run_aggregates")
        .select("*")
        .eq("run_id", run_id)
        .execute()
    )
    aggregates = None
    if agg_result.data:
        a = agg_result.data[0]
        aggregates = AggregateResponse(
            faithfulness_avg=a.get("faithfulness_avg"),
            relevancy_avg=a["relevancy_avg"],
            p50_latency_ms=a["p50_latency_ms"],
            p95_latency_ms=a["p95_latency_ms"],
            avg_cost_usd=a.get("avg_cost_usd"),
            total_cost_usd=a.get("total_cost_usd"),
            hallucination_rate=a.get("hallucination_rate"),
            total_cases=a["total_cases"],
            passed_cases=a["passed_cases"],
            failed_cases=a["failed_cases"],
            overall_passed=a["overall_passed"],
        )

    detail = RunDetailResponse(run=run, aggregates=aggregates)
    return detail.model_dump()


@router.post("/runs/{run_id}/complete")
async def complete_run(run_id: str, req: CompleteRunRequest):
    """Mark a run as completed and store aggregate metrics.

    1. INSERT into run_aggregates
    2. UPDATE eval_runs SET status='completed', completed_at=NOW()
    """
    # Verify run exists
    run_result = (
        supabase.table("eval_runs")
        .select("id, status")
        .eq("id", run_id)
        .execute()
    )
    if not run_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if run_result.data[0]["status"] != "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Run already completed or failed",
        )

    # Insert aggregates
    agg_data = req.model_dump()
    agg_data["run_id"] = run_id
    supabase.table("run_aggregates").insert(agg_data).execute()

    # Update run status
    supabase.table("eval_runs").update(
        {"status": "completed", "completed_at": "now()"}
    ).eq("id", run_id).execute()

    return AggregateResponse(**req.model_dump()).model_dump()


@router.post("/runs/{run_id}/fail")
async def fail_run(run_id: str, req: FailRunRequest):
    """Mark a run as failed. Used when the runner itself crashes mid-run."""
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

    supabase.table("eval_runs").update(
        {"status": "failed", "completed_at": "now()"}
    ).eq("id", run_id).execute()

    return {"id": run_id, "status": "failed"}
