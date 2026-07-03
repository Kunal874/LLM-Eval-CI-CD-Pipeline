-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Test cases (the golden dataset)
CREATE TABLE test_cases (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    question      TEXT NOT NULL,
    expected_answer TEXT NOT NULL,
    category      TEXT NOT NULL DEFAULT 'general',
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_test_cases_category ON test_cases(category);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ language 'plpgsql';

CREATE TRIGGER update_test_cases_updated_at
    BEFORE UPDATE ON test_cases
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Eval runs (one per CI trigger or manual run)
CREATE TABLE eval_runs (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_hash       VARCHAR(40),
    branch            VARCHAR(255),
    triggered_by      VARCHAR(50) NOT NULL DEFAULT 'cli',
    pipeline_type     VARCHAR(10) NOT NULL DEFAULT 'llm',
    pipeline_endpoint TEXT,
    config_snapshot   JSONB NOT NULL DEFAULT '{}',
    status            VARCHAR(20) NOT NULL DEFAULT 'running',
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at      TIMESTAMPTZ,
    CONSTRAINT status_values CHECK (status IN ('running','completed','failed')),
    CONSTRAINT pipeline_type_values CHECK (pipeline_type IN ('llm','rag')),
    CONSTRAINT triggered_by_values CHECK (triggered_by IN ('cli','github_actions'))
);

CREATE INDEX idx_eval_runs_created_at ON eval_runs(created_at DESC);
CREATE INDEX idx_eval_runs_status ON eval_runs(status);

-- Per-question results (one row per test case per run)
CREATE TABLE run_results (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              UUID NOT NULL REFERENCES eval_runs(id) ON DELETE CASCADE,
    case_id             UUID NOT NULL REFERENCES test_cases(id) ON DELETE CASCADE,
    question            TEXT NOT NULL,
    expected_answer     TEXT NOT NULL,
    actual_answer       TEXT,
    context             JSONB,
    faithfulness_score  FLOAT,
    relevancy_score     FLOAT,
    latency_ms          INTEGER NOT NULL,
    cost_usd            FLOAT,
    passed              BOOLEAN NOT NULL DEFAULT false,
    error               TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_run_results_run_id ON run_results(run_id);
CREATE INDEX idx_run_results_passed ON run_results(run_id, passed);

-- Aggregated metrics per run (one row per run, written on completion)
CREATE TABLE run_aggregates (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id              UUID NOT NULL UNIQUE REFERENCES eval_runs(id) ON DELETE CASCADE,
    faithfulness_avg    FLOAT,
    relevancy_avg       FLOAT NOT NULL,
    p50_latency_ms      INTEGER NOT NULL,
    p95_latency_ms      INTEGER NOT NULL,
    avg_cost_usd        FLOAT,
    total_cost_usd      FLOAT,
    hallucination_rate  FLOAT,
    total_cases         INTEGER NOT NULL,
    passed_cases        INTEGER NOT NULL,
    failed_cases        INTEGER NOT NULL,
    overall_passed      BOOLEAN NOT NULL DEFAULT false,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
