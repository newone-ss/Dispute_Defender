"""Unit tests verifying pure telemetry scoring engine."""

import pytest

from app.config import get_config
from app.core.schemas import TelemetryData
from app.policy.fairness_gate import load_scoring_policy
from app.policy.scoring_engine import score

config = get_config()
policy = load_scoring_policy(config.scoring_policy_path)


@pytest.mark.parametrize(
    "telemetry,expected_min_score,expected_max_score",
    [
        # Perfect doorstep delivery: OTP + 40m GPS + matching weight + signature + device
        (
            TelemetryData(
                otp_verified=True,
                geofence_distance_m=40.0,
                shipped_weight_g=500.0,
                delivered_weight_g=498.0,
                delivery_signature=True,
                device_fingerprint_match=True,
            ),
            95,
            100,
        ),
        # Good OTP + 400m GPS (secondary perimeter 80% pts) + clean weight
        (
            TelemetryData(
                otp_verified=True,
                geofence_distance_m=400.0,
                shipped_weight_g=500.0,
                delivered_weight_g=500.0,
                delivery_signature=False,
                device_fingerprint_match=False,
            ),
            75,
            85,
        ),
        # Failed OTP, far GPS (15km), missing POD -> Low score
        (
            TelemetryData(
                otp_verified=False,
                geofence_distance_m=15000.0,
                shipped_weight_g=500.0,
                delivered_weight_g=0.0,
                delivery_signature=False,
                device_fingerprint_match=False,
            ),
            0,
            15,
        ),
    ],
)
def test_pure_scoring_engine_bounds(telemetry, expected_min_score, expected_max_score):
    """Verify that pure scoring function deterministically stays within expected point ranges."""
    res = score(telemetry, policy)
    assert expected_min_score <= res.total_score <= expected_max_score
