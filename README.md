# AeroFlow: AI-Powered Transaction Processing Pipeline

AeroFlow is a modern, containerized transaction processing system. It accepts raw financial transaction logs (CSV), normalizes them via a cleaning engine, detects statistical spending anomalies, batches classifications through Gemini 2.5 Flash, and creates visual analytics reports.

## 🏗️ Architecture Design & Data Flow

👉 **[Interactive Architecture Diagram (Google Drive)](https://drive.google.com/file/d/1LBz13vjlMBJVbT4iN3CrbPicosMQTg2j/view?usp=drive_link)**

🎥 **[Project Walkthrough Video (Loom)](https://www.loom.com/share/8584350389a34388b9b829bd703740f4)**

```
                     ┌──────────────────┐
                     │  React Frontend  │ (Port 5173)
                     └────────┬─────────┘
                              │ HTTP
                              ▼
                     ┌──────────────────┐
                     │   FastAPI API    │ (Port 8000)
                     └────────┬─────────┘
                              │
       ┌──────────────────────┼───────────┐
       │ PostgreSQL DB        │ Redis     │ (Job queue & broker)
       │  (Jobs & Txns)       │ Backend   │
       └──────────────────────┴─────┬─────┘
                                    │
                                    ▼ 
                              ┌───────────┐
                              │  Celery   │ (Workers)
                              │  Worker   │
                              └─────┬─────┘
                                    │ 
                                    ▼
                              ┌───────────┐
                              │  Gemini   │ (AI Categorization & Summary)
                              │ 2.5 Flash │
                              └───────────┘
```

1. **Upload Lifecycle:** Client uploads CSV &rarr; FastAPI saves file to a shared Docker volume, creates a database record (status: `pending`), enqueues a Celery task, and immediately returns a Job ID.
2. **Workers Pipeline:** The Celery worker picks up the Job ID &rarr; runs data cleaning (deduplication, date parsing) &rarr; runs per-account median outlier detection &rarr; batches missing categories through Gemini API (batches of 20) &rarr; requests an executive summary &rarr; bulk-persists transactions &rarr; updates Job to `completed`.
3. **Reactive UI:** The React client polls the status API, presenting an animated progress bar. On completion, it displays spend charts, anomaly indicators, and the narrative.

---

## 🛠️ Tech Stack

* **Frontend:** React, Vite, Tailwind CSS, Recharts, Lucide Icons
* **Backend API:** FastAPI, SQLAlchemy 2.0 (ORM), Pydantic v2, Loguru (Structured Logging)
* **Task Queue:** Celery, Redis (Broker/Backend)
* **Database:** PostgreSQL 15 (Timescale/Alpine)
* **AI Engine:** Gemini 2.5 Flash (via official Google Generative AI SDK)
* **Orchestration:** Docker, Docker Compose

---

## 🚀 Setup & Execution Guide

### Prerequisite
Ensure you have **Docker** and **Docker Compose** installed on your system.

### Step 1: Configure Environment Variables
Create a file named `.env` in the root directory (alongside `docker-compose.yml`) and paste your Gemini API key:
```env
GEMINI_API_KEY=your-actual-api-key-here
```
*(If the key is left empty or invalid, the pipeline runs gracefully using programmatic fallbacks for classification and summaries, ensuring the container never crashes).*

### Step 2: Spin Up Containers
Launch all services using a single command:
```bash
docker compose up --build
```
This builds and starts:
- **FastAPI API** at `http://localhost:8000`
- **React Frontend** at `http://localhost:5173`
- **Postgres Database** at `localhost:5432`
- **Redis Queue** at `localhost:6379`
- **Celery Worker Thread**

---

## 📡 API Documentation & Verification

### 1. API Health Check
Returns the connection health status of PostgreSQL and Redis databases.
* **Request:** `GET http://localhost:8000/health`
* **Curl:**
```bash
curl -X GET http://localhost:8000/health
```

### 2. Ingest Transaction CSV
Uploads a transaction spreadsheet and starts the pipeline.
* **Request:** `POST http://localhost:8000/jobs/upload`
* **Curl:**
```bash
curl -X POST http://localhost:8000/jobs/upload \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@transactions.csv"
```

### 3. Poll Pipeline Status
Returns progress percentage (0-100%) and current status.
* **Request:** `GET http://localhost:8000/jobs/{job_id}/status`
* **Curl:**
```bash
curl -X GET http://localhost:8000/jobs/YOUR_JOB_UUID_HERE/status
```

### 4. Fetch Analysis Results
Retrieves aggregated spend metrics, category breakdowns, anomalies list, and clean records.
* **Request:** `GET http://localhost:8000/jobs/{job_id}/results`
* **Curl:**
```bash
curl -X GET http://localhost:8000/jobs/YOUR_JOB_UUID_HERE/results
```

### 5. List Historical Ingestions
* **Request:** `GET http://localhost:8000/jobs`
* **Curl:**
```bash
curl -X GET http://localhost:8000/jobs
```

---

## 📈 Scale & Bottleneck Analysis (For Video Review)

If this pipeline handles a 100x scale increase (10,000+ simultaneous uploads), here is where it breaks and the production solutions:

1. **File Ingestion & Memory (OOM):** 
   * *Problem:* Loading massive files in memory using `pandas.read_csv` will exhaust container RAM.
   * *Solution:* Stream file uploads directly to disk/S3 and parse them using chunk generators (`pd.read_csv(..., chunksize=1000)`).
2. **Database I/O Bottlenecks:**
   * *Problem:* ORM inserting transactions one-by-one locks database threads.
   * *Solution:* Implement PostgreSQL `COPY` commands or SQLAlchemy Core bulk insertions (`bulk_insert_mappings`) in batches of 5000 records. Add a PgBouncer connection pool.
3. **AI API Rate Limits:**
   * *Problem:* Thousands of batched requests will exceed Gemini TPM/RPM limits.
   * *Solution:* Set up a dedicated throttled Celery queue for LLM tasks, implementing token-bucket rate limiters.
