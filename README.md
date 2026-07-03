# llmeval

[![CI](https://github.com/your-username/llm-eval/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/llm-eval/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> Automated LLM evaluation that runs on every git push.

![Dashboard screenshot coming soon](docs/assets/dashboard-placeholder.png)

---

## What is this?

Deploying changes to LLM prompts, RAG retrieval pipelines, or generation models often feels like flying blind. A prompt change that improves one edge case might secretly degrade overall answer accuracy, introduce hallucinations across other topics, or double your p95 latency. Without automated regression testing, engineering teams rely on slow manual QA or discover quality regressions only after users report broken responses.

**llmeval** is an open-source continuous evaluation framework designed specifically for LLM and RAG pipelines. By integrating directly into your CI/CD pipeline (such as GitHub Actions), `llmeval` automatically executes your evaluation suite against every pull request. It compares outputs against benchmark test cases, computes quality scores using LLM-as-a-Judge (via RAGAS), measures latency and cost, and automatically blocks merges if metrics breach defined thresholds.

---

## Quick Start

### 1. Clone and configure

```bash
git clone https://github.com/your-username/llm-eval
cd llm-eval
cp .env.example .env
# Edit .env with your Supabase credentials and API key
```

### 2. Provision Supabase

1. Create a free project at [supabase.com](https://supabase.com)
2. Go to the SQL Editor and run the contents of `supabase/migrations/001_initial_schema.sql`
3. Copy your project URL and service role key into `.env`

*(Alternatively, to run entirely locally without Supabase, see `docker-compose.local.yml` in the Self-Hosting Guide).*

### 3. Start the stack

```bash
docker-compose up --build
```

- **Dashboard**: http://localhost:3000  
- **API**: http://localhost:8000

### 4. Upload your test dataset

Go to http://localhost:3000/dataset and upload a CSV:
```csv
question,expected_answer,category
"What is your refund policy?","You can return items within 30 days.","refunds"
"How do I contact support?","Email support@example.com","support"
```

### 5. Configure your pipeline

Copy `.evalrc.example.yml` to `.evalrc.yml` in your application repository:
```bash
cp .evalrc.example.yml .evalrc.yml
```

Edit `.evalrc.yml` to point at your application's pipeline endpoint and your deployed `llmeval` backend URL.

### 6. Run your first eval

```bash
pip install llmeval
llmeval run
```

### 7. Add to GitHub Actions

Copy `.github/workflows/llm-eval.yml` to your project repository `.github/workflows/llm-eval.yml`.
Add these GitHub Actions secrets in your repository settings:
- `LLMEVAL_API_KEY` — the API key from your `.env`
- `LLMEVAL_API_URL` — the URL of your deployed backend
- `OPENAI_API_KEY` — used by RAGAS for scoring outputs

---

## Pipeline Response Contract

Your application's pipeline endpoint configured in `.evalrc.yml` must accept HTTP `POST` requests and return JSON.

**Request** (sent by `llmeval` runner):
```json
{
  "question": "What is your refund policy?",
  "run_id": "8fa85f64-5717-4562-b3fc-2c963f66afa6",
  "case_id": "3d4638cb-464a-44aa-ba60-b633092288ca"
}
```

**Response — RAG pipeline** (`pipeline.type: "rag"`):
```json
{
  "answer": "You can return items within 30 days of purchase.",
  "context": [
    "Our return policy allows refunds within 30 days.",
    "Items must be in original condition."
  ]
}
```

**Response — Plain LLM** (`pipeline.type: "llm"`):
```json
{
  "answer": "You can return items within 30 days of purchase."
}
```

> [!IMPORTANT]
> The `context` field (array of strings representing retrieved context chunks) is **required** for RAG pipelines to compute faithfulness and hallucination rate scores. For plain LLM pipelines, only answer relevancy and latency/cost are evaluated.

---

## Configuration Reference

The `.evalrc.yml` configuration file defines project settings, pipeline connectivity, and pass/fail thresholds.

| Section / Field | Type | Required? | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `version` | string | **Yes** | `"1"` | Configuration spec version |
| `project.name` | string | **Yes** | — | Unique name identifier for your project |
| `project.api_url` | string | **Yes** | `"http://localhost:8000"` | Base URL of your `llmeval` backend API |
| `project.api_key` | string | **Yes** | `${LLMEVAL_API_KEY}` | API key for authentication |
| `pipeline.type` | `"llm" \| "rag"` | **Yes** | `"llm"` | Pipeline architecture type |
| `pipeline.endpoint` | string | **Yes** | — | HTTP POST endpoint to query during eval |
| `pipeline.timeout_seconds` | integer | Optional | `30` | Request timeout per test case |
| `pipeline.headers` | map[str,str] | Optional | `{}` | Custom HTTP headers sent to endpoint |
| `thresholds.hallucination_rate_max` | float \| null | Optional | `null` | Maximum allowed hallucination rate (RAG only) |
| `thresholds.faithfulness_min` | float \| null | Optional | `null` | Minimum required faithfulness score (RAG only) |
| `thresholds.relevancy_min` | float \| null | Optional | `null` | Minimum required answer relevancy score |
| `thresholds.p95_latency_ms_max` | integer \| null | Optional | `null` | Maximum allowed 95th percentile latency in ms |
| `thresholds.cost_per_query_usd_max` | float \| null | Optional | `null` | Maximum allowed average cost per query in USD |
| `judge.model` | string | Optional | `"gpt-4o-mini"` | OpenAI-compatible model used for evaluation |
| `judge.api_key` | string | Optional | `${OPENAI_API_KEY}` | API key for the judge model provider |

---

## Metrics

| Metric | Description | Pipeline type | Better when |
| :--- | :--- | :--- | :--- |
| `relevancy_avg` | Is the actual answer relevant to the input question? | both | **higher** |
| `faithfulness_avg` | Is the answer strictly grounded in retrieved context chunks? | RAG only | **higher** |
| `hallucination_rate` | Fraction of ungrounded statements (`1.0 - faithfulness_avg`) | RAG only | **lower** |
| `p95_latency_ms` | 95th percentile request response time across all cases | both | **lower** |
| `avg_cost_usd` | Average API cost incurred per evaluation query | both | **lower** |

---

## Data and Privacy

Understanding where data flows is important when evaluating sensitive corporate or customer prompts:

1. **Persistent Storage**: The `llmeval` backend stores test cases (questions, expected answers), run metadata, and evaluation results (actual answers, retrieved context chunks, latency, and computed scores) inside Postgres/Supabase.
2. **Third-Party API Transmission**: During execution, the runner sends the question, actual answer, and context chunks to the configured judge model (default: OpenAI `gpt-4o-mini`) via RAGAS to compute faithfulness and relevancy scores.
3. **Privacy & Self-Hosting**: To keep all evaluation data completely on-premise without third-party exposure, deploy a self-hosted LLM (e.g., Llama 3 via Ollama or vLLM wrapped with LiteLLM) and point `judge.model` and `judge.api_key` in `.evalrc.yml` to your local judge endpoint.
4. **Security Note (`NEXT_PUBLIC_API_KEY`)**: In this self-hosted single-tenant dashboard, the API key is passed to the frontend bundle via environment variable to authenticate requests to the backend. This is acceptable for single-user self-hosted environments. If hosting on a shared or public network, protect the frontend and API behind an identity proxy (such as Cloudflare Access, OAuth2 Proxy, or VPN).

---

## License

[MIT](LICENSE)
