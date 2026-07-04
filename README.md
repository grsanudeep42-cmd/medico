# medico — Monorepo

A full-stack healthcare facilities platform.

```
medico/
├── backend/          FastAPI · SQLAlchemy (async) · Alembic · Redis
├── dashboard/        Next.js 14 (App Router) · Tailwind CSS
├── field-app/        Flutter · sqflite (offline-first)
├── data-pipeline/    Python package
│   ├── research/     Raw facility JSON files (drop here)
│   └── scripts/      loader.py · generator.py
├── docker-compose.yml
└── .env.example
```

## Quick start

### 1. Environment
```bash
cp .env.example .env
# Fill in DATABASE_URL, REDIS_URL, SECRET_KEY, POSTGRES_PASSWORD
```

### 2. Infrastructure + backend (Docker)
```bash
docker compose up --build
# FastAPI → http://localhost:8000
# Health  → http://localhost:8000/health
```

### 3. Run Alembic migrations
```bash
cd backend
pip install -r requirements.txt
DATABASE_URL=<your-url> alembic upgrade head
```

### 4. Dashboard (Next.js)
```bash
cd dashboard
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_BASE_URL
npm install
npm run dev
# http://localhost:3000
```

### 5. Field app (Flutter)
```bash
cd field-app
flutter pub get
flutter run
```

### 6. Data pipeline & Simulation

All pipeline commands should be executed from within your active Python virtual environment (e.g. using `backend/.venv`):

```bash
cd data-pipeline
# Install dependencies and register CLI entrypoints
pip install -e .

# 1. Generate schema-compliant synthetic facility fixtures
medico-generate --count 10 --out research/facilities_sample.json

# 2. Ingest facilities, departments, equipment, and daily averages into Postgres
medico-load --file research/facilities_sample.json

# 3. Seed historical operational metrics (stock, staff, attendance, diagnostics)
python scripts/seed_test_data.py

# 4. Simulate real-time daily operational footfall and log activity
medico-generate-logs
```

## AI Operations Control Room

The Medico backend contains an intelligent, real-time analytics module (`backend/app/routers/ai.py`) that monitors and scores district facility performance:
- **Dynamic Risk Assessment**: Evaluates and flags facilities based on stock-out frequencies (>20%), bed occupancy volatilities (>0.30), low doctor attendance (<80%), diagnostic test availability gaps against IPHS requirements (>30%), and footfall deviations.
- **Stock Demand Forecasting**: Automatically predicts medicine stock-out thresholds and sounds early warnings if resources fall below reorder thresholds or have less than 7 days of supply.
- **Smart Redistribution Suggestions**: Recommends optimal cross-facility stock transfer actions to resolve critical shortages without needing manual supply chain intervention.

You can access these metrics at `http://localhost:3000/ai-ops` on the district admin dashboard.

## Services

| Service   | Port  | Image              | Description |
|-----------|-------|--------------------|-------------|
| Postgres  | 5432 / 5433 | postgres:16-alpine | Dynamic database backend |
| Redis     | 6379  | redis:7-alpine     | WebSocket live operations pub/sub |
| Backend   | 8000  | (FastAPI Application) | API endpoints & AI Analytics pipeline |
| Dashboard | 3000  | (Next.js Application) | District Admin Console |

