// Types for LLM Eval CI/CD Frontend

export interface TestCase {
  id: string
  question: string
  expected_answer: string
  category: string
  created_at: string
  updated_at: string
}

export interface CasesResponse {
  cases: TestCase[]
  total: number
}

export interface UploadResponse {
  imported: number
  skipped: number
  errors: string[]
}

export interface EvalRun {
  id: string
  commit_hash: string | null
  branch: string | null
  triggered_by: 'cli' | 'github_actions'
  pipeline_type: 'llm' | 'rag'
  status: 'running' | 'completed' | 'failed'
  created_at: string
  completed_at: string | null
  // joined from run_aggregates
  overall_passed?: boolean
}

export interface RunAggregate {
  faithfulness_avg: number | null
  relevancy_avg: number
  p50_latency_ms: number
  p95_latency_ms: number
  avg_cost_usd: number | null
  total_cost_usd: number | null
  hallucination_rate: number | null
  total_cases: number
  passed_cases: number
  failed_cases: number
  overall_passed: boolean
}

export interface CaseResult {
  id: string
  case_id: string
  question: string
  expected_answer: string
  actual_answer: string | null
  faithfulness_score: number | null
  relevancy_score: number | null
  latency_ms: number
  cost_usd: number | null
  passed: boolean
  error: string | null
}

export interface RunDetail {
  run: EvalRun
  aggregates: RunAggregate | null
}

export interface RunResultsResponse {
  results: CaseResult[]
  total: number
}

export interface RunsListResponse {
  runs: EvalRun[]
  total: number
}

export interface RunMetric {
  id: string
  commit_hash: string | null
  branch: string | null
  created_at: string
  status: string
  overall_passed: boolean
  faithfulness_avg: number | null
  relevancy_avg: number
  p50_latency_ms: number
  p95_latency_ms: number
  avg_cost_usd: number | null
  hallucination_rate: number | null
  total_cases: number
  passed_cases: number
  failed_cases: number
}

