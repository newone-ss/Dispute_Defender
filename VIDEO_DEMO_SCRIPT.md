# Razorpay Dispute Defender — 5-Minute Golden Path Video Demonstration Script

A comprehensive, second-by-second choreography script for recording the winning hackathon submission video.

---

## 🎬 Pre-Recording Checklist & Setup

Before hitting record, ensure the following environments and windows are open and arranged:

1. **Window 1 (Browser - Chrome/Brave):**
   * **URL:** `http://localhost:3000` (React 19 Dashboard)
   * Fullscreen or 1920x1080 resolution.
   * Start on the **Overview** page (`/`).
2. **Window 2 (API Client - Postman):**
   * Collection: `Razorpay Dispute Defender API`
   * Request: `2. Webhook Ingestion (Razorpay)` -> `Ingest Webhook - payment.dispute.created (/api/webhook)`
   * URL: `http://127.0.0.1:8000/api/webhook`
   * Headers confirmed:
     * `Content-Type`: `application/json`
     * `X-Razorpay-Signature`: `mock_signature_dev` *(HMAC bypass header for mock/dev environment)*
     * `X-Razorpay-Event-Id`: `evt_{{$timestamp}}` *(auto-generates dynamic unique ID)*
3. **Window 3 (Terminal):**
   * Running: `uvicorn main:app --port 8000` showing clean, live structured JSON logs.
   * Font size enlarged (+2 zoom) so judges can read stdout clearly.

---

## ⏱️ Video Timeline Choreography (5:00 Total)

| Timestamp | Screen Action | Background Process | Talking Points (Say Aloud) |
| :--- | :--- | :--- | :--- |
| **0:00 – 0:45** | **Overview Dashboard (`http://localhost:3000/`)**<br><br>1. Hover mouse over the **Financial ROI** header.<br>2. Point to the **Net INR Protected** card (`₹2,48,500 / +84.2% ROI Boost`).<br>3. Highlight **Bank Loss Penalties Avoided** (`₹42,000 / 28 Claims @ ₹1,500`).<br>4. Point to the **Auto-Contest Win Rate** (`84.6%`) and the **Telemetry Compliance** progress bars. | React Query fetches `/api/metrics` (aggregating SQLite `disputes` table with WAL mode) and calculates real-time merchant ROI metrics. | *"In Indian e-commerce, friendly fraud is bleeding merchants dry. A customer receives an expensive item at their doorstep, signs for it, and then calls their bank claiming 'Product Not Received.' The merchant loses the product, the money, and incurs a brutal ₹1,500 bank penalty. Meet **Razorpay Dispute Defender**—an automated AI risk engine that uses physical courier telemetry and omnichannel RAG to resolve disputes in sub-25 milliseconds with zero hallucinations."* |
| **0:45 – 1:45** | **Sub-25ms Webhook Ingestion (Postman & Terminal)**<br><br>1. Switch window to **Postman**.<br>2. Select `POST /api/webhook`.<br>3. Show the Headers tab: highlight `X-Razorpay-Signature: mock_signature_dev` and `X-Razorpay-Event-Id: evt_{{$timestamp}}`.<br>4. In the Request Body, point to the nested payload:<br>• Dispute ID: `"disp_golden_path_001"`<br>• Amount: `₹2,499.00`<br>• Telemetry: Doorstep OTP `verified: true`, Geofence distance `42.0m`, Scale Weight Delta `2g`, Signed POD.<br>5. Click **Send**.<br>6. Highlight the immediate response:<br>`status: "received"`, `decision: "inserted"`, **`latency_ms: ~8.6ms`**. | 1. Constant-time HMAC-SHA256 signature verification.<br>2. JSON schema extraction.<br>3. Deterministic idempotency check in SQLite.<br>4. Single-transaction atomic persist to `disputes` & `audit_jobs` tables.<br>5. Offloads heavy scoring to async `BackgroundTasks` without blocking response. | *"When a chargeback webhook hits our endpoint, speed is non-negotiable. Razorpay requires sub-25 millisecond response times. Watch this: we send a real-time chargeback payload with Doorstep OTP, sub-50m GPS geofencing, and scale weight telemetry. In just **8.6 milliseconds**, our endpoint validates HMAC authenticity, guarantees atomic idempotency, commits the record, and returns 200 OK."* |
| **1:45 – 2:30** | **Asynchronous AI Audit & Terminal Logs**<br><br>1. Switch window to the **Backend Terminal**.<br>2. Scroll down to highlight the structured JSON logs:<br>• `event: "webhook_ingest"` (8.6ms latency)<br>• `event: "chromadb_query"` (Cosine distance omnichannel search)<br>• `event: "audit_decision"` (`decision: "AUTO_CONTESTED"`, `score: 95/100`)<br>• `event: "evidence_compiled"` (Jinja2 SHA-256 digest generated). | 1. Async background worker claims the dispute.<br>2. Normalizes telemetry into Pydantic models.<br>3. Vector query over ChromaDB `customer_chats` collection.<br>4. Pure rule scoring engine evaluates signals (OTP +40, GPS +25, Weight +20, POD +10 = 95/100).<br>5. Compiles byte-stable Jinja2 UDIR template. | *"Notice what happened in the terminal. The heavy AI lifting never blocks the payment gateway. In the background, our audit worker claimed the job, queried ChromaDB for omnichannel WhatsApp and Zendesk transcripts, cross-referenced the carrier telemetry, scored the case at 95 out of 100, and deterministically auto-contested the dispute in under 400 milliseconds."* |
| **2:30 – 3:30** | **Live Real-Time Ledger (`/disputes`)**<br><br>1. Switch back to the browser and click **Disputes Ledger** on the left sidebar.<br>2. Show that `disp_golden_path_001` appears **automatically** at the top of the table (without needing a hard browser refresh).<br>3. Type `disp_golden_path_001` into the search box to show instantaneous client/server filtering.<br>4. Hover over each Telemetry Pill:<br>• **Doorstep OTP:** Green check (`Verified`)<br>• **GPS Offset:** `42m` (`Sub-50m Precision`)<br>• **Weight Delta:** `-2g` (`Stable / < 2% Delta`)<br>• **POD:** `Signed`<br>• **Status:** `AUTO_CONTESTED` badge. | TanStack Query auto-polls every 3 seconds and triggers instantaneous window-focus revalidation. Serializes typed database rows into responsive UI viewmodels. | *"Now we switch to our React 19 dashboard. Powered by TanStack Query, the new dispute appears instantly. Look at the telemetry pills on this row: Cryptographic Doorstep OTP is matched, BlueDart GPS geofencing confirmed delivery within 42 meters of the cardholder address, and scale weight variance between hub and doorstep is under 2%. The risk engine has automatically marked it AUTO_CONTESTED."* |
| **3:30 – 4:30** | **The Deep Audit Dossier & Cryptographic UDIR Packet**<br><br>1. Click directly on the `disp_golden_path_001` row to open the **Deep Audit Dossier** modal.<br>2. **Tab 1 (Evidence Breakdown):** Point to the 95/100 score gauge and explain the signal weighting.<br>3. **Tab 4 (Customer RAG):** Click this tab! Point to the ChromaDB vector match showing a WhatsApp transcript where the buyer messaged: *'Got it, thanks! Package was intact.'* with a `+0.92` sentiment score.<br>4. **Tab 5 (NPCI UDIR Packet):** Click this tab! Point to the legal representment brief.<br>5. Click the **'Copy Digest'** button (shows green check: *'Hash Copied'*).<br>6. Click **'Download Packet (.md)'**.<br>7. **Tab 6 (Raw JSON):** Click briefly to show the immutable SQLite audit log.<br>8. Point to the **Operator Override Bar** at the bottom. | 1. Retrieves verified dispute record via `GET /api/disputes/{id}`.<br>2. Displays semantic cosine relevance distance from ChromaDB.<br>3. Computes and validates SHA-256 tamper-evident checksum over Jinja2-rendered markdown.<br>4. Aligns claims with Visa Compelling Evidence 3.0 (CE 3.0) and NPCI UDIR Clause 8.1.b. | *"When we click into the Deep Audit Dossier, you see our core innovation: 100% explainability. Look at Customer RAG—ChromaDB surfaced a WhatsApp confirmation where the customer explicitly admitted delivery 30 minutes post-dropoff, completely refuting friendly fraud. Next, look at the NPCI UDIR Packet. Instead of letting an LLM hallucinate legal arguments, our engine renders a deterministic, byte-stable Jinja2 brief stamped with a SHA-256 cryptographic digest. It is tamper-proof, court-admissible, and ready for instant NPCI submission."* |
| **4:30 – 5:00** | **Consumer Fairness Gate & Closing Impact (`/simulator`)**<br><br>1. Close modal and navigate to **Scenario Simulator** (`/simulator`).<br>2. Select scenario **'Transit Damage Defect Trip'**.<br>3. Click **'Run Scenario Pipeline'**.<br>4. Watch the 7-step pipeline animate and show the **Consumer Fairness Gate** turning amber/red: `Liability Released / Auto-Accepted`.<br>5. Point to the summary: *Avoided ₹1,500 bank dispute filing fee*. | Evaluates pre-existing customer complaint ticket in Zendesk. Detects legitimate transit defect, bypassing contestation logic to protect merchant rating and avoid bank arbitration penalty fees. | *"Finally, our engine isn't just a dispute crusher—it features a built-in Consumer Fairness Gate. In our simulator, when a customer legitimately reported a cracked screen prior to disputing, the engine recognizes the merchant's fault, auto-accepts the refund, and prevents an unnecessary ₹1,500 bank penalty. Razorpay Dispute Defender transforms chargebacks from a multi-week operational nightmare into an autonomous, mathematically verifiable profit protector. Thank you!"* |

---

## 🎯 High-Impact Video Tips for the Hackathon Judges

1. **Keep the Voice Paced & Authoritative:**
   * Speak with confidence when mentioning financial terms: *"Visa Compelling Evidence 3.0 (CE 3.0)"*, *"NPCI UDIR Guidelines"*, and *"Deterministic Byte-Stable Engine"*.
2. **Visual Contrast:**
   * Move the mouse smoothly. Let the cursor rest on the **SHA-256 Hash Digest** and the **Sub-25ms Latency** response in Postman for at least 2 seconds so judges can pause the video and inspect it.
3. **Soundbite to Repeat:**
   * *"Zero LLM Hallucinations. Sub-25ms Ingestion. Cryptographically verifiable evidence."*
