"""Pure deterministic telemetry scoring engine.

Computes physical courier delivery confidence scores (0-100)
without any I/O, database access, or global state.
"""

from typing import Any, Dict

from app.core.schemas import ScoreBreakdown, TelemetryData


def score(telemetry: TelemetryData, policy: Dict[str, Any]) -> ScoreBreakdown:
    """Compute deterministic courier confidence points based on declarative policy."""
    weights = policy.get("weights", {})
    geofence_cfg = policy.get("geofence", {})
    weight_cfg = policy.get("weight", {})

    # 1. Doorstep OTP Verified (Binary: max 35 pts)
    otp_pts = weights.get("otp_verified", 35.0) if telemetry.otp_verified else 0.0

    # 2. GPS Geofence Proximity (Max 30 pts with meter precision)
    geo_pts = 0.0
    geo_m = telemetry.geofence_distance_m
    if geo_m is None and telemetry.geofence_distance_km is not None:
        geo_m = telemetry.geofence_distance_km * 1000.0

    if geo_m is not None:
        primary_r = geofence_cfg.get("primary_radius_m", 100.0)
        secondary_r = geofence_cfg.get("secondary_radius_m", 500.0)
        tertiary_r = geofence_cfg.get("tertiary_radius_m", 2000.0)
        max_geo = weights.get("geofence_match", 30.0)

        if geo_m <= primary_r:
            geo_pts = max_geo
        elif geo_m <= secondary_r:
            geo_pts = round(max_geo * 0.80, 2)
        elif geo_m <= tertiary_r:
            ratio = 1.0 - ((geo_m - secondary_r) / (tertiary_r - secondary_r))
            geo_pts = round(max_geo * 0.80 * max(0.0, ratio), 2)
        else:
            geo_pts = 0.0

    # 3. Origin-to-Doorstep Weight Reconciliation (Max 20 pts)
    weight_pts = 0.0
    weight_loss_g = 0.0
    shipped = telemetry.shipped_weight_g
    delivered = telemetry.delivered_weight_g

    if shipped is not None and delivered is not None and shipped > 0:
        weight_loss_g = max(0.0, shipped - delivered)
        delta_pct = abs(shipped - delivered) / shipped * 100.0

        clean_tol = weight_cfg.get("clean_tolerance_pct", 5.0)
        max_tol = weight_cfg.get("max_tolerance_pct", 15.0)
        max_wt = weights.get("weight_delta_ok", 20.0)

        if delta_pct <= clean_tol:
            weight_pts = max_wt
        elif delta_pct <= max_tol:
            ratio = 1.0 - ((delta_pct - clean_tol) / (max_tol - clean_tol))
            weight_pts = round(max_wt * max(0.0, ratio), 2)
        else:
            weight_pts = 0.0

    # 4. Proof of Delivery / Signature (Max 10 pts)
    sig_pts = weights.get("delivery_signature", 10.0) if telemetry.delivery_signature else 0.0

    # 5. Checkout Device Fingerprint Consistency (Max 5 pts)
    dev_pts = weights.get("device_fingerprint", 5.0) if telemetry.device_fingerprint_match else 0.0

    total = int(min(round(otp_pts + geo_pts + weight_pts + sig_pts + dev_pts), 100))

    return ScoreBreakdown(
        total_score=total,
        otp_points=otp_pts,
        geofence_points=geo_pts,
        weight_points=weight_pts,
        signature_points=sig_pts,
        device_points=dev_pts,
        geofence_distance_m=geo_m,
        weight_loss_g=round(weight_loss_g, 1),
    )
