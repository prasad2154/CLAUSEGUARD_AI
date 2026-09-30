
# ClauseGuard AI

**Agentic Contract Risk Detection & Review System**

> Production-quality RAG application powered by LangGraph multi-agent orchestration, Qdrant vector search, local sentence embeddings, and a premium React command-center UI.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Feature Matrix](#feature-matrix)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start — Docker](#quick-start--docker)
- [Quick Start — Local Dev](#quick-start--local-dev)
- [API Reference](#api-reference)
- [Testing](#testing)
- [RAGAS Evaluation](#ragas-evaluation)
- [Environment Variables](#environment-variables)

---

## Overview

ClauseGuard AI ingests legal contracts (PDF, DOCX, TXT), parses and segments clauses, generates dense vector embeddings, stores them in Qdrant, then runs a multi-agent LangGraph workflow to:

- Detect risky/non-standard clauses with exact citation evidence
- Identify missing standard clauses required for the contract type
- Answer questions about any clause with verifiable citations (no hallucination)
- Compare two contract versions and detect semantic and risk-level shifts

Every AI output is grounded in indexed clause text — no fabricated answers.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                        ClauseGuard AI Stack                          │
├──────────────────────────────────────────────────────────────────────┤
│  Frontend (React 18 + Vite + Tailwind v3 + Framer Motion)           │
│  • Dashboard • Upload Studio • Review Studio                        │
│  • Document Vault • Comparison Studio • Playbook Studio             │
├──────────────────────────────────────────────────────────────────────┤
│  FastAPI Backend (Python 3.11)                                       │
│  • /api/upload → ingestion pipeline                                  │
│  • /api/review → LangGraph multi-agent workflow                      │
│  • /api/query  → Citation-grounded Q&A agent                        │
│  • /api/compare → Semantic contract comparison                       │
│  • /api/playbook → Configurable risk rules                           │
│  • /api/metrics  → Live analytics                                    │
│  • /health       → Dependency health check                           │
├──────────────────────────────────────────────────────────────────────┤
│  Ingestion Pipeline                                                  │
│  PDF (PyMuPDF + pdfplumber) → OCR fallback (Tesseract) →           │
│  DOCX (python-docx) → Clause Segmenter → Metadata Extractor        │
├──────────────────────────────────────────────────────────────────────┤
│  Agent Layer (LangGraph)                                             │
│  Orchestrator → Risk Agent → Missing Clause Agent →                 │
│  Compliance Agent → Synthesis Agent                                  │
│  (separate) Q&A Agent → Comparison Agent                            │
├──────────────────────────────────────────────────────────────────────┤
│  Storage                                                             │
│  PostgreSQL (metadata, clauses, reviews, queries)                   │
│  Qdrant (clause embeddings — all-MiniLM-L6-v2, 384-dim)            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Feature Matrix

| Feature | Status | Description |
|---|---|---|
| PDF Upload & Extraction | ✅ | PyMuPDF + pdfplumber native text extraction |
| DOCX Upload | ✅ | python-docx full document parsing |
| OCR for Scanned PDFs | ✅ | Tesseract fallback for non-selectable text |
| Clause Segmentation | ✅ | Regex + heuristic boundary detection |
| Dense Embeddings | ✅ | all-MiniLM-L6-v2 local model (no API key) |
| Qdrant Vector Store | ✅ | Persistent clause embedding index |
| Risk Detection | ✅ | Multi-agent LangGraph risk scoring |
| Missing Clause Detection | ✅ | Playbook-driven standard clause audit |
| Citation-Grounded Q&A | ✅ | Exact clause citations, no hallucination |
| Contract Comparison | ✅ | Semantic clause-level diff with risk scoring |
| Playbook Rules | ✅ | Configurable risk policy library |
| Dashboard Analytics | ✅ | Real-time metrics from PostgreSQL |
| Health Monitoring | ✅ | All service dependency status |
| RAGAS Evaluation | ✅ | Faithfulness & grounding benchmarks |

---

## Tech Stack

### Backend
- **FastAPI 0.111** — async API framework
- **LangGraph 0.1** — multi-agent orchestration DAG
- **LangChain 0.2** — LLM tooling and chains
- **Qdrant 1.9** — high-performance vector database
- **sentence-transformers** — local `all-MiniLM-L6-v2` embeddings
- **SQLAlchemy 2.0 + Alembic** — ORM and migrations
- **PostgreSQL 15** — relational metadata store
- **PyMuPDF, pdfplumber, pytesseract** — document ingestion
- **pytest + RAGAS** — testing and evaluation

### Frontend
- **React 18 + TypeScript** — UI framework
- **Vite 5** — build tool
- **Tailwind CSS v3** — utility-first styling
- **Framer Motion** — animations
- **Recharts** — analytics charts
- **Axios** — typed HTTP client
- **React Router v6** — SPA routing

### Infrastructure
- **Docker + docker-compose** — container orchestration
- **Nginx** — frontend static serving and proxy

---

## Project Structure

```
clauseguard_ai/
├── backend/
│   ├── app/
│   │   ├── agents/          # LangGraph multi-agent workflow
│   │   ├── api/             # FastAPI routers
│   │   ├── comparison/      # Contract diff engine
│   │   ├── ingestion/       # PDF/DOCX/OCR pipeline
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── retrieval/       # Embeddings + Qdrant + Reranker
│   │   ├── review/          # Risk engine + report generator
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── services/        # DB service layer
│   ├── tests/               # Pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── lib/             # api.ts, types.ts, utils.ts
│   │   ├── pages/           # Dashboard, Upload, Review, Compare, Playbook, Library
│   │   └── components/layout/  # MainLayout + animated dock
│   ├── Dockerfile
│   └── nginx.conf
├── evaluation/
│   └── ragas_eval.py        # RAGAS benchmarking script
├── sample_contracts/        # Test contracts (balanced + high-risk)
├── docker-compose.yml
└── .env.example
```

---

## Quick Start — Docker

```bash
# 1. Clone the repository
git clone https://github.com/yourorg/clauseguard-ai.git
cd clauseguard-ai

# 2. Set up environment
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY (or ANTHROPIC_API_KEY)

# 3. Start all services
docker compose up --build

# 4. Access the app
open http://localhost       # Frontend UI
open http://localhost:8000/docs  # FastAPI Swagger docs
```

---

## Quick Start — Local Dev

### Backend

```bash
cd backend

# Create and activate virtual environment
    # Linux/Mac

pip install -r requirements.txt

# Set environment variables (copy .env.example)
cp ../.env.example .env

# Run infrastructure (Postgres + Qdrant)
docker compose up postgres qdrant -d

# Start FastAPI dev server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # Starts at http://localhost:5173
```

---

## API Reference

Full interactive docs available at `http://localhost:8000/docs` (Swagger UI).

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/upload` | Upload and ingest a contract (PDF/DOCX/TXT) |
| `GET` | `/api/documents` | List all documents (paginated) |
| `GET` | `/api/documents/{id}` | Get document metadata |
| `GET` | `/api/documents/{id}/clauses` | Get all parsed clauses |
| `DELETE` | `/api/documents/{id}` | Delete document + embeddings |
| `POST` | `/api/review` | Run multi-agent risk review |
| `GET` | `/api/review/{doc_id}` | Retrieve latest review |
| `POST` | `/api/query` | Ask a grounded Q&A question |
| `POST` | `/api/compare` | Compare two contract versions |
| `GET` | `/api/playbook` | List compliance rules |
| `POST` | `/api/playbook` | Create new risk rule |
| `PUT` | `/api/playbook/{id}` | Update or toggle a rule |
| `DELETE` | `/api/playbook/{id}` | Remove a rule |
| `GET` | `/api/metrics` | System analytics |
| `GET` | `/health` | Service health check |

---

## Testing

```bash
cd backend

# Run all tests
pytest

# Run with coverage report
pytest --cov=app --cov-report=html

# Run specific test class
pytest tests/test_api.py::TestPlaybookEndpoint -v
pytest tests/test_ingestion.py::TestClauseSegmenter -v
pytest tests/test_schemas.py -v
```

---

## RAGAS Evaluation

```bash
# 1. Upload a sample contract first
curl -X POST http://localhost:8000/api/upload \
  -F "file=@sample_contracts/service_agreement_balanced.txt"

# 2. Note the document_id from the response

# 3. Run RAGAS evaluation
cd backend
python ../evaluation/ragas_eval.py \
  --document_id <your_document_id> \
  --base_url http://localhost:8000 \
  --output ../evaluation/results.json

# 4. For full LLM-graded RAGAS evaluation (requires OpenAI API key)
python ../evaluation/ragas_eval.py \
  --document_id <your_document_id> \
  --full_ragas
```

**Grounding benchmark target: ≥ 80% of answers citation-grounded**

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection URL | `postgresql://clauseguard:clauseguard@localhost:5432/clauseguard` |
| `QDRANT_HOST` | Qdrant hostname | `localhost` |
| `QDRANT_PORT` | Qdrant port | `6333` |
| `LLM_PROVIDER` | LLM provider (`openai` or `anthropic`) | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | — |
| `LLM_MODEL` | Model to use for agents | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Local embedding model | `all-MiniLM-L6-v2` |
| `UPLOAD_DIR` | Directory for uploaded files | `./uploads` |
| `MAX_FILE_SIZE_MB` | Upload size limit | `25` |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |

## Demo Images
Dashboard Ui
<img width="1841" height="862" alt="dashboard" src="https://github.com/user-attachments/assets/c0898d49-2fe4-4dd7-804e-253a5103336c" />
Documents Uploded
<img width="1856" height="857" alt="Screenshot 2026-09-30 230453" src="https://github.com/user-attachments/assets/ffd74927-dfa7-45b6-b1a9-32b15d6ecb5d" />
Analysis Page
<img width="1892" height="845" alt="analysis" src="https://github.com/user-attachments/assets/56776601-59eb-4833-be0d-81d7e8d9e115" />
Q/A chatbot
<img width="417" height="732" alt="image" src="https://github.com/user-attachments/assets/a205a2ed-3ab1-436a-a00d-bd3337ec2cb3" />

Comparision of Files
<img width="1781" height="857" alt="comparision" src="https://github.com/user-attachments/assets/ab7cd1bb-d6c7-49e2-9f49-8e77fd251404" />
Rules
<img width="1746" height="862" alt="rules" src="https://github.com/user-attachments/assets/9931ccaa-b5cc-460f-9aa3-188cb5baa5dc" />







=======
# CLAUSEGUARD_AI
>>>>>>> 9227441165c7e42e49f304facde3c71a06f00996
