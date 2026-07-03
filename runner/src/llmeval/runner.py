"""Core eval runner — orchestrate the full evaluation loop."""

import asyncio
import numpy as np
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from llmeval.models import EvalConfig, TestCase, CaseResult
from llmeval.http_mode import call_pipeline
from llmeval.scoring import score_result
from llmeval.poster import BackendClient

console = Console()


async def run_eval(config: EvalConfig, git_info: dict) -> bool:
    """Run the full eval loop.

    Returns True if all thresholds pass, False if any fail.
    """
    client = BackendClient(config)

    # 1. Create run
    run_id = await client.create_run(
        {
            "commit_hash": git_info.get("commit_hash"),
            "branch": git_info.get("branch"),
            "triggered_by": git_info.get("triggered_by", "cli"),
            "pipeline_type": config.pipeline.type,
            "pipeline_endpoint": config.pipeline.endpoint,
            "config_snapshot": config.model_dump(),
        }
    )
    console.print(f"[bold]Run created:[/bold] {run_id}")

    try:
        # 2. Fetch test cases
        raw_cases = await client.get_cases()
        if not raw_cases:
            raise ValueError("No test cases found in dataset. Upload cases first.")

        cases = [TestCase(**c) for c in raw_cases]
        console.print(f"[bold]Running against {len(cases)} test cases...[/bold]")

        # 3. Run each test case
        results: list[CaseResult] = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
        ) as progress:
            task = progress.add_task("Evaluating...", total=len(cases))

            for case in cases:
                progress.update(
                    task, description=f"Testing: {case.question[:50]}..."
                )

                # Call pipeline
                pipeline_resp, latency_ms, error = await call_pipeline(
                    case, run_id, config.pipeline
                )

                # Score result
                faithfulness_score = None
                relevancy_score = None
                cost_usd = None

                if pipeline_resp and not error:
                    faithfulness_score, relevancy_score, cost_usd = (
                        await score_result(
                            case,
                            pipeline_resp,
                            config.pipeline.type,
                            config.judge.model,
                            config.judge.api_key,
                        )
                    )

                # Determine pass/fail for this case
                passed = _case_passes(
                    config,
                    faithfulness_score,
                    relevancy_score,
                    latency_ms,
                    cost_usd,
                    error,
                )

                result = CaseResult(
                    case_id=case.id,
                    question=case.question,
                    expected_answer=case.expected_answer,
                    actual_answer=pipeline_resp.answer if pipeline_resp else None,
                    context=pipeline_resp.context if pipeline_resp else None,
                    faithfulness_score=faithfulness_score,
                    relevancy_score=relevancy_score,
                    latency_ms=latency_ms,
                    cost_usd=cost_usd,
                    passed=passed,
                    error=error,
                )
                results.append(result)

                # Post result immediately (don't batch — avoids losing data
                # if runner crashes)
                await client.post_result(run_id, result)
                progress.advance(task)

        # 4. Compute aggregates
        aggregates = _compute_aggregates(results, config)

        # 5. Complete the run
        await client.complete_run(run_id, aggregates)

        # 6. Print summary
        _print_summary(aggregates, config)

        return aggregates["overall_passed"]

    except Exception as e:
        console.print(f"[red]Runner error: {e}[/red]")
        await client.fail_run(run_id, str(e))
        raise


def _case_passes(
    config, faithfulness, relevancy, latency_ms, cost_usd, error
) -> bool:
    """Determine if a single case passes all thresholds."""
    if error:
        return False
    t = config.thresholds
    if t.relevancy_min and relevancy is not None and relevancy < t.relevancy_min:
        return False
    if (
        t.faithfulness_min
        and faithfulness is not None
        and faithfulness < t.faithfulness_min
    ):
        return False
    if t.p95_latency_ms_max and latency_ms > t.p95_latency_ms_max:
        return False
    if (
        t.cost_per_query_usd_max
        and cost_usd is not None
        and cost_usd > t.cost_per_query_usd_max
    ):
        return False
    return True


def _compute_aggregates(results: list[CaseResult], config: EvalConfig) -> dict:
    """Compute aggregate metrics across all case results."""
    latencies = [r.latency_ms for r in results]
    relevancy_scores = [
        r.relevancy_score for r in results if r.relevancy_score is not None
    ]
    faith_scores = [
        r.faithfulness_score for r in results if r.faithfulness_score is not None
    ]
    costs = [r.cost_usd for r in results if r.cost_usd is not None]

    faithfulness_avg = float(np.mean(faith_scores)) if faith_scores else None
    relevancy_avg = float(np.mean(relevancy_scores)) if relevancy_scores else 0.0
    hallucination_rate = (
        (1 - faithfulness_avg) if faithfulness_avg is not None else None
    )

    passed_cases = sum(1 for r in results if r.passed)
    failed_cases = len(results) - passed_cases

    # Overall pass: check aggregate thresholds
    t = config.thresholds
    overall_passed = True

    if t.hallucination_rate_max and hallucination_rate is not None:
        if hallucination_rate > t.hallucination_rate_max:
            overall_passed = False
    if t.faithfulness_min and faithfulness_avg is not None:
        if faithfulness_avg < t.faithfulness_min:
            overall_passed = False
    if t.relevancy_min and relevancy_avg < t.relevancy_min:
        overall_passed = False

    p50 = int(np.percentile(latencies, 50)) if latencies else 0
    p95 = int(np.percentile(latencies, 95)) if latencies else 0

    if t.p95_latency_ms_max and p95 > t.p95_latency_ms_max:
        overall_passed = False

    avg_cost = float(np.mean(costs)) if costs else None
    total_cost = float(sum(costs)) if costs else None

    if t.cost_per_query_usd_max and avg_cost is not None:
        if avg_cost > t.cost_per_query_usd_max:
            overall_passed = False

    return {
        "faithfulness_avg": faithfulness_avg,
        "relevancy_avg": relevancy_avg,
        "p50_latency_ms": p50,
        "p95_latency_ms": p95,
        "avg_cost_usd": avg_cost,
        "total_cost_usd": total_cost,
        "hallucination_rate": hallucination_rate,
        "total_cases": len(results),
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "overall_passed": overall_passed,
    }


def _print_summary(aggregates: dict, config: EvalConfig) -> None:
    """Print a formatted eval summary to the console."""
    console.print("\n[bold]===== EVAL RESULTS =====[/bold]")
    console.print(f"Total cases:    {aggregates['total_cases']}")
    console.print(f"Passed:         {aggregates['passed_cases']}")
    console.print(f"Failed:         {aggregates['failed_cases']}")
    console.print(f"Relevancy avg:  {aggregates['relevancy_avg']:.1%}")
    if aggregates["faithfulness_avg"] is not None:
        console.print(f"Faithfulness:   {aggregates['faithfulness_avg']:.1%}")
        console.print(f"Hallucination:  {aggregates['hallucination_rate']:.1%}")
    console.print(f"p50 latency:    {aggregates['p50_latency_ms']}ms")
    console.print(f"p95 latency:    {aggregates['p95_latency_ms']}ms")

    if aggregates["overall_passed"]:
        console.print("\n[bold green]✓ ALL THRESHOLDS PASSED[/bold green]")
    else:
        console.print("\n[bold red]✗ THRESHOLDS FAILED — merge blocked[/bold red]")
