# Implementation Plan - NyayaFlow AI-Powered Transaction Processing Pipeline

NyayaFlow is an asynchronous financial transaction processing pipeline designed to ingest, clean, categorize, and analyze raw transaction logs. It utilizes FastAPI for the API layer, Celery & Redis for asynchronous task processing, PostgreSQL for structured storage, Gemini 2.5 Flash for AI classification & narrative summarizing, and React for a rich, visual user interface.

## User Review Required

> [!IMPORTANT]
> **Alembic vs. Auto-creation:** We will configure Alembic migrations, but we will also implement an automatic database table creation check at API startup. This ensures that the reviewer can just run `docker compose up` and have everything run perfectly without having to manually run migrations.
>
> **Gemini API Key:** The Gemini API key will be read from a `.env` file passed into the Docker Compose environment as `GEMINI_API_KEY`. The user will need to provide a valid API key in their local `.env` file.
>
> **Median Calculation Scope:** Anomaly detection (Rule 1: amount > 3x median) will calculate the median for each account using all transactions in the database. If it's a brand new account with no historical data, it will fall back to using the transactions present within the currently uploaded CSV.

## Open Questions

No blocker questions, but we will proceed with the assumptions below:
1. **Gemini SDK:** We will use the official Google GenAI Python SDK (`google-genai` or `google-generativeai`) to connect to the Gemini API.
2. **Missing Transaction IDs:** Some CSV rows have missing `txn_id`. We will generate a unique UUID prefix or a synthetic transaction ID (e.g., `TXN_SYNTH_...`) so we can reference them cleanly, but preserve a flag showing they were missing.

---

## Proposed Changes

We will create the following folder structure and files inside `c:\Users\Lenovo\Documents\VSCode\Backend DevOps`:

```
backend/
├── app/
│   ├── api/
│   │   ├── health.py         # [NEW] API health check endpoints
│   │   └── jobs.py           # [NEW] Job upload, status, results, and list API
│   ├── core/
│   │   ├── config.py         # [NEW] Settings and environment variables loading
│   │   ├── database.py       # [NEW] SQLAlchemy session management and engine
│   │   └── celery.py         # [NEW] Celery worker configuration
│   ├── models/
│   │   ├── base.py           # [NEW] Base model
│   │   ├── job.py            # [NEW] Job database model
│   │   ├── transaction.py    # [NEW] Transaction database model
│   │   └── summary.py        # [NEW] Job Summary database model
│   ├── schemas/
│   │   ├── job.py            # [NEW] Pydantic models for Job endpoints
│   │   └── transaction.py    # [NEW] Pydantic models for Transaction endpoints
│   ├── services/
│   │   ├── csv_processor.py      # [NEW] CSV parsing and normalization
│   │   ├── anomaly_detector.py   # [NEW] Statistical and business rules anomaly engine
│   │   ├── llm_service.py        # [NEW] Batched LLM classification & retry decorator
│   │   └── summary_service.py    # [NEW] Job summary extraction & narrative generation
│   ├── workers/
│   │   └── tasks.py          # [NEW] Celery tasks (process_csv_task)
│   ├── utils/
│   │   ├── logger.py         # [NEW] Loguru structured logging configuration
│   │   └── retry.py          # [NEW] Tenacity retry decorator wrapper
│   └── main.py               # [NEW] FastAPI application entry point
├── Dockerfile                # [NEW] Backend service docker container
├── requirements.txt          # [NEW] Python dependencies
├── alembic.ini               # [NEW] Alembic config
└── alembic/                  # [NEW] DB Migrations directory

frontend/                     # [NEW] React + Vite + Tailwind CSS Application
├── package.json
├── index.html
├── src/
│   ├── App.jsx
│   ├── main.jsx
│   ├── index.css
│   └── components/
│       ├── FileUpload.jsx
│       ├── JobProgress.jsx
│       ├── Dashboard.jsx
│       └── TransactionTable.jsx

docker-compose.yml            # [NEW] Single orchestrator compose file
README.md                     # [NEW] Project documentation, setup guide, curl scripts
```

---

## Detailed Phase-Wise Task List

### Phase 1: Docker & Database Foundations
- [ ] Create `backend/requirements.txt` with FastAPI, Celery, Redis, SQLAlchemy 2.0, Pydantic v2, Loguru, Tenacity, Pandas, and Gemini client.
- [ ] Create database models (`Job`, `Transaction`, `JobSummary`) using SQLAlchemy 2.0.
- [ ] Create database connectivity helper (`core/database.py`) and config loader (`core/config.py`).
- [ ] Initialize Alembic config and create the first migration script.
- [ ] Build `backend/Dockerfile` and root `docker-compose.yml` defining `api`, `postgres`, `redis`, and `worker` services.

### Phase 2: Processing Pipeline (Engines)
- [ ] **Data Cleaning Engine (`services/csv_processor.py`):**
  - Normalize dates (supporting `DD-MM-YYYY` and `YYYY/MM/DD` to `YYYY-MM-DD`).
  - Strip currency prefixes (e.g. `$` and whitespace).
  - Normalize currency to upper-case (e.g. `INR`, `USD`).
  - Normalize transaction status to upper-case (`SUCCESS`, `FAILED`, `PENDING`).
  - Clean missing categories to `UNCATEGORIZED`.
  - Drop exact duplicates and record raw vs clean row counts.
- [ ] **Anomaly Detection Engine (`services/anomaly_detector.py`):**
  - Implement per-account median calculator (Rule 1). Flag transactions > 3x median.
  - Implement domestic merchant USD flagger (Rule 2).
- [ ] **AI Classification & Summarizer (`services/llm_service.py`):**
  - Add robust batched category classification (mapping custom index to transaction rows).
  - Add retry mechanism using `tenacity` for resilience.
  - Create narrative summary generation with Pydantic structured output validation.

### Phase 3: Background Workers & API Layer
- [ ] Implement Celery task in `workers/tasks.py` linking all pipeline steps together and updating step-wise progress to the DB.
- [ ] Write FastAPI endpoints in `api/jobs.py`:
  - `POST /jobs/upload` - accepts CSV file, creates Job, starts async task, returns Job ID.
  - `GET /jobs/{id}/status` - returns job status, progress percentage, and high-level stats if completed.
  - `GET /jobs/{id}/results` - returns full clean transactions, anomalies, category spend breakdown, and LLM narrative.
  - `GET /jobs` - list jobs with filter support.
- [ ] Add `GET /health` checking database, redis, and worker health.
- [ ] Configure `loguru` structured logging to print readable status updates during job progress.

### Phase 4: Frontend Development
- [ ] Scaffold React + Vite + Tailwind CSS frontend application.
- [ ] Design File Upload screen with interactive upload state.
- [ ] Build Processing screen with real-time progress bar polling the status API every 3 seconds.
- [ ] Develop Dashboard visual cards for total INR/USD spend, anomaly count, risk level, and the narrative summary.
- [ ] Implement charts for category breakdown and top merchants.
- [ ] Build an interactive searchable table displaying flagged anomalies.

### Phase 5: Verification & Production Polish
- [ ] Write manual verification guide with `curl` requests.
- [ ] Verify execution using `docker compose up`.
- [ ] Draft final project documentation and high-level architecture diagram.

---

## Verification Plan

### Automated/Local CLI Testing
- run `docker compose up --build` to launch all services.
- Test endpoint health: `curl http://localhost:8000/health`.
- Upload sample `transactions.csv` and verify task orchestration logs.
- Test edge cases (missing columns, invalid file format, completely empty categories, large currency anomalies).

### Manual Frontend Testing
- Open application in browser.
- Upload `transactions.csv`.
- Observe the polling progress bar transition smoothly from 0% to 100%.
- Review summary analytics cards, charts, and flagged anomalies.
