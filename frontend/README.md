# 🛡️ Dispute Defender — Frontend Dashboard

> Real-time chargeback analytics, courier telemetry audit inspector, and manual dispute resolution dashboard built with **React 19**, **TypeScript**, **Tailwind CSS**, and **Vite**.

---

## 🚀 Overview

The frontend serves as the operations and analytics command center for Razorpay Dispute Defender. It provides risk operators with immediate visibility into automated dispute resolutions, physical courier telemetry integrity, and financial ROI metrics.

### Key Capabilities

- **Financial Analytics**: Displays net disputed exposure, INR revenue successfully recovered (85% win rate), bank penalty fees avoided (₹1,500 per case), and overall pipeline ROI boost.
- **Filterable Dispute Ledger**: Live table filtering by status (`AUTO_CONTESTED`, `NEEDS_REVIEW`, `AUTO_ACCEPTED`, `ACCEPTED`, `LOST`, `WON`).
- **Telemetry Checklist Badges**: Instant visual indicators for doorstep OTP verification, GPS geofence match, packaging weight delta, signature POD, and device fingerprint.
- **Deep Audit Inspection Modal**:
  - Full courier telemetry breakdown with geofence distance (meters) and package weight variance.
  - Manifest OCR extraction trace with confidence scoring.
  - Omnichannel customer chat sentiment and prior defect ticket checks.
  - Live preview of the byte-stable NPCI UDIR / Visa representment evidence packet with computed SHA-256 digest.
- **Interactive Dispute Simulator**: Test synthetic disputes in real time against the backend scoring engine and Consumer Fairness Gate.
- **Authenticated Manual Overrides**: Operators can override dispute verdicts with required audit justifications.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Framework** | React 19 (`react`, `react-dom`) |
| **Language** | TypeScript (Strict mode) |
| **Build & Dev Tool** | Vite |
| **Styling** | Tailwind CSS with custom Razorpay risk color tokens |
| **Routing** | React Router v7 |
| **Icons** | Lucide React |
| **API Layer** | Fetch API client with typed interfaces (`src/lib/api.ts`) |

---

## 📁 Directory Structure

```text
frontend/
├── public/                     # Static assets (favicons, SVG icons)
├── src/
│   ├── components/             # Reusable UI components
│   │   ├── AuditModal.tsx      # Modal for telemetry breakdown, OCR audit, & UDIR packet
│   │   ├── DisputeTable.tsx    # Interactive table with filtering and action buttons
│   │   ├── MetricCards.tsx     # ROI, recovered INR, and penalty metrics cards
│   │   ├── Sidebar.tsx         # Collapsible navigation drawer
│   │   └── TelemetryBadge.tsx  # Color-coded physical telemetry checklist pill
│   ├── pages/
│   │   ├── Dashboard.tsx       # Main analytics page with interactive simulator
│   │   └── Disputes.tsx        # Comprehensive dispute management & review view
│   ├── lib/
│   │   └── api.ts              # Typed backend REST client with fallback mocks
│   ├── App.tsx                 # Root router and layout shell
│   ├── index.css               # Tailwind directives and custom utility classes
│   └── main.tsx                # Application mounting entrypoint
├── index.html                  # HTML entrypoint with viewport & metadata
├── package.json                # Project dependencies and npm scripts
├── tailwind.config.js          # Design system theme extensions
├── tsconfig.json               # TypeScript base configuration
├── tsconfig.app.json           # Application TypeScript compiler options
└── vite.config.ts              # Vite server & API proxy config (port 5173 -> 8000)
```

---

## ⚡ Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Run the Development Server

```bash
npm run dev
```

The application starts at `http://localhost:5173`. API requests to `/api/*` are automatically proxied to the backend at `http://localhost:8000`.

### 3. Production Build & Validation

```bash
npm run build
```

Performs strict TypeScript type-checking (`tsc -b`) and bundles production assets into `dist/`.
