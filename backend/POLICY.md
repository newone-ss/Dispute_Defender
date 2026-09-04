# 🛡️ Dispute Defender — Scoring Policy Governance & Operational Guide

> This document defines the protocol for modifying telemetry weights, geofence perimeters, weight loss tolerances, and action thresholds within `app/policy/scoring_policy.yaml`.

---

## 1. Governance & Sign-off Rules

1. **No Code Modification for Tunables**: 
   - Never hardcode scoring weights, radii, or tolerances inside Python source code. All changes must be made exclusively in [`app/policy/scoring_policy.yaml`](file:///c:/Users/piyus/OneDrive/Desktop/project/razorpay/backend/app/policy/scoring_policy.yaml).
2. **Version Bump Mandate**:
   - Any adjustment to weights, radii, tolerances, or action thresholds requires a semantic policy version bump (e.g. `2026.1.0` -> `2026.1.1`).
   - The version bump must be recorded in [`backend/CHANGELOG.md`](file:///c:/Users/piyus/OneDrive/Desktop/project/razorpay/backend/CHANGELOG.md).
3. **Approval Authority**:
   - Changes to the **Consumer Fairness Gate** (e.g. raising `fairness_weight_loss_g`) require sign-off from the **Risk Policy Lead** and **Head of Merchant Operations** to prevent accidental penalty fee exposure.

---

## 2. Signal Weights & Scoring Rubric

The scoring rubric sums to a maximum of **100 points**:

```yaml
weights:
  otp_verified: 35.0          # Doorstep 2FA verification
  geofence_match: 30.0        # GPS coordinate proximity
  weight_delta_ok: 20.0       # Packaging integrity
  delivery_signature: 10.0    # Carrier manifest proof
  device_fingerprint: 5.0     # Historical transaction identity
```

- **Rule**: The sum of all signal weights in `weights` must strictly equal `100.0`.
- **Unit Test Enforcement**: Modifying these values without updating test fixtures will fail `tests/test_audit_engine.py`.

---

## 3. GPS Geofence Configuration

```yaml
geofence:
  primary_radius_m: 100.0      # Full points (30 pts)
  secondary_radius_m: 500.0    # 80% points (24 pts)
  tertiary_radius_m: 2000.0    # Linear falloff to 0 pts
```

- **Urban Dense Hubs**: Set `primary_radius_m` to `100.0m` (NPCI UDIR recommended residential perimeter).
- **Rural/Suburban Deliveries**: Can increase `secondary_radius_m` to `800.0m` if GPS cell tower triangulation error margins justify it.

---

## 4. Consumer Fairness Gate Thresholds

```yaml
weight:
  clean_tolerance_pct: 5.0      # 0 to 5% delta considered intact
  max_tolerance_pct: 15.0       # Scaled falloff between 5% and 15%
  fairness_weight_loss_g: 100.0 # Absolute weight loss > 100g triggers AUTO_ACCEPT
```

- **Why 100g?**: Weight loss greater than 100 grams is the standard courier logistics indicator of tampering, pilferage, or empty parcel delivery.
- Contesting cases with $> 100\text{g}$ weight loss is classified as merchant bad-faith representment and triggers the **₹1,500 bank penalty fee**.

---

## 5. Deployment & Rollout Checklist

Before deploying an updated `scoring_policy.yaml`:
1. Run `python -m pytest tests -v` to ensure all pure functions pass with the new policy.
2. Run `python -m ruff check app tests` to verify linting.
3. Restart `audit_worker` daemon to flush cached policy values.
4. Verify structured log output confirms new `policy_version` upon startup.
