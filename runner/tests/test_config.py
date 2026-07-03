"""Tests for .evalrc.yml config loading."""

import os
import pytest
from pathlib import Path
from llmeval.config import load_config
from llmeval.models import EvalConfig, Thresholds


# ── Fixtures ─────────────────────────────────────────────────────────────────

VALID_CONFIG = """\
version: "1"
project:
  name: "test-project"
  api_url: "http://localhost:8000"
  api_key: "test-api-key"
pipeline:
  type: "rag"
  endpoint: "http://localhost:9000/query"
  timeout_seconds: 30
  headers:
    Authorization: "Bearer test-token"
thresholds:
  hallucination_rate_max: 0.05
  faithfulness_min: 0.90
  relevancy_min: 0.80
  p95_latency_ms_max: 5000
  cost_per_query_usd_max: 0.10
judge:
  model: "gpt-4o-mini"
  api_key: "sk-test-key"
"""

CONFIG_WITH_ENV_VARS = """\
version: "1"
project:
  name: "test-project"
  api_url: "http://localhost:8000"
  api_key: "${TEST_LLMEVAL_API_KEY}"
pipeline:
  type: "llm"
  endpoint: "http://localhost:9000/query"
thresholds:
  relevancy_min: 0.80
judge:
  model: "gpt-4o-mini"
  api_key: "${TEST_OPENAI_API_KEY}"
"""


# ── Tests ────────────────────────────────────────────────────────────────────


def test_load_config_file_not_found():
    """load_config raises FileNotFoundError when file is missing."""
    with pytest.raises(FileNotFoundError):
        load_config(Path("nonexistent.yml"))


def test_load_config_unset_env_var(tmp_path):
    """load_config raises ValueError when an ${ENV_VAR} is unset."""
    config_file = tmp_path / ".evalrc.yml"
    config_file.write_text(CONFIG_WITH_ENV_VARS)

    # Ensure the env vars are NOT set
    os.environ.pop("TEST_LLMEVAL_API_KEY", None)
    os.environ.pop("TEST_OPENAI_API_KEY", None)

    with pytest.raises(ValueError, match="Environment variable"):
        load_config(config_file)


def test_load_config_env_var_substitution(tmp_path):
    """load_config correctly substitutes ${VAR} from environment."""
    config_file = tmp_path / ".evalrc.yml"
    config_file.write_text(CONFIG_WITH_ENV_VARS)

    os.environ["TEST_LLMEVAL_API_KEY"] = "my-secret-key"
    os.environ["TEST_OPENAI_API_KEY"] = "sk-real-key"

    try:
        cfg = load_config(config_file)
        assert cfg.project.api_key == "my-secret-key"
        assert cfg.judge.api_key == "sk-real-key"
    finally:
        os.environ.pop("TEST_LLMEVAL_API_KEY", None)
        os.environ.pop("TEST_OPENAI_API_KEY", None)


def test_load_config_valid(tmp_path):
    """load_config parses a valid .evalrc.yml into EvalConfig correctly."""
    config_file = tmp_path / ".evalrc.yml"
    config_file.write_text(VALID_CONFIG)

    cfg = load_config(config_file)

    assert isinstance(cfg, EvalConfig)
    assert cfg.version == "1"
    assert cfg.project.name == "test-project"
    assert cfg.project.api_url == "http://localhost:8000"
    assert cfg.pipeline.type == "rag"
    assert cfg.pipeline.endpoint == "http://localhost:9000/query"
    assert cfg.pipeline.timeout_seconds == 30
    assert cfg.pipeline.headers == {"Authorization": "Bearer test-token"}
    assert cfg.thresholds.hallucination_rate_max == 0.05
    assert cfg.thresholds.faithfulness_min == 0.90
    assert cfg.thresholds.relevancy_min == 0.80
    assert cfg.thresholds.p95_latency_ms_max == 5000
    assert cfg.judge.model == "gpt-4o-mini"
    assert cfg.judge.api_key == "sk-test-key"


def test_thresholds_accepts_null_values():
    """Thresholds model accepts null values for optional thresholds."""
    t = Thresholds(
        hallucination_rate_max=None,
        faithfulness_min=None,
        relevancy_min=None,
        p95_latency_ms_max=None,
        cost_per_query_usd_max=None,
    )
    assert t.hallucination_rate_max is None
    assert t.faithfulness_min is None
    assert t.relevancy_min is None
    assert t.p95_latency_ms_max is None
    assert t.cost_per_query_usd_max is None
