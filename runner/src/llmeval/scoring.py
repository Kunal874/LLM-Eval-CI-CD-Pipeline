"""RAGAS-based scoring — faithfulness and answer relevancy."""

from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy
from datasets import Dataset
from llmeval.models import PipelineResponse, TestCase


async def score_result(
    case: TestCase,
    response: PipelineResponse,
    pipeline_type: str,
    judge_model: str,
    judge_api_key: str,
) -> tuple[float | None, float | None, float | None]:
    """Score a pipeline response using RAGAS metrics.

    Returns: (faithfulness_score, relevancy_score, cost_usd)
    faithfulness_score is None if pipeline_type == "llm" or context is empty.
    cost_usd is an estimate based on token usage if available, else None.

    RAGAS expects a Dataset with columns:
      - question: str
      - answer: str
      - contexts: list[str]  (required for faithfulness)
      - ground_truth: str
    """
    import os

    os.environ["OPENAI_API_KEY"] = judge_api_key

    # Always compute relevancy (works without context)
    relevancy_data = Dataset.from_dict(
        {
            "question": [case.question],
            "answer": [response.answer],
            "contexts": [response.context or [""]],
            "ground_truth": [case.expected_answer],
        }
    )

    try:
        relevancy_result = evaluate(
            relevancy_data,
            metrics=[answer_relevancy],
        )
        relevancy_score = float(relevancy_result["answer_relevancy"])
    except Exception:
        # Scoring failed — log but don't crash the run
        relevancy_score = None

    # Compute faithfulness only for RAG pipelines with context
    faithfulness_score = None
    if pipeline_type == "rag" and response.context:
        faith_data = Dataset.from_dict(
            {
                "question": [case.question],
                "answer": [response.answer],
                "contexts": [response.context],
                "ground_truth": [case.expected_answer],
            }
        )
        try:
            faith_result = evaluate(faith_data, metrics=[faithfulness])
            faithfulness_score = float(faith_result["faithfulness"])
        except Exception:
            faithfulness_score = None

    # Cost estimation: RAGAS uses GPT calls internally.
    # We cannot reliably extract token usage from RAGAS 0.1.x.
    # Return None for now; will be addressed in a future phase.
    cost_usd = None

    return faithfulness_score, relevancy_score, cost_usd
