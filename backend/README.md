# 🛡️ Razorpay Dispute Defender — Backend

> Automated, deterministic risk manager and chargeback defense pipeline powered by courier physical telemetry (doorstep OTP, meter-precision GPS geofencing, weight delta reconciliation), declarative policy scoring, Jinja2 NPCI UDIR evidence compilation, and zero-liability Consumer Fairness Gates.

---

## 🏛️ Architecture Overview

```
                        ┌────────────────────────────────────────────────────────┐
                        │             Razorpay Webhook Ingestion                 │
                        │           POST /api/webhook (Sub-25ms)                 │
                        └───────────────────────┬────────────────────────────────┘
                                                │
                                    HMAC-SHA256 Verification
                                    Idempotency Key Dedup
                                                │
                                                ▼ Atomic Commit
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              DURABLE SQLITE QUEUE & STORAGE                            │
│                                                                                        │
│   Disputes Table (Status: RECEIVED)  ◄───►  AuditJobs Table (Status: PENDING)          │
└───────────────────────────────────────┬────────────────────────────────────────────────┘
                                        │
                                        │ Polled with Atomic Lease (300s)
                                        ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                       STANDALONE AUDIT WORKER DAEMON                                   │
│                       `python -m app.workers.audit_worker`                             │
│                                                                                        │
│   1. Manifest OCR Extractor   ◄─── Gemini 1.5 Flash / Regex Fallback                   │
│   2. ChromaDB RAG Engine      ◄─── Ingests WhatsApp/Email/Zendesk Transcripts          │
│   3. Pure Scoring Engine      ◄─── Reads `app/policy/scoring_policy.yaml` (0-100 pts)  │
│   4. Consumer Fairness Gate   ◄─── Transit Weight Loss > 100g OR Open Support Ticket   │
│   5. Reason-Code Router       ◄─── Open Box Delivery (OBD) Doorstep Inspection Proof   │
│   6. Jinja2 Evidence Compiler ◄─── Zero-Hallucination NPCI UDIR Legal Markdown         │
│   7. Razorpay Client (Mock)   ◄─── POST /v1/documents & PATCH /v1/disputes/contest     │
│   8. Audit Trail Logger       ◄─── Records state transition & SHA-256 evidence digest  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quick Start & Run Commands

### 1. Requirements & Installation
Python 3.10+ is required.

```bash
cd backend
pip install -r requirements.txt
# or install package in editable mode:
pip install -e .
```

### 2. Seed Database & Knowledge Base
Initialize SQLite tables and index Visa CE 3.0 / NPCI UDIR rulebooks and synthetic customer chat transcripts into ChromaDB:

```bash
python -m app.data.seed_database
```

### 3. Start FastAPI Webhook & Dashboard Server
Runs on port 8000:

```bash
python -m app.main
# or:
uvicorn app.main:app --reload --port 8000
```

### 4. Start the Standalone Durable Queue Worker
In a separate terminal, launch the audit queue worker daemon:

```bash
python -m app.workers.audit_worker
```

Or process a single queued batch and exit:
```bash
python -m app.workers.audit_worker --once
```

### 5. Run the Automated Test Suite
Run the full 18-test pytest suite:

```bash
python -m pytest tests -v
```

Run code formatting and linting checks:
```bash
python -m ruff check app tests
python -m ruff format --check app tests
```

---

## ⚙️ Environment Variables Reference

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `APP_ENV` | `development` | Environment mode (`development`, `staging`, `production`). In production, missing secrets trigger fail-fast startup exits. |
| `LOG_LEVEL` | `INFO` | Structured JSON log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `DATABASE_URL` | `sqlite:///./data/mock_db/disputes.db` | SQLAlchemy 2.0 database URL. Enforces WAL mode and foreign keys on SQLite. |
| `SCORING_POLICY_PATH` | `./app/policy/scoring_policy.yaml` | Path to declarative YAML scoring thresholds and policy version. |
| `CHROMADB_PATH` | `./data/mock_db/chroma_db` | Filesystem storage path for ChromaDB vector embeddings. |
| `RAZORPAY_KEY_ID` | `rzp_test_51ZDefenderMock` | Razorpay API key identifier. |
| `RAZORPAY_KEY_SECRET` | `secret_test_mockkey998877` | Razorpay API key secret. |
| `RAZORPAY_WEBHOOK_SECRET` | `whsec_mockdisputeshield123` | Secret used to verify HMAC-SHA256 on `X-Razorpay-Signature`. |
| `RAZORPAY_MOCK_MODE` | `true` | Safety toggle. When `true`, all Razorpay API calls return deterministic mocks and do not debit funds. |
| `ADMIN_OVERRIDE_TOKEN` | `admin_secret_token_override_99` | Static token required in `X-Admin-Token` header for `/override` endpoints. |
| `GEMINI_API_KEY` | `""` | Optional Google Gemini key for AI OCR manifest parsing. Regex fallback used when absent. |
| `AUDIT_WORKER_POLL_INTERVAL_SECONDS` | `2.0` | Polling interval for the audit queue worker daemon. |
| `AUDIT_JOB_LEASE_SECONDS` | `300` | Lease duration before an abandoned/crashed job is reclaimed. |

---

## 📊 Scoring Policy & Decision Engine

Scoring weights and cutoffs are defined declaratively in [`app/policy/scoring_policy.yaml`](file:///c:/Users/piyus/OneDrive/Desktop/project/razorpay/backend/app/policy/scoring_policy.yaml):

| Signal | Weight | Logic |
| :--- | :---: | :--- |
| **Doorstep OTP Verified** | **35 pts** | Binary match — verified single-use OTP entered at doorstep with delivery agent |
| **GPS Geofence Proximity** | **30 pts** | **Full 30 pts** if $\le 100\text{m}$; **24 pts (80%)** if $\le 500\text{m}$; linear falloff up to $2,000\text{m}$; $0\text{ pts}$ beyond |
| **Weight Delta OK** | **20 pts** | **Full 20 pts** if origin vs doorstep scale delta $\le 5\%$; scaled between $5\%\text{--}15\%$ |
| **Proof of Delivery (POD)** | **10 pts** | Physical signature or electronic proof of delivery recorded on manifest |
| **Device Fingerprint** | **5 pts** | Checkout session device fingerprint matches historical customer record |

### Action Thresholds
- **Score $\ge 80$**: `AUTO_CONTESTED` (NPCI UDIR evidence packet compiled and submitted)
- **Score $40\text{--}79$**: `NEEDS_REVIEW` (Flagged for human operator review)
- **Score $< 40$**: `AUTO_ACCEPTED` (Liability released to avoid bank loss penalty)

---

## ⚖️ Consumer Fairness Gate

Contesting chargebacks when the merchant is genuinely at fault wastes resources and guarantees an additional **₹1,500 bank penalty fee** charged on lost contests.

The Consumer Fairness Gate immediately triggers `AUTO_ACCEPT` if:
1. **Open CRM Defect Ticket**: Customer notified customer support of a defect/damage prior to initiating a chargeback.
2. **Transit Weight Loss $> 100\text{g}$**: Packaging scale weight differential indicates missing contents or empty box.
3. **Omnichannel Chat Complaint**: Customer communication history in WhatsApp/Email/Zendesk confirms a prior unaddressed complaint.

---

## 📜 Why Jinja2 Over LLMs for Legal Representment

Bank representment packets submitted to NPCI and card networks must meet strict regulatory standards:
- **Zero Hallucination Guarantee**: LLMs generating legal text risk inventing fictitious tracking IDs, wrong timestamps, or false weight metrics.
- **Auditable & Byte-Stable**: Every packet is compiled from [`app/templates/npci_udir_packet.md.j2`](file:///c:/Users/piyus/OneDrive/Desktop/project/razorpay/backend/app/templates/npci_udir_packet.md.j2) using verified telemetry models. A SHA-256 checksum is computed and logged upon generation for irrefutable proof of byte-equality.

---

## 🚀 Production Hardening Roadmap

1. **Distributed Queue**: Migrate `app/core/queue.py` from SQLite table leases to **AWS SQS** or **Celery with Redis**. The downstream `process_dispute` pipeline remains unchanged.
2. **PostgreSQL Migration**: Swap `sqlite:///` for PostgreSQL with connection pooling (`pgbouncer`).
3. **Admin Token Rotation**: Replace static `ADMIN_OVERRIDE_TOKEN` with OAuth2 / JWT integration with merchant IAM.
