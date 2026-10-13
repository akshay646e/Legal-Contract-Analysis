# AI-Powered Legal Contract Analysis & Intelligence Engine (LexAI)

> **Enterprise Stack:** Python 3.12, FastAPI, Generative AI (LLMs), RAG, Prompt Engineering, Pydantic, Vector Database (ChromaDB / pgvector), REST APIs, SQLAlchemy (SQLite/PostgreSQL), Docker, Git, AWS Ready.

An AI-powered legal contract analysis system engineered to automate the review, due diligence, and risk assessment of commercial agreements. The platform extracts key legal clauses, flags unfavorable conditions, generates red-line amendment counter-proposals, compiles executive summaries, and offers an interactive RAG conversational copilot with verifiable clause citations.

---

## 🏛️ High-Level System Architecture

```
                                   +-----------------------------------------------+
                                   |           Uploaded Contract Documents         |
                                   |              (PDF / DOCX / TXT)               |
                                   +-----------------------+-----------------------+
                                                           |
                                                           v
                                   +-----------------------------------------------+
                                   |          Document Ingestion & Parser          |
                                   |      (pypdf / python-docx / Preprocessor)     |
                                   +-----------------------+-----------------------+
                                                           |
                                 +-------------------------+-------------------------+
                                 |                                                   |
                                 v                                                   v
               +-----------------------------------+               +-----------------------------------+
               |    Legal-Aware Chunker & Vector   |               |      LLM Orchestration & Analysis |
               |     (Section Context Injection)   |               |     (Structured Outputs / Prompts)|
               +-----------------+-----------------+               +-----------------+-----------------+
                                 |                                                   |
                                 v                                                   v
               +-----------------------------------+               +-----------------------------------+
               |  ChromaDB / Persistent Vector DB  |               |  - Executive Summaries            |
               |       (Metadata Indexing)         |               |  - Clause Identification          |
               +-----------------+-----------------+               |  - Risk Audit & Redlining         |
                                 |                                 +-----------------+-----------------+
                                 |                                                   |
                                 +-------------------------+-------------------------+
                                                           |
                                                           v
                                   +-----------------------------------------------+
                                   |               FastAPI REST Engine             |
                                   |           (/contracts, /analysis, /chat)      |
                                   +-----------------------+-----------------------+
                                                           |
                                 +-------------------------+-------------------------+
                                 |                                                   |
                                 v                                                   v
               +-----------------------------------+               +-----------------------------------+
               |     Interactive RAG Copilot       |               |     Executive Workbench UI        |
               |      (Grounded Citations)         |               |     (Dark Mode Dashboard)         |
               +-----------------------------------+               +-----------------------------------+
```

---

## 🎓 Personal Trainer Curriculum & Learning Guide

This repository is built as a complete hands-on learning masterclass for enterprise AI engineering.

### 📌 Milestone 1: Multi-Format Document Ingestion Engine
- **Why Naive Text Extraction Fails:** Real-world contracts contain page headers, footers, pagination artifacts (*"Page 3 of 12"*), and non-standard whitespace that corrupt embeddings and prompt contexts.
- **Implementation:** [`app/parsers/document_parser.py`](file:///e:/Legal%20Contract%20Analysis/app/parsers/document_parser.py) and [`app/parsers/preprocessor.py`](file:///e:/Legal%20Contract%20Analysis/app/parsers/preprocessor.py).
- **Key Concepts:** Page tracking per section, multi-format parsing for PDF, DOCX, and TXT, and regex section heading segmentation.

### 📌 Milestone 2: Intelligent Legal-Aware Chunking & Vector DB
- **The Problem with Naive Chunking:** Arbitrary token splitting cuts clauses mid-sentence. For example, splitting a Limitation of Liability clause between the cap and its exception (*"except for willful misconduct"*) causes the LLM to give dangerously incomplete legal advice.
- **The Solution:** [`app/rag/chunker.py`](file:///e:/Legal%20Contract%20Analysis/app/rag/chunker.py) injects hierarchical section prefixes into each chunk (*e.g., `Section 4: Limitation of Liability`*) and splits along sentence boundaries with context overlap.
- **Vector DB:** [`app/rag/vector_store.py`](file:///e:/Legal%20Contract%20Analysis/app/rag/vector_store.py) encapsulates ChromaDB persistence with an automatic in-memory cosine fallback for zero-dependency local runs.

### 📌 Milestone 3: Core AI Analysis Engines (Clauses, Risks, Redlining)
- **Structured Outputs with Pydantic:** Guarantees deterministic, production-safe JSON schemas.
- **Clause Extraction:** [`app/services/clause_extractor.py`](file:///e:/Legal%20Contract%20Analysis/app/services/clause_extractor.py) extracts 8 critical legal clause categories:
  1. Termination (for cause, for convenience, notice cure periods)
  2. Limitation of Liability (aggregate cap, consequential damage waivers)
  3. Indemnification (third-party claims, IP infringement)
  4. Confidentiality (trade secret exclusions, survival duration)
  5. Payment Terms (invoicing, late interest, price increases)
  6. Governing Law & Jurisdiction (venue, forum, choice of law)
  7. Restrictive Covenants (non-solicitation duration)
  8. Intellectual Property & Data Ownership
- **Risk Assessment & Redlining:** [`app/services/risk_analyzer.py`](file:///e:/Legal%20Contract%20Analysis/app/services/risk_analyzer.py) assesses clauses against balanced corporate playbooks, assigns severity (`HIGH`, `MEDIUM`, `LOW`, `SAFE`), and drafts exact redline counter-proposals.

### 📌 Milestone 4: Context-Aware Legal RAG with Citations
- **Zero Hallucination Grounding:** [`app/services/qa_service.py`](file:///e:/Legal%20Contract%20Analysis/app/services/qa_service.py) queries contract-scoped vector embeddings, injects retrieved excerpts into a temperature `0.0` prompt, and returns verbatim clause quotes and section citations.

### 📌 Milestone 5: Production FastAPI Backend & Storage Layer
- **Async REST API:** [`app/api/`](file:///e:/Legal%20Contract%20Analysis/app/api/) implements modular routers:
  - `/api/contracts`: Upload, list, detail, delete, stats
  - `/api/analysis`: Summarize, extract clauses, assess risks, full-pipeline
  - `/api/chat`: Grounded RAG conversational queries & history
- **Database:** SQLAlchemy ORM models in [`app/db/models.py`](file:///e:/Legal%20Contract%20Analysis/app/db/models.py) supporting SQLite for instant zero-config local testing and PostgreSQL for cloud deployments.

### 📌 Milestone 6: Executive Workbench UI Dashboard
- Modern, dark-themed LegalTech UI located in [`app/static/`](file:///e:/Legal%20Contract%20Analysis/app/static/).
- Features: Drag-and-drop upload, contract library, side-by-side tabs (Executive Summary, Key Clauses, Risk & Redline Matrix, Full Document Viewer), and live RAG chat with citation pills.

### 📌 Milestone 7: Containerization & Cloud Deployment
- Multi-stage [`Dockerfile`](file:///e:/Legal%20Contract%20Analysis/Dockerfile) and [`docker-compose.yml`](file:///e:/Legal%20Contract%20Analysis/docker-compose.yml) orchestrating FastAPI and PostgreSQL.

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration (`.env`)
Copy `.env.example` to `.env`:
```ini
APP_NAME="Legal Contract Analysis Engine"
APP_ENV=development
DEBUG=True
PORT=8000
HOST="0.0.0.0"

# Choose "openai", "azure_openai", or "mock" (for zero-cost offline testing)
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-4o-mini
DATABASE_URL=sqlite:///./storage/legal_contracts.db
```

> **Tip:** If you do not have an OpenAI API key yet, set `LLM_PROVIDER=mock`. The entire application, parser, chunker, database, full analysis pipeline, and RAG copilot will run smoothly and deterministically offline!

### 3. Run the Application

#### Option A: Run Backend & Frontend Separately (Modern Industry Standard)
**Terminal 1 — Backend (FastAPI REST Engine):**
```powershell
cd backend
uvicorn app.main:app --reload --port 8000
```
- API & Swagger Docs: **http://localhost:8000/docs**
- Health Check: **http://localhost:8000/health**

**Terminal 2 — Frontend (Vite Dev Server):**
```powershell
cd frontend
npm run dev
```
- Frontend UI Dashboard: **http://localhost:5173/** (automatically proxies API requests to port 8000)

#### Option B: Run Full-Stack via Docker Compose
```powershell
docker-compose up --build
```
- Frontend: **http://localhost:3000**
- Backend API: **http://localhost:8000/docs**

---

## 🧪 Running Automated Tests
Run the test suite with `pytest`:
```powershell
pytest -v
```

---

## ☁️ AWS Cloud Deployment Playbook

For production deployment on AWS:
1. **Compute (AWS ECS Fargate):** Package the container with [`Dockerfile`](file:///e:/Legal%20Contract%20Analysis/Dockerfile) and deploy via Amazon ECS on AWS Fargate.
2. **Database (Amazon RDS PostgreSQL):** Set `DATABASE_URL=postgresql://user:pass@rds-instance:5432/legal_contracts`.
3. **Document Storage (Amazon S3):** Swap local `storage/uploads` for an S3 bucket configured with server-side encryption (SSE-S3 or KMS).
4. **Vector Store:** Use AWS OpenSearch Service or RDS PostgreSQL with the `pgvector` extension.
5. **Observability:** Centralized logging with AWS CloudWatch and AWS X-Ray for tracing LLM latency.
