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

### 6. Data pipeline
```bash
cd data-pipeline
pip install -e .

# Generate synthetic fixtures
medico-generate --count 100 --out research/facilities_sample.json

# Load into Postgres
medico-load --file research/facilities_sample.json
```

## Services

| Service   | Port  | Image              |
|-----------|-------|--------------------|
| Postgres  | 5432  | postgres:16-alpine |
| Redis     | 6379  | redis:7-alpine     |
| Backend   | 8000  | (local Dockerfile) |
| Dashboard | 3000  | (npm run dev)      |
