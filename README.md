# RAG-Based ChatBOT — Natural Language SQL Dashboard System

A production-grade, highly performant full-stack application that converts natural language questions into secure SQL queries via Google Gemini, retrieves precise schema context using a hybrid Qdrant RAG pipeline, executes queries against your MySQL database, and automatically constructs premium visual dashboards alongside AI-generated analytical insights. 

It is composed of a performant **FastAPI backend** and a modern **Angular Single Page Application frontend** served using an Nginx reverse-proxy deployment.

---

## Key Features

1. **Intelligent Query Translation**: Highly tuned multi-turn SQL generation leveraging Google Gemini (`gemini-2.5-flash`), featuring smart schema context extraction, CTE support, and automated error-correction loops.
2. **LangGraph Orchestration**: The entire backend pipeline is built on a formal LangGraph `StateGraph`, providing robust, deterministic state management and explicit conditional routing between multi-agent nodes.
3. **Hybrid RAG Introspection**: Connects to your database, introspects tables/indexes/columns/sample rows, splits the schema into semantically enriched chunks, generates embeddings, and retrieves precise contexts via Qdrant hybrid vector search and Gemini reranking.
4. **Standalone Angular Workspace**: A modular client built using Angular standalone components featuring:
   - **Conversation History Sidebar**: Create, list, load, and delete database-persisted chats.
   - **SQL Debugger Box**: A collapsible syntax-colored container highlighting generated queries and run latency.
   - **Data Visualizer**: Frost-bordered paginated data tables displaying query rows.
   - **Dynamic Dashboards**: Interactive charts (Bar, Line, Scatter, Pie, Funnel, Treemap) compiled client-side using Plotly.js.
   - **AI Statistical Insights Deck**: Diagnostic cards summarizing findings, trends, anomalies (IQR/Z-Score), and recommendations.
5. **DTDL Observability & Evaluation**: Fully closes the Data-To-Dashboard Lifecycle gap with:
   - **LangSmith Tracing**: Deep, node-level visual tracing and latency tracking for every step in the LangGraph pipeline.
   - **RAGAS Metrics**: Automated background evaluation of context precision, recall, answer relevancy, and faithfulness.
   - **LLM-as-Judge**: Automated scoring of the generated SQL correctness against the original natural language intent.
6. **Operations & Security**: JWT-based session security, Prometheus performance metrics middleware, Redis-backed query caching, structured JSON logging, and token usage budget trackers.
7. **Unified Deployment & CI/CD**: Containerized Docker Compose file running Nginx reverse-proxy to serve assets and route APIs on port 80 (eliminating CORS), and GitHub Actions workflows checking backend unit tests and frontend compilation builds.

---

## Directory Architecture

```
Rag_based_ChatBOT/
├── app/                      # FastAPI Backend Workspace
│   ├── api/                 # FastAPI routes (v1: Auth, Chat, Dashboard, SQL, Health)
│   ├── core/                # Config, security, exceptions, middleware, dependencies
│   ├── db/                  # Engine, async session management, Redis, and Qdrant wrappers
│   ├── models/              # SQLAlchemy 2.0 ORM models (User, Conversation, Dashboard, Audit)
│   ├── schemas/             # Pydantic validation schemas (Auth, Chat, SQL, Dashboards)
│   ├── repositories/        # Layered database CRUD logic
│   ├── rag/                 # Introspector, schema chunker, retriever, and Gemini reranker
│   ├── prompts/             # Modular system prompt templates (SQL, Viz, Insights, Summarizer)
│   ├── agents/              # Multi-agent coordinators (Intent, SQL, Validation, Viz, Insight)
│   └── services/            # Main core services (Auth, SQL executor, Cache, Chat, LLM wrapper)
├── frontend/                 # Standalone Angular SPA Workspace
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/  # Standalone components (Login, ChatDashboard)
│   │   │   ├── services/    # Injectable API services (AuthService, ChatService)
│   │   │   └── interceptors/# HTTP interceptor (Automatic Bearer Auth headers insertion)
│   │   ├── index.html       # Loads FontAwesome & Google Fonts
│   │   └── styles.css       # Deep-space glassmorphism global stylesheet
│   └── angular.json         # Compiles global Plotly.js dependencies
├── scripts/                 # Administration CLIs (Index schema, database seeding, benchmarks)
├── deployment/              # Production orchestration (Docker, Compose, Kubernetes, Nginx)
└── .github/workflows/        # Automated CI/CD pipelines (GitHub Actions)
```

---

## Local Development Setup

### 1. Run Core Dependencies
Using Docker, spin up the cache and vector database containers:
```bash
docker run -d -p 6379:6379 redis:7-alpine
docker run -d -p 6333:6333 qdrant/qdrant:latest
```

### 2. Configure Environment
Copy `.env.example` to `.env` and configure credentials:
```env
GEMINI_API_KEY=your_gemini_api_key
DATABASE_URL=mysql+asyncmy://username:password@localhost:3306/your_database
REDIS_URL=redis://localhost:6379/0
QDRANT_URL=http://localhost:6333
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:4200
```

### 3. Initialize & Introspect Schema
Populate base tables and index the schema vectors:
```bash
# Seed standard tables and admin account
python scripts/seed_data.py

# Introspect MySQL database schema and upload vector embeddings to Qdrant
python scripts/index_schema.py
```

### 4. Start Servers
Launch the FastAPI backend server on port 8000:
```bash
uvicorn app.main:app --reload --port 8000
```

Navigate to the frontend folder, install dependencies, and run the Angular server on port 4200:
```bash
cd frontend
npm install
npm start
```
Open **`http://localhost:4200/`** to interact with the RAG ChatBOT!

---

## Production Deployment (Docker Compose)

The application can be deployed locally in production with a single command. The frontend Nginx container serves the Angular app and reverse-proxies `/api/v1/` calls to the FastAPI container on port `80`, bypassing any CORS limitations.

1. Configure `.env` variables.
2. Build and start containers:
   ```bash
   cd deployment/docker
   docker-compose up --build -d
   ```
3. Open **`http://localhost/`** in your browser.

---

## CI/CD Pipeline (GitHub Actions)

An automated CI/CD workflow is set up under `.github/workflows/ci-cd.yml` to run on any `push` or `pull_request` to `main`/`master` branches:
- **Backend Validation**: Spins up temporary Redis and Qdrant services in isolation, installs python requirements, checks python file syntax, and runs pytest.
- **Frontend Validation**: Sets up Node 18, installs npm packages, and runs Angular production compilation check (`npm run build`).
