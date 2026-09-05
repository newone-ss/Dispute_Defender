# 🛡️ Razorpay Dispute Defender (AI Risk Manager)

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19.0-61DAFB?style=flat-square&logo=react&logoColor=black)](https://react.dev)
[![Vite 6](https://img.shields.io/badge/Vite-6.1-646CFF?style=flat-square&logo=vite&logoColor=white)](https://vite.dev)
[![Tailwind CSS v4](https://img.shields.io/badge/Tailwind_CSS-v4.0-06B6D4?style=flat-square&logo=tailwindcss&logoColor=white)](https://tailwindcss.com)
[![SQLite WAL](https://img.shields.io/badge/Database-SQLite_WAL-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org)
[![ChromaDB](https://img.shields.io/badge/Vector_Store-ChromaDB-FF6600?style=flat-square)](https://trychroma.com)

> **Razorpay AI Buildathon — Track 2: AI Risk Manager**  
> An automated, deterministic chargeback defense platform for high-velocity merchants. Combines courier physical telemetry (doorstep OTP, GPS geofence, hub-to-doorstep weight delta), automated Jinja2 NPCI UDIR evidence compilation, restricted OCR manifest extraction, and zero-liability Consumer Fairness Gates.

---

## 🛠️ Technology Stack

### Backend Architecture
| Component | Technology | Description |
| :--- | :--- | :--- |
| **API Framework** | **FastAPI (ASGI)** | High-concurrency async REST API & WebSockets with sub-25ms webhook ingestion |
| **Data Validation** | **Pydantic v2 & Settings** | Strict typed validation, environment configurations, and schema serialization |
| **ORM & Persistence** | **SQLAlchemy 2.0 + SQLite (WAL)** | Fully typed asynchronous mapped models with SQLite Write-Ahead Logging for high write throughput |
| **Template Engine** | **Jinja2** | Byte-stable, deterministic compilation of NPCI UDIR representment evidence packets with SHA-256 digests |
| **Vector Engine** | **ChromaDB** | Vector similarity search for omnichannel customer support tickets (Zendesk) and regulatory rulebooks |
| **AI / Document OCR** | **Google Gemini 2.5 Flash** | Isolated manifest extraction for unstructured delivery waybills (with deterministic regex fallback) |
| **Testing Harness** | **Pytest & Pytest-Asyncio** | Comprehensive test suite covering scoring engine, compiler snapshot, webhook HMAC, and queue recovery |

### Frontend Architecture
| Component | Technology | Description |
| :--- | :--- | :--- |
| **Core UI Library** | **React 19** | Modern reactive component architecture with optimized reconciliation and hooks |
| **Build Tool & Bundler** | **Vite 6** | Ultra-fast Hot Module Replacement (HMR), tree-shaking, and optimized production bundling |
| **Styling & Design** | **Tailwind CSS v4** | Clean, responsive modern enterprise design system with refined typography and micro-interactions |
| **State & Data Sync** | **TanStack React Query v5** | Declarative caching, background polling, automatic re-fetching, and optimistic UI updates |
| **Routing** | **React Router v7** | Declarative client-side routing with nested layouts and active navigation states |
| **Data Visualization** | **Recharts & Native SVG** | Interactive analytics, financial KPI metrics, and dispute distribution charts |
| **Iconography** | **Lucide React** | Cohesive, accessible stroke-based icon library |

### Compliance & Payment Protocols
| Standard | Specification | Description |
| :--- | :--- | :--- |
| **NPCI UDIR** | Unified Dispute and Issue Resolution | Standardized evidence packet formatting for UPI dispute representment |
| **Visa CE 3.0** | Compelling Evidence 3.0 | Regulatory evidence matching customer purchase history and physical delivery |
| **Razorpay API v1** | Disputes & Documents API | Direct integration for evidence upload (`/v1/documents`) and dispute submission (`/v1/disputes/{id}/contest`) |
| **Webhook Security** | HMAC-SHA256 | Cryptographic signature validation with timing-attack safe comparisons |

---

## 🚀 Key Highlights & Architectural Mandates

1. **Deterministic Courier Telemetry Over Sentiment:**
   - Evaluates physical delivery signals: **Doorstep OTP verification** (35 pts), **GPS Geofence proximity** within 5km radius (30 pts), **Origin-to-doorstep weight delta** within 5% (20 pts), **Proof of Delivery signature** (10 pts), and **Device fingerprint** (5 pts).
   - Score > 80: `AUTO_CONTESTED` | Score 40–80: `NEEDS_REVIEW` | Score < 40: `AUTO_ACCEPTED`.

2. **Consumer Fairness Gate & Zero-Liability Risk Release:**
   - If an open customer defect support ticket exists OR transit weight loss > 100g, the system immediately triggers `DECISION: AUTO_ACCEPT`.
   - Calls Razorpay's Accept API (`POST /v1/disputes/{id}/accept`) to release liability and avoid the **₹1,500 bank penalty fee** charged on lost chargeback contests.

3. **Deterministic NPCI UDIR & Visa Representment Assembly:**
   - Bank representment documents are generated via Jinja2 (`backend/data/templates/npci_udir_packet.md.j2`), adhering strictly to NPCI Unified Dispute and Issue Resolution (UDIR) compliance without LLM hallucinations.
   - Uploads evidence to Razorpay Documents API (`POST /v1/documents`, purpose `dispute_evidence`) and contests via `PATCH /v1/disputes/{id}/contest` with `action: "submit"`.

4. **Restricted LLM Scope:**
   - LLMs and Vision models are strictly isolated to `core/ocr_extractor.py` for parsing messy, unstructured scanned delivery manifests into typed Pydantic models. Includes deterministic fallback regex parser for offline/test resilience.

5. **Non-blocking Webhook Ingestion & Durable Queue:**
   - `POST /api/v1/webhook` (and `/webhook`) validates HMAC-SHA256 signatures, deduplicates idempotency keys, and commits an atomic `AuditJob` in < 25ms. A standalone queue worker daemon processes jobs asynchronously with atomic SQLite leases.

---

## 🖥️ Platform Interfaces

### 1. Executive Risk Dashboard (`/`)
- Real-time financial metrics: Revenue defended (₹), win rate (%), and dispute volume.
- Interactive decision distribution and telemetry health breakdown.
- Live feed of recent disputes with immediate audit actions.

### 2. Disputes Ledger (`/disputes`)
- Comprehensive tabular dispute audit trail with search, status filters (`AUTO_CONTESTED`, `NEEDS_REVIEW`, `AUTO_ACCEPTED`), and telemetry pills.
- **Deep Audit Dossier**: 8-tab inspection modal containing:
  - **Telemetry**: Physical courier signals (OTP, Geofence, Scale weight, POD).
  - **Evidence**: Ground-truth logs and tracking events.
  - **OCR Manifest**: Scanned waybill parsing results with confidence scoring.
  - **Customer RAG**: Vector search matches against Zendesk support tickets.
  - **NPCI UDIR Packet**: Rendered representment document preview with SHA-256 digest.
  - **Operator Override**: Human-in-the-loop manual decisioning with audit logging.
  - **Raw JSON**: Complete payload inspection for developer review.

### 3. Interactive Scenario Simulator (`/simulator`)
- Interactive testbench to dispatch simulated chargeback webhooks across 5 real-world scenarios:
  1. *Clean Winnable Chargeback* (Valid OTP, 42m geofence, matching weight).
  2. *Pre-Dispute Support Ticket* (Zendesk ticket detected via ChromaDB RAG → Fairness Gate).
  3. *Transit Weight Loss (> 100g)* (Weight delta -280g → Fairness Gate Auto-Accept).
  4. *Open Box Delivery (OBD) Verified* (Doorstep physical verification).
  5. *Failed OTP & Rogue Geofence* (1,840m distance, unverified OTP → Auto-Accept).
- Real-time CI/CD event pipeline visualizer showing step-by-step scoring, gate evaluation, and packet compilation.

---

## 🏗️ Monorepo Structure


<img width="432" height="552" alt="image" src="https://github.com/user-attachments/assets/5ec4cecb-709c-4849-91d2-3e89196f3767" />


---

## ⚡ Quick Start & Verification

### 1. Prerequisites
- **Python 3.11+**
- **Node.js 18+ & npm**

### 2. Backend Setup & Run

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Seed SQLite database with test cases and vector embeddings
python -m app.data.seed_database

# Run evaluation benchmark
python -m evaluate.run_benchmark

# Run the automated test suite (18 tests)
python -m pytest tests -v

# Start FastAPI server (Runs on port 8000)
python -m app.main
# or: uvicorn main:app --reload --port 8000

# In a separate terminal, launch the durable audit queue worker daemon:
python -m app.workers.audit_worker
```

### 3. Frontend Setup & Run

```bash
cd frontend

# Install dependencies
npm install

# Start Vite development server (Runs on port 3000)
npm run dev

# Open in your browser:
# http://localhost:3000
```

---

## 🛡️ Telemetry Scoring Rubric

| Signal | Max Weight | Logic / Condition |
| :--- | :--- | :--- |
| **Delivery OTP Verified** | **35 pts** | Binary match — verified single-use OTP entered at doorstep |
| **GPS Geofence Match** | **30 pts** | Full points if ≤ 5.0km; linear falloff between 5.0km and 15.0km |
| **Weight Delta OK** | **20 pts** | Full points if shipped vs delivered weight delta ≤ 5%; partial if ≤ 15% |
| **Delivery Signature / POD** | **10 pts** | Physical signature or electronic proof of delivery recorded |
| **Device Fingerprint** | **5 pts** | Checkout session device fingerprint matches historical customer record |
| **Consumer Fairness Gate** | **OVERRIDE** | Open support defect ticket or >100g weight loss → `AUTO_ACCEPT` |

---

## 📊 Evaluation & Financial ROI Benchmark

Run `python -m evaluate.run_benchmark` to evaluate the 50 ground-truth scenarios:

| Metric | Result | Impact |
| :--- | :--- | :--- |
| **Overall Classification Accuracy** | **100.0%** | Conclusive evidence vs weak cases |
| **Consumer Fairness Gate Accuracy** | **100.0%** | Zero false contests on legit defects/losses |
| **Direct Revenue Recovered (85% win rate)** | **₹360,687.54** | Defended through NPCI UDIR evidence packets |
| **Bank Penalties Avoided (₹1,500/case)** | **₹27,000.00** | Upfront auto-acceptance on genuine merchant defect cases |
| **Net Financial Value Protected** | **₹406,826.22** | **67.1% Net ROI Boost** |

---

## 🔒 Security & Governance

- **Deterministic Defense**: No LLM decision-making in the financial judgment loop; pure mathematical scoring and rule-based governance.
- **HMAC Signature Verification**: All incoming webhooks are validated with timing-safe SHA-256 signature verification.
- **Audit Logging**: Every operator override, scoring step, and evidence generation creates an immutable audit trail.
- **PII Protection**: Customer phone numbers and addresses are masked in logs and client dossiers.
