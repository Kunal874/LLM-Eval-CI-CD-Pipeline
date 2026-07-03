"""Pydantic models for runner config and data structures."""

from pydantic import BaseModel
from typing import Literal


# ── Config Models ────────────────────────────────────────────────────────────


class PipelineConfig(BaseModel):
    type: Literal["llm", "rag"] = "llm"
    endpoint: str
    timeout_seconds: int = 30
    headers: dict[str, str] = {}


class Thresholds(BaseModel):
    hallucination_rate_max: float | None = None
    faithfulness_min: float | None = None
    relevancy_min: float | None = None
    p95_latency_ms_max: int | None = None
    cost_per_query_usd_max: float | None = None


class JudgeConfig(BaseModel):
    model: str = "gpt-4o-mini"
    api_key: str


class ProjectConfig(BaseModel):
    name: str
    api_url: str
    api_key: str


class EvalConfig(BaseModel):
    version: str
    project: ProjectConfig
    pipeline: PipelineConfig
    thresholds: Thresholds
    judge: JudgeConfig


# ── Data Models ──────────────────────────────────────────────────────────────


class TestCase(BaseModel):
    id: str
    question: str
    expected_answer: str
    category: str


class PipelineRequest(BaseModel):
    question: str
    run_id: str
    case_id: str


class PipelineResponse(BaseModel):
    answer: str
    context: list[str] | None = None
    metadata: dict = {}


class CaseResult(BaseModel):
    case_id: str
    question: str
    expected_answer: str
    actual_answer: str | None
    context: list[str] | None
    faithfulness_score: float | None
    relevancy_score: float | None
    latency_ms: int
    cost_usd: float | None
    passed: bool
    error: str | None
