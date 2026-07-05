# 🏥 Project Medico: Gemini Co-Pilot Collaboration Transcript
**Hackathon 2026 Submission Document**

This document logs the development journey, design patterns, and engineering decisions made during the collaboration between the developer and Gemini to build the Medico platform.

---

## 📅 Session 1: Architectural Design & Schema Planning

**Developer**:
We are building a smart district dashboard for primary and community health centres (PHCs/CHCs). The frontline staff logs metrics (beds, stock, attendance, footfall) on their mobile apps, but district admins have zero real-time visibility. I want to build a background AI service to flags facilities at risk. Let's design the database model for alerts and map out the thresholds.

**Gemini**:
To prevent "alert storms" (sending repeated alerts for the same issue), we should design a structured `FacilityAlert` model with fields for:
*   Unique composite checks (`facility_id` + `category`)
*   Severity levels (`info`, `warning`, `critical`)
*   Detail payloads (JSON storage for dynamic metrics like missing tests or days-of-supply)
*   Acknowledgement status (`acknowledged_at`, `acknowledged_by`)

Let's implement this schema in SQLAlchemy and use Alembic to handle migrations dynamically.

---

## 📅 Session 2: Mathematical Risk Evaluation Engine

**Developer**:
The alerts shouldn't just be static thresholds. I want to identify anomalies, such as unstable bed reporting, low doctor attendance, and diagnostic test gaps compared to the Indian Public Health Standards (IPHS).

**Gemini**:
We can achieve this using FastAPI integrated with APScheduler and NumPy:
1.  **Bed Occupancy Volatility**: Instead of checking single days, we can calculate the standard deviation ($\sigma$) of the occupancy rate over time. A $\sigma > 0.30$ indicates reporting spikes or chaotic admissions.
2.  **Footfall Ratios**: We will calculate the median footfall across the entire district and flag any facility operating at $< 50\%$ of that median.
3.  **IPHS Gaps**: We'll define IPHS requirements per tier (e.g., PHC vs. CHC) in the app settings, check active test availability, and flag centres missing $> 30\%$ of required diagnostic services.
4.  **Linear Demand Projection**: We can calculate the consumption rate using a rolling window of recent stock transactions, calculate $Days = Current Qty / Daily Rate$, and trigger critical alerts if stock-out is forecasted within 3 days.

---

## 📅 Session 3: Implementing Live Websockets & Real-Time Sync

**Developer**:
Admins shouldn't have to refresh the dashboard to see alerts. We need live push notifications. Let's set up WebSockets.

**Gemini**:
Let's leverage Redis Pub/Sub:
1.  When the AI scheduler (or an inline stock-level update) commits an alert to PostgreSQL, we'll publish the event payload to a Redis channel called `district` or the specific `facility_id` channel.
2.  We will implement a FastAPI WebSocket endpoint (`/ws/district` and `/ws/facility/{id}`) that listens to the Redis channels and broadcasts JSON frames directly to the client.
3.  On the Next.js front-end, we will build a `NotificationBell` component that connects to this WebSocket on mount, automatically incrementing a badge count and prepending new alerts to the notification center list without polling.

---

## 📅 Session 4: Real stock redistribution & One-Click Actions

**Developer**:
The redistribution suggestions on the dashboard must be actionable. When an admin clicks "Approve Transfer", we should actually execute the transfer in the database.

**Gemini**:
Let's build a secure `POST /ai/transfers/approve` transaction endpoint:
*   It will validate that the source facility has enough stock.
*   It will atomically subtract the stock from the source and add it to the destination's stock level.
*   It will insert two records into the transaction history (`transfer_out` and `transfer_in`) for tracking.
*   It will broadcast the new stock levels over WebSockets to sync all clients immediately.

---

## 📅 Session 5: Debugging Flutter & Cross-Platform Settings

**Developer**:
We are compiling the Flutter field application locally, but the speech-to-text packages are throwing errors on the Linux desktop environment. We also need localized translations.

**Gemini**:
Let's clean that up:
1.  We'll stub out the native speech-to-text plugins inside the Flutter CMake configuration so the project builds successfully on standard Linux desktops for testing, while pointing developers to settings where API keys can be configured.
2.  We'll set up `flutter_localizations` with `.arb` translation templates, supporting English, Hindi, and Telugu, so healthcare workers can easily toggle settings and view the interface in their native language.
