"""Pydantic v2 request and response models for the LLM Eval API."""

from typing import Literal
from pydantic import BaseModel


# ── REQUEST MODELS ──────────────────────────────────────────────────────────


class CreateRunRequest(BaseModel):
    commit_hash: str | None = None
    branch: str | None = None
    triggered_by: Literal["cli", "github_actions"] = "cli"
    pipeline_type: Literal["llm", "rag"] = "llm"
    pipeline_endpoint: str | None = None
    config_snapshot: dict = {}


class CreateResultRequest(BaseModel):
    case_id: str
    question: str
    expected_answer: str
    actual_answer: str | None = None
    context: list[str] | None = None
    faithfulness_score: float | None = None
    relevancy_score: float | None = None
    latency_ms: int
    cost_usd: float | None = None
    passed: bool
    error: str | None = None


class CompleteRunRequest(BaseModel):
    faithfulness_avg: float | None = None
    relevancy_avg: float
    p50_latency_ms: int
    p95_latency_ms: int
    avg_cost_usd: float | None = None
    total_cost_usd: float | None = None
    hallucination_rate: float | None = None
    total_cases: int
    passed_cases: int
    failed_cases: int
    overall_passed: bool


class FailRunRequest(BaseModel):
    error: str


class CreateCaseRequest(BaseModel):
    question: str
    expected_answer: str
    category: str = "general"


class UpdateCaseRequest(BaseModel):
    question: str | None = None
    expected_answer: str | None = None
    category: str | None = None


# ── RESPONSE MODELS ─────────────────────────────────────────────────────────


class RunResponse(BaseModel):
    id: str
    commit_hash: str | None
    branch: str | None
    triggered_by: str
    pipeline_type: str
    status: str
    created_at: str
    completed_at: str | None


class AggregateResponse(BaseModel):
    faithfulness_avg: float | None
    relevancy_avg: float
    p50_latency_ms: int
    p95_latency_ms: int
    avg_cost_usd: float | None
    total_cost_usd: float | None
    hallucination_rate: float | None
    total_cases: int
    passed_cases: int
    failed_cases: int
    overall_passed: bool


class RunDetailResponse(BaseModel):
    run: RunResponse
    aggregates: AggregateResponse | None


class RunMetricResponse(BaseModel):
    id: str
    commit_hash: str | None
    branch: str | None
    created_at: str
    status: str
    overall_passed: bool
    faithfulness_avg: float | None
    relevancy_avg: float
    p50_latency_ms: int
    p95_latency_ms: int
    avg_cost_usd: float | None
    hallucination_rate: float | None
    total_cases: int
    passed_cases: int
    failed_cases: int


class ResultResponse(BaseModel):
    id: str
    case_id: str
    question: str
    expected_answer: str
    actual_answer: str | None
    faithfulness_score: float | None
    relevancy_score: float | None
    latency_ms: int
    cost_usd: float | None
    passed: bool
    error: str | None


class CaseResponse(BaseModel):
    id: str
    question: str
    expected_answer: str
    category: str
    created_at: str
    updated_at: str


class UploadResponse(BaseModel):
    imported: int
    skipped: int
    errors: list[str]
