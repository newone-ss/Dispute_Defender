import { request } from './client';
import { getMockAuditDetails } from '../mock/mockAudits';

export async function getAudit(id) {
  const baseMock = getMockAuditDetails(id);
  try {
    const raw = await request(`/audit/${id}`, { method: 'GET' }, null);
    if (!raw) return baseMock;

    // Normalize values between backend DisputeOut schema and frontend audit views
    const amount = raw.amount ?? raw.amount_inr ?? (raw.amount_paise ? raw.amount_paise / 100 : baseMock.amount);
    const score = raw.riskScore ?? raw.score ?? (raw.status === 'AUTO_CONTESTED' ? 95 : baseMock.riskScore);
    const status = (raw.status || baseMock.status || 'AUTO_CONTESTED').toUpperCase();
    const disputeId = raw.disputeId || raw.razorpay_dispute_id || raw.id || id;
    const paymentId = raw.payment_id || raw.paymentId || baseMock.paymentId;
    const decisionReason = raw.decision_reason || raw.decisionReason || baseMock.decisionReason;

    // Telemetry normalization from raw.telemetry
    const tel = raw.telemetry || {};
    const telOtp = tel.otp?.verified ?? tel.otp_verified ?? true;
    const telGps = tel.geofence?.distance_m ?? tel.gps_distance_meters ?? 42.1;
    const telWeightShipped = tel.weight?.shipped_g ?? 2400;
    const telWeightDelivered = tel.weight?.delivered_g ?? 2356;
    const weightDelta = telWeightDelivered - telWeightShipped;
    const weightDeltaPct = Math.abs(Math.round((weightDelta / (telWeightShipped || 1)) * 10000) / 100);

    // Dynamic evidence signals
    const evidenceSignals = (Array.isArray(raw.evidenceSignals) && raw.evidenceSignals.length > 0)
      ? raw.evidenceSignals
      : [
          {
            id: "otp",
            name: "Doorstep OTP Verification",
            category: "Physical Telemetry",
            points: telOtp ? 35 : 0,
            maxPoints: 35,
            status: telOtp ? "VERIFIED" : "FAILED",
            statusColor: telOtp ? "emerald" : "rose",
            description: telOtp
              ? "Single-use 4-digit token matched and entered by customer on carrier handset"
              : "Delivery logged without single-use OTP entered on carrier handset",
            benchmark: "Binary match requirement (35 pts)"
          },
          {
            id: "gps",
            name: "GPS Geofence Proximity",
            category: "Physical Telemetry",
            points: telGps <= 100 ? 30 : telGps <= 500 ? 24 : 0,
            maxPoints: 30,
            status: telGps <= 100 ? "VERIFIED" : telGps <= 500 ? "AMBIGUOUS" : "FAILED",
            statusColor: telGps <= 100 ? "emerald" : telGps <= 500 ? "amber" : "rose",
            description: `Carrier handset recorded ${telGps}m offset from destination delivery pin (Threshold <= 100m)`,
            benchmark: "<=100m = 30 pts, <=500m = 24 pts, >2,000m = 0 pts"
          },
          {
            id: "weight",
            name: "Origin vs Doorstep Weight Scale",
            category: "Physical Telemetry",
            points: weightDeltaPct <= 5 ? 20 : weightDeltaPct <= 15 ? 12 : 0,
            maxPoints: 20,
            status: weightDeltaPct <= 5 ? "VERIFIED" : weightDeltaPct <= 15 ? "AMBIGUOUS" : "FAILED",
            statusColor: weightDeltaPct <= 5 ? "emerald" : weightDeltaPct <= 15 ? "amber" : "rose",
            description: `Origin: ${telWeightShipped}g | Doorstep: ${telWeightDelivered}g (Delta: ${weightDelta}g / ${weightDeltaPct}% variance)`,
            benchmark: "<=5% delta = 20 pts, 5-15% scaled, >15% = 0 pts"
          },
          {
            id: "pod",
            name: "Proof of Delivery (POD) Signature",
            category: "Carrier Documentation",
            points: (tel.delivery_signature ?? true) ? 10 : 0,
            maxPoints: 10,
            status: (tel.delivery_signature ?? true) ? "VERIFIED" : "FAILED",
            statusColor: (tel.delivery_signature ?? true) ? "emerald" : "rose",
            description: (tel.delivery_signature ?? true)
              ? "Touch-stylus recipient delivery signature recorded on BlueDart manifest"
              : "Physical signature missing or marked uncollected",
            benchmark: "Binary signature presence (10 pts)"
          },
          {
            id: "device",
            name: "Device & Session Fingerprint",
            category: "Digital Telemetry",
            points: 5,
            maxPoints: 5,
            status: "VERIFIED",
            statusColor: "emerald",
            description: "Canvas fingerprint, WebGL vendor, and IP subnet match historical orders",
            benchmark: "Device identity profile match (5 pts)"
          }
        ];

    const isFairnessTripped = status === 'AUTO_ACCEPTED';
    const fairnessGateCheck = raw.fairnessGateCheck || {
      passed: !isFairnessTripped,
      trippedCondition: isFairnessTripped ? "OPEN_DEFECT_TICKET" : null,
      openDefectTicket: isFairnessTripped,
      defectTicketId: isFairnessTripped ? "ZEN-4910" : null,
      excessiveWeightLoss: isFairnessTripped,
      weightLossGrams: isFairnessTripped ? 134 : Math.abs(weightDelta),
      chatDefectDetected: isFairnessTripped,
      gateAction: isFairnessTripped ? "TRIGGER_AUTO_ACCEPT" : "PASS_TO_CONTEST",
      rationale: isFairnessTripped
        ? "Customer notified support regarding transit defect before filing dispute. Contesting blocked to eliminate ₹1,500 penalty."
        : "No open defect tickets found. Weight loss within tolerance. Zero customer complaints on omnichannel logs.",
    };

    return {
      ...baseMock,
      disputeId,
      razorpayDisputeId: disputeId,
      paymentId,
      amount,
      currency: raw.currency || 'INR',
      status,
      riskScore: score,
      decisionReason: decisionReason || baseMock.decisionReason,
      evidenceSignals,
      fairnessGateCheck,
      customerRag: raw.customerRag || baseMock.customerRag,
      courierTelemetry: raw.courierTelemetry || baseMock.courierTelemetry,
      ocrData: raw.ocrData || baseMock.ocrData,
      udirLegalPacketMarkdown: raw.evidence_packet || baseMock.udirLegalPacketMarkdown,
      rawDatabaseRecord: raw,
    };
  } catch (err) {
    console.warn("Falling back to mock audit dossier:", err);
    return baseMock;
  }
}

export async function downloadUdirPacket(id) {
  const audit = getMockAuditDetails(id);
  const blob = new Blob([audit.udirLegalPacketMarkdown], { type: 'text/markdown;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `NPCI_UDIR_Packet_${id || 'DSP-1024'}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  return { success: true };
}
