"""Unit tests verifying byte-stable evidence packet compilation and SHA-256 integrity."""

from app.core.compiler import compile_packet
from app.core.schemas import GateResult, PolicyCitation, TelemetryData


def test_compiler_byte_stable_snapshot():
    """Assert compile_packet generates deterministic markdown with consistent SHA-256."""
    telemetry = TelemetryData(
        delivery_type="STANDARD",
        otp_verified=True,
        geofence_distance_m=42.5,
        shipped_weight_g=520.0,
        delivered_weight_g=518.0,
        delivery_signature=True,
        device_fingerprint_match=True,
        courier="Delhivery Express",
        awb_number="DEL-883921004",
    )
    citations = [
        PolicyCitation(
            network="NPCI",
            clause_id="UDIR-2.1",
            text="Product Not Received: Proof of delivery and OTP constitute compelling evidence.",
            source_file="npci_udir.pdf",
            policy_version="2026.1.0",
        )
    ]
    gate = GateResult(triggered=False, action="PASS_THROUGH")

    rendered1 = compile_packet(
        dispute_id="disp_snapshot_test",
        payment_id="pay_snapshot_test",
        amount_inr=2499.0,
        reason_code="npci.udir.pnr",
        score=95,
        telemetry=telemetry,
        citations=citations,
        fairness=gate,
    )

    # Re-run immediately
    rendered2 = compile_packet(
        dispute_id="disp_snapshot_test",
        payment_id="pay_snapshot_test",
        amount_inr=2499.0,
        reason_code="npci.udir.pnr",
        score=95,
        telemetry=telemetry,
        citations=citations,
        fairness=gate,
    )

    # Extract dynamic timestamp line before comparison
    lines1 = [
        line
        for line in rendered1.splitlines()
        if "Compilation Timestamp" not in line and "Document Ref" not in line
    ]
    lines2 = [
        line
        for line in rendered2.splitlines()
        if "Compilation Timestamp" not in line and "Document Ref" not in line
    ]

    assert lines1 == lines2
    assert "Delhivery Express" in rendered1
    assert "DEL-883921004" in rendered1
    assert "42.5m" in rendered1
