# 🏥 Medico — AI-Driven Real-Time Health Centre Management Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Next.js 14](https://img.shields.io/badge/Next.js%2014-000000?style=for-the-badge&logo=nextdotjs)](https://nextjs.org/)
[![Flutter](https://img.shields.io/badge/Flutter-02569B?style=for-the-badge&logo=flutter)](https://flutter.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

---

## 🎯 WOW 2026 Hackathon Submission
**Medico** is a full-stack, enterprise-grade monorepo designed to solve critical operational inefficiencies in primary and community health centres (PHCs and CHCs) across public health districts.

---

## 🔴 The Problem

Primary Health Centres (PHCs) and Community Health Centres (CHCs) form the backbone of rural healthcare, yet they suffer from **recurring, severe operational gaps**:
*   **Critical Medicine Stock-Outs**: Vital medicines run dry without early warning.
*   **Unmanaged Patient Footfall**: Overcrowding or massive under-utilization of rural clinics goes unnoticed.
*   **Bed Unavailability**: Real-time admission capacities are completely invisible.
*   **Predictable Doctor Attendance Gaps**: Absenteeism directly impacts quality of care but is rarely flagged in real-time.
*   **Manual Tracking Overload**: Operational data is logged manually on paper registers, leading to a total lack of centralized, real-time visibility for district health administrators.

---

## ⚡ The Challenge

Build a **multilingual AI-enabled platform** for real-time health centre management covering:
1.  **Stock monitoring** and early stock-out warnings.
2.  **Patient footfall tracking** compared against district benchmarks.
3.  **Bed occupancy** and availability logs.
4.  **Doctor/staff attendance audits**.
5.  **Diagnostic test availability audits** checked against Indian Public Health Standards (IPHS) requirements.
6.  **AI-driven demand forecasting** (predicting exact days-of-supply remaining).
7.  **Smart resource redistribution recommendations** to transfer stock seamlessly from surplus clinics to deficit ones.
8.  **Automated administrative flagging & intervention workflows** to notify district managers of failing facilities.

---

## 🚀 The Medico Solution

Medico solves these challenges with an **offline-first, multilingual, AI-powered system** that connects frontline healthcare workers at rural centres with district-level administrators via a live-updating console.

```mermaid
graph TD
    A[Multilingual Field App <br>Flutter / SQLite] -- Sync / Offline-First --> B(FastAPI Backend)
    C[Real-time Logs & Audits] --> B
    B --> D[(PostgreSQL)]
    B -- Live Event Pub/Sub --> E[Redis]
    E -- Websockets / Instantly --> F[Next.js District Dashboard]
    G[AI Risk & Forecasting Engine] -- Runs Scheduled/Inline --> B
    G -- Auto Flags/Redistributions --> F
```

### 🌟 Key Features & Core Innovation

#### 1. 📲 Multilingual Offline-First Field App (Flutter)
*   **Frontline Native App**: Built for medical officers and staff to log stock levels, occupied beds, footfall, and doctor presence.
*   **Local-First Architecture**: Implemented with SQLite (`sqflite`) storage so health workers can work fully offline inside remote villages. Data automatically synchronizes the moment internet connectivity returns.
*   **Multilingual Support**: Completely localized into **English**, **Hindi (हिन्दी)**, and **Telugu (తెలుగు)** to bridge language barriers.
*   **Smart Voice Reporting (Whisper STT + LLM)**: Frontline workers can tap a mic icon, speak naturally (e.g., *"We used 5 units of paracetamol and admitted 3 patients"*), and the app extracts structured updates automatically.

#### 2. 🧠 AI Operations Control Room & Risk Auditor (FastAPI + NumPy)
*   **Multi-Dimensional Facility Risk Scoring**: Automatically evaluates and flags centres based on IPHS tier compliance:
    *   **Stock-out Rate**: Flags if >20% of inventory catalogue is at zero stock.
    *   **Bed Volatility**: Detects reporting anomalies (standard deviation > 0.30) to catch fraudulent or missed admissions logs.
    *   **Doctor Attendance**: Sounds critical alarms if average doctor presence drops below 80%.
    *   **Footfall Deviances**: Flags under-utilised or inaccessible facilities (footfall < 50% of the district's median).
    *   **IPHS Diagnostic Test Gap**: Compares current test capabilities against mandated tests for PHCs/CHCs. Flags if the clinic lacks >30% of its required diagnostic suite.

#### 3. 🔮 Predictive Stock-Out Forecasting
*   **Linear Consumption Projections**: Analyzes the rate of medicine dispensing over the last 20 transaction history frames.
*   **Time-to-Exhaustion Forecasting**: Calculates the exact remaining days-of-supply.
*   **Proactive Warnings**: Automatically generates warnings (under 7 days of remaining stock) and critical alerts (under 3 days remaining) if stock levels drop below custom reorder thresholds.

#### 4. 🔄 Smart Resource Redistribution Engine (Admins Approve in 1-Click)
*   **Automated Matching Engine**: Instead of requesting new procurement cycles, the AI identifies nearby clinics with excess stock of the needed medicine and recommends optimal cross-transfers.
*   **One-Click Administrative Actions**: District admins see redistribution cards in the Control Room. Clicking **"Approve Transfer"** runs an atomic database transaction that decrements stock at the source, increments at the destination, logs transaction records (`transfer_out` / `transfer_in`), and publishes updates to both facilities' devices.

#### 5. 🔔 Real-time Redis WebSockets & Alert Inbox
*   **Instant Alert Delivery**: Integrated with Redis Pub/Sub. When the AI Engine or an inline stock write triggers a warning, it pushes an event over WebSocket (`ws/district`).
*   **District Notification Bell**: The dashboard updates immediately in real-time, flashing red and incrementing the notification count without requiring any browser page refreshes or polling.

---

## 🛠️ Monorepo Structure

```
medico/
├── backend/          FastAPI · SQLAlchemy (async) · Alembic · Redis · AsyncPG
├── dashboard/        Next.js 14 (App Router) · TypeScript · Tailwind CSS
├── field-app/        Flutter · sqflite (offline-first) · l10n (EN/HI/TE)
├── data-pipeline/    Python package for fixture generation & metrics loading
│   ├── research/     Raw facility json templates
│   └── scripts/      loader.py · generator.py · seed_test_data.py
├── docker-compose.yml
└── .env.example
```

---

## ⚡ Quick Start

### 1. Environment Configuration
Copy the root template and populate required keys:
```bash
cp .env.example .env
# Fill in DATABASE_URL, REDIS_URL, SECRET_KEY, POSTGRES_PASSWORD
```

### 2. Launch Infrastructure (Docker)
Start Postgres, Redis, and the FastAPI backend service:
```bash
docker compose up --build
# FastAPI Swagger Docs → http://localhost:8000/docs
# Backend Health Check → http://localhost:8000/health
```

### 3. Database Migrations
Run Alembic migrations to build tables (including the new `facility_alerts` system):
```bash
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/medico alembic upgrade head
```

### 4. Data Pipeline & AI Simulation
To populate the dashboard with meaningful data, ingest sample health facilities and seed the metrics simulator:
```bash
cd data-pipeline
# 1. Install local pipeline package
pip install -e .

# 2. Generate schema-compliant mock facility fixtures
medico-generate --count 10 --out research/facilities_sample.json

# 3. Load facilities and structural metadata into Postgres
medico-load --file research/facilities_sample.json

# 4. Seed historical operational logs (stock transactions, bed snapshots, attendance, test availability)
python scripts/seed_test_data.py

# 5. Run daily simulator to generate footfall logs and triggers
medico-generate-logs
```

### 5. Launch Next.js Dashboard
```bash
cd dashboard
cp .env.local.example .env.local
# Set NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
# Open dashboard → http://localhost:3000
# AI Control Room  → http://localhost:3000/ai-ops
```

### 6. Run Flutter Field App
```bash
cd field-app
flutter pub get
flutter run
```

---

## 📊 Services Configuration

| Service | Port | Image | Role |
| :--- | :--- | :--- | :--- |
| **PostgreSQL** | `5432` / `5433` | `postgres:16-alpine` | Primary transactional relational store |
| **Redis** | `6379` | `redis:7-alpine` | Event broadcasting cache & WebSocket pub/sub |
| **FastAPI Backend** | `8000` | (FastAPI Local) | REST API, background worker, & AI evaluation scheduler |
| **Next.js Dashboard** | `3000` | (Next.js Local) | Real-time district administrative monitoring console |

---

## ⚡ AI Threshold Constants

The AI evaluation engine checks facility health every **6 hours** (and instantly on-demand) against the following strict parameters:

*   **Stockout Alarm**: Triggered if `zero_stock_items / total_items > 20%`.
*   **Bed Volatility Warning**: Triggered if bed occupancy rates show high variance (`std_dev > 0.30`).
*   **Doctor Attendance Alarm**: Critical alert if attendance logs record `< 80%` presence for medical officers.
*   **Diagnostic Gap Warning**: Triggered if required tests missing from availability checklist is `> 30%`.
*   **Footfall Alarm**: Warning raised if average clinic footfall is `< 50%` of the active district median.

---

### 🏆 Hackathon Highlights
*   **Production-Ready Async PG**: The backend is built completely async utilizing `SQLAlchemy 2.0` and `asyncpg` to handle high concurrent logging requests.
*   **Real Stock Redistributions**: This isn't just a mock system. When an administrator clicks **Approve**, the inventory numbers update dynamically, generating transaction audits that are sent directly back to the mobile field app.
*   **Multilingual Voice Extraction**: Enables frontline community health workers of any linguistic background to report status without typing, digitizing rural healthcare seamlessly.
