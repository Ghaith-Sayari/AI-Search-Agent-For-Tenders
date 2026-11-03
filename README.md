# TenderIntel — AI Search Agent for Tenders

TenderIntel is an AI-assisted tender discovery and qualification platform. It collects procurement opportunities from configurable sources, normalizes and validates the data, applies a Gatekeeper policy layer, scores opportunities against a company profile, and exposes the results through a FastAPI backend and React operations console.

The platform is designed to reduce the time spent searching tender portals while keeping automated decisions observable, auditable, and safe to review before a proposal is generated.

## What the system does

- Scrapes tender portals and other configured sources.
- Normalizes source-specific payloads into a canonical opportunity contract.
- Deduplicates records and loads them into Supabase/PostgreSQL.
- Uses the Gatekeeper agent to detect junk, apply eligibility policies, and route records to `approved`, `rejected`, `needs_review`, `expired`, or `failed`.
- Uses the Opportunity Analyzer to score approved tenders for domain, geography, budget, eligibility, and strategic fit.
- Routes uncertain results to a human review queue.
- Generates, reviews, scores, and exports proposal drafts.
- Tracks pipeline runs, stage progress, LLM usage, system health, and notification delivery.
- Supports semantic search over stored opportunities.

## Architecture

The implemented flow follows the supplied architecture:

```text
Tender portals / RSS
        |
        v
Python scrapers (Playwright/HTTP)
        |
        v
Normalization + source mapping + Pydantic validation
        |
        +--> Raw JSON / Supabase Storage
        |
        v
Supabase/PostgreSQL staging tables
        |
        v
LangGraph orchestration
        |
        +--> Gatekeeper agent
        |       |
        |       +--> approved -> production tender store
        |       +--> needs_review -> review queue
        |       +--> rejected/expired/failed -> audited decision
        |
        +--> Opportunity Analyzer
        |       |
        |       +--> good fit / review / not fit
        |
        +--> Proposal Generator
                |
                +--> Markdown/DOCX proposal output

React console <---- FastAPI API ----> Supabase/PostgreSQL
                                      |
                                      +--> email notification worker
```

The repository also contains `graph.png`, a generated view of the LangGraph orchestration.

## Repository structure

| Path | Purpose |
| --- | --- |
| `scrapers/` | Scraper registry, base class, and source implementations. |
| `mappings/` | Source-to-canonical field mappings and validation schemas. |
| `pipeline/` | Normalization, hashing, Celery tasks, and compatibility pipeline wrappers. |
| `agents/gatekeeper/` | Policy-driven tender classification, audit records, and dead-letter handling. |
| `agents/opportunity_analyzer/` | Deterministic signals, semantic/keyword analysis, LLM judgment, scoring, and persistence. |
| `agents/proposal_generator/` | Proposal context preparation, section drafting, compliance review, scoring, and export. |
| `orchestration/langgraph/` | LangGraph state, nodes, routing, checkpointing, and run execution. |
| `api/` | FastAPI application, routes, schemas, services, repositories, and mappers. |
| `db/migrations/` | SQL migrations for Supabase/PostgreSQL tables and indexes. |
| `frontend/` | React 19 + Vite operations console. |
| `configs/` | Model and scoring policy configuration. |
| `data/raw_scrapes/` | Local raw scraper payloads and diagnostics. |
| `DATA_GOVERNANCE.md` | Data contracts, deduplication, idempotency, and DLQ rules. |

## Technology stack

- **Backend:** Python, FastAPI, Pydantic, Uvicorn
- **Agents/orchestration:** LangGraph-style orchestration, local Ollama-compatible LLM endpoints, optional LangSmith tracing
- **Ingestion:** Playwright, BeautifulSoup, source-specific Python scrapers
- **Persistence:** Supabase/PostgreSQL, Supabase Storage, vector search with `sentence-transformers`
- **Background processing:** Celery and Redis
- **Frontend:** React, TypeScript, Vite, Tailwind CSS, Recharts
- **Proposal output:** Markdown, DOCX, and PDF-related rendering dependencies

## Prerequisites

- Python 3.10+
- Node.js 18+ (or Bun)
- A Supabase project with the SQL migrations applied
- An Ollama-compatible local model endpoint for the agents
- Redis if Celery tasks are used
- Playwright browser dependencies

## Backend setup

```bash
git clone https://github.com/Ghaith-Sayari/AI-Search-Agent-For-Tenders.git
cd AI-Search-Agent-For-Tenders

python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
playwright install
```

Create a `.env` file in the repository root. At minimum, configure:

```dotenv
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-key

OLLAMA_BASE_URL=http://localhost:11434
GATEKEEPER_MODEL=llama3.2:3b
OPPORTUNITY_ANALYZER_MODEL=llama3.2:3b
PROPOSAL_GENERATOR_MODEL=llama3.2:3b
OPPORTUNITY_ANALYZER_PROFILE_ID=your-profile-id
```

Optional configuration includes:

- `OPPORTUNITY_ANALYZER_OLLAMA_BASE_URL`
- `OPPORTUNITY_ANALYZER_EMBEDDING_MODEL`
- `PIPELINE_INGESTION_PER_SOURCE_LIMIT`
- `PIPELINE_GATEKEEPER_MAX_ITEMS`
- `PIPELINE_ANALYSIS_MAX_ITEMS`
- `PIPELINE_INGESTION_USE_SUBPROCESS`
- `PIPELINE_INGESTION_FALLBACK_TO_RAW`
- `GATEKEEPER_LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, and `LANGSMITH_PROJECT`
- `OFFER_EMAIL_NOTIFICATIONS_ENABLED` and the `OFFER_EMAIL_SMTP_*` settings

### Database migrations

Run the SQL files in `db/migrations/` in filename order using the Supabase SQL editor or your normal migration workflow. The migrations create the staging, production, gatekeeper audit, analysis, proposal, pipeline-run, and notification tables.

The ingestion layer uses deterministic keys and database-level uniqueness to make retries safe. Invalid records are rejected by the canonical contract and can be routed to the Gatekeeper dead-letter records instead of blocking the full batch.

## Running the backend

Start the API:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

API documentation is available at:

- `http://localhost:8000/docs`
- `http://localhost:8000/redoc`
- `http://localhost:8000/health`

Run the scraper discovery entrypoint:

```bash
python main.py
```

Run opportunity analysis directly:

```bash
python run_opportunity_analyzer.py \
  --profile-id "$OPPORTUNITY_ANALYZER_PROFILE_ID" \
  --limit 5
```

Run the LangGraph orchestration directly:

```bash
python run_orchestration.py
```

The API also exposes `POST /v1/runs`, which starts a pipeline run in the background. Supported modes are `full`, `analysis_only`, and `gatekeeper_only`.

## Celery worker

Redis-backed ingestion tasks are defined in `pipeline/tasks.py`.

```bash
celery -A pipeline.tasks.app worker --loglevel=INFO
```

The normal task queue is `default`; failed tasks can be routed to the `dead_letter` queue after retries are exhausted.

## Frontend setup

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```dotenv
VITE_API_BASE_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

The console is served on `http://localhost:3000`. It provides dashboards for opportunities, analyses, proposals, review items, pipeline runs, system health, cost usage, and company-profile onboarding.

Useful frontend commands:

```bash
npm run build
npm run lint
npm run preview
```

## API overview

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Backend health check. |
| `GET` | `/v1/opportunities` | Filter and sort analyzed opportunities. |
| `GET` | `/v1/opportunities/{id}` | Read one opportunity. |
| `GET/POST` | `/v1/runs` | List or start pipeline runs. |
| `GET` | `/v1/runs/{id}` | Read run progress and stage details. |
| `GET/POST` | `/v1/reviews` | List and resolve human review items. |
| `GET/POST/PATCH` | `/v1/proposals` | Create, generate, edit, and inspect proposals. |
| `POST` | `/v1/proposals/{id}/export` | Export a proposal. |
| `GET/PUT` | `/v1/company-profile` | Read or update the matching profile. |
| `GET` | `/v1/agents/status` | Read agent/service status. |
| `GET` | `/v1/metrics/cost` | Read LLM usage and estimated cost metrics. |

## Scoring and decision policy

The default policy in `configs/scoring.yaml` scores opportunities from 0 to 100:

- Domain relevance: 35%
- Geography fit: 20%
- Budget fit: 20%
- Eligibility fit: 15%
- Strategic fit: 10%

Default decisions are:

- `75–100`: good fit / pursue
- `50–74.99`: needs review
- `0–49.99`: not fit

Hard blockers, deadline rules, high-risk terms, and sector/geography policies are documented under `agents/gatekeeper/policies/`.

## Reliability and governance

The ingestion pipeline is built around the following safeguards:

1. Source-specific mappings produce a canonical, validated record.
2. Deterministic hashes and a unique database key prevent duplicate opportunities and repeated processing.
3. Batch failures are isolated; malformed records are not silently written to production.
4. Gatekeeper decisions and evidence are persisted for auditability.
5. Pipeline runs expose stage status, counters, errors, retries, and LLM usage.
6. Optional raw JSON fallback and isolated scraper subprocesses improve resilience around browser-based scraping.

See [`DATA_GOVERNANCE.md`](DATA_GOVERNANCE.md) for the complete data contract and DLQ specification.

## Testing

Install the development dependencies from `requirements.txt`, then run:

```bash
pytest
```

For frontend type-checking and build validation:

```bash
cd frontend
npm run lint
npm run build
```

## License and project status

This repository does not currently declare a license file. Confirm the intended license before distributing or deploying the project. The codebase is under active development; review environment settings, scraper selectors, model availability, and database migrations before using it in production.
