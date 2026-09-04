# Changelog

All notable changes to the Razorpay Dispute Defender scoring policies, models, and architecture are documented here.

## [2026.1.0] - 2026-09-04

### Added
- **Declarative Scoring Policy**: Centralized all scoring weights, geofence radii, and weight thresholds into `app/policy/scoring_policy.yaml`.
- **Durable SQLite Queue**: Implemented `audit_jobs` table with atomic lease claiming (`BEGIN IMMEDIATE`) and crash recovery, replacing transient `BackgroundTasks`.
- **Sub-25ms Webhook Ingestion**: Added mandatory HMAC-SHA256 signature verification (`hmac.compare_digest`), database-level idempotency via `idempotency_key`, and atomic `AuditJob` creation.
- **Pure Scoring Engine**: Decoupled `score()` and `fairness_gate()` into pure functions without I/O or globals.
- **Reason Code Registry**: Standardized `ReasonCodeRegistry` in `app/policy/reason_codes.py` mapping NPCI UDIR and Visa CE 3.0 standards.
- **Byte-Stable Evidence Compiler**: Generates SHA-256 digests on rendered Jinja2 NPCI UDIR representment packets.
- **Safety Interlock**: Added persistent "MOCK MODE" visual banner in dashboard header.
- **Authenticated Overrides**: Added `X-Admin-Token` authentication for manual dispute overrides with mandatory operator audit notes.
- **Automated Pytest Suite**: Added 18 unit and integration tests covering HMAC signatures, idempotency, pure scoring, fairness gates, and queue crash recovery.
