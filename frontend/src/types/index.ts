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
  status: "running" | "completed" | "failed"
  model_id: string
  pipeline_url: string
  total_cases: number
  passed_cases: number
  failed_cases: number
  created_at: string
  completed_at: string | null
  config_snapshot: Record<string, unknown>
}

export interface CaseResult {
  id: string
  run_id: string
  case_id: string
  question: string
  expected_answer: string
  actual_answer: string
  latency_ms: number
  faithfulness: number | null
  answer_relevancy: number | null
  passed: boolean
  failure_reasons: string[]
  created_at: string
}

export interface RunResultsResponse {
  results: CaseResult[]
  total: number
}

export interface RunAggregates {
  total_cases: number
  passed_cases: number
  failed_cases: number
  pass_rate: number
  avg_latency_ms: number
  p95_latency_ms: number
  avg_faithfulness: number | null
  avg_answer_relevancy: number | null
}
