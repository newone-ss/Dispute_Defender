export function getMockAuditDetails(disputeId) {
  // Return tailored details based on dispute ID or default to comprehensive DSP-1024 template
  const isDSP1023 = disputeId === "DSP-1023";
  const isDSP1020 = disputeId === "DSP-1020";

  return {
    disputeId: disputeId || "DSP-1024",
    razorpayDisputeId: "disp_O6pQ7zWq82KL9a",
    paymentId: "pay_O5fT8xRm49JK1b",
    amount: isDSP1023 ? 28990 : isDSP1020 ? 4999 : 14500,
    currency: "INR",
    status: isDSP1023 ? "AUTO_ACCEPTED" : isDSP1020 ? "AUTO_ACCEPTED" : "AUTO_CONTESTED",
    riskScore: isDSP1023 ? 84 : isDSP1020 ? 18 : 95,
    decisionReason: isDSP1023 
      ? "Consumer Fairness Gate: Customer notified Zendesk regarding defective unit before chargeback. Released to eliminate ₹1,500 penalty."
      : isDSP1020
      ? "Insufficient Physical Evidence: Missing OTP and 1.8km geofence drift. Released early."
      : "Automated Contestation: Cryptographic doorstep OTP matched, 42m geofence precision, weight delta < 2%.",

    evaluatedAt: "2026-09-04T18:25:41+05:30",
    auditWorkerId: "worker_daemon_01_wal",
    leaseDurationSec: 300,
    razorpayDocumentId: isDSP1023 ? null : "doc_99aK71bO82mL4",
    razorpayContestReceipt: isDSP1023 ? null : "rcpt_cntst_910482_live_mock",

    sha256Digest: isDSP1023
      ? "4a2d89b1c7e6f30458129038dcefa71092b38fca615284092bce37482910fa72"
      : "9f83ab29c4d8e57201fa87c92b3d6812e34f71a980bc2e541f6a09de38b9104c",

    // TAB 1: EVIDENCE
    evidenceSignals: [
      {
        id: "otp",
        name: "Doorstep OTP Verification",
        category: "Physical Telemetry",
        points: isDSP1020 ? 0 : 35,
        maxPoints: 35,
        status: isDSP1020 ? "FAILED" : "VERIFIED",
        statusColor: isDSP1020 ? "rose" : "emerald",
        description: isDSP1020 
          ? "Delivery logged without single-use OTP entered on carrier handset"
          : "Single-use 4-digit token '8492' entered by customer at delivery point",
        benchmark: "Binary match requirement (35 pts)"
      },
      {
        id: "gps",
        name: "GPS Geofence Proximity",
        category: "Physical Telemetry",
        points: isDSP1020 ? 0 : isDSP1023 ? 30 : 30,
        maxPoints: 30,
        status: isDSP1020 ? "FAILED" : "VERIFIED",
        statusColor: isDSP1020 ? "rose" : "emerald",
        description: isDSP1020
          ? "Carrier coordinates were 1,840m from destination (Exceeds 500m falloff)"
          : isDSP1023
          ? "Carrier handset recorded 65m offset from destination pin"
          : "Carrier handset recorded 42m offset from delivery address geofence (Threshold <= 100m)",
        benchmark: "<=100m = 30 pts, <=500m = 24 pts, >2,000m = 0 pts"
      },
      {
        id: "weight",
        name: "Origin vs Doorstep Weight Scale",
        category: "Physical Telemetry",
        points: isDSP1020 ? 18 : isDSP1023 ? 14 : 20,
        maxPoints: 20,
        status: isDSP1023 ? "AMBIGUOUS" : isDSP1020 ? "VERIFIED" : "VERIFIED",
        statusColor: isDSP1023 ? "amber" : "emerald",
        description: isDSP1023
          ? "Origin: 1,850g | Doorstep: 1,716g (Delta: -134g / 7.2% drop)"
          : isDSP1020
          ? "Origin: 620g | Doorstep: 595g (Delta: -25g / 4.1% drop)"
          : "Origin: 2,400g | Doorstep: 2,356g (Delta: -44g / 1.83% tolerance)",
        benchmark: "<=5% delta = 20 pts, 5-15% scaled, >15% = 0 pts"
      },
      {
        id: "pod",
        name: "Proof of Delivery (POD) Signature",
        category: "Carrier Documentation",
        points: isDSP1020 ? 0 : isDSP1023 ? 0 : 10,
        maxPoints: 10,
        status: (isDSP1020 || isDSP1023) ? "FAILED" : "VERIFIED",
        statusColor: (isDSP1020 || isDSP1023) ? "rose" : "emerald",
        description: (isDSP1020 || isDSP1023)
          ? "Physical signature missing or marked uncollected on carrier manifest"
          : "Cryptographic touch-stylus signature recorded and verified on BlueDart manifest",
        benchmark: "Binary signature presence (10 pts)"
      },
      {
        id: "device",
        name: "Device & Session Fingerprint",
        category: "Digital Telemetry",
        points: isDSP1020 ? 0 : 5,
        maxPoints: 5,
        status: isDSP1020 ? "FAILED" : "VERIFIED",
        statusColor: isDSP1020 ? "rose" : "emerald",
        description: isDSP1020
          ? "Checkout session originated from anonymized Tor proxy node"
          : "Canvas fingerprint, WebGL vendor, and IP subnet match historical orders",
        benchmark: "Device identity profile match (5 pts)"
      }
    ],

    fairnessGateCheck: {
      passed: !isDSP1023,
      trippedCondition: isDSP1023 ? "OPEN_DEFECT_TICKET" : null,
      openDefectTicket: isDSP1023,
      defectTicketId: isDSP1023 ? "ZEN-4910" : null,
      excessiveWeightLoss: isDSP1023,
      weightLossGrams: isDSP1023 ? 134 : 44,
      chatDefectDetected: isDSP1023,
      gateAction: isDSP1023 ? "TRIGGER_AUTO_ACCEPT" : "PASS_TO_CONTEST",
      rationale: isDSP1023
        ? "Customer notified Zendesk support regarding damaged screen before filing dispute. Contesting would result in guaranteed defeat plus ₹1,500 bank penalty."
        : "No open defect tickets found. Weight loss within 100g cutoff. Zero customer complaints on omnichannel logs.",
    },

    // TAB 2: TELEMETRY
    courierTelemetry: {
      carrier: "BlueDart Express",
      awb: "BLD-994827104",
      serviceType: "Surface Express Cargo",
      driverId: "DRV-MUM-4821 (S. Rane)",
      driverHandset: "Samsung Galaxy XCover 5 / BlueDart POS v4.2.1",
      timestamps: {
        dispatched: "2026-09-02T09:14:00+05:30",
        outForDelivery: "2026-09-02T13:45:10+05:30",
        doorstepArrived: "2026-09-02T14:21:40+05:30",
        otpSubmitted: "2026-09-02T14:22:18+05:30",
      },
      weightMetrics: {
        hubScaleId: "HUB-BOM-SCALE-03 (Calibrated: 2026-08-15)",
        hubWeightGrams: 2400,
        doorstepScaleId: "VAN-04-PORTABLE-SCALE",
        doorstepWeightGrams: 2356,
        deltaGrams: -44,
        deltaPercentage: 1.83,
        tamperingThresholdGrams: 100,
        tamperDetected: false,
      },
      geofenceMetrics: {
        destinationAddress: "Flat 402, Sea Green Apts, Perry Cross Rd, Bandra West, Mumbai 400050",
        destinationCoords: { lat: 19.0560, lng: 72.8277 },
        deliveryScanCoords: { lat: 19.0563, lng: 72.8279 },
        offsetMeters: 42.1,
        accuracyRadiusMeters: 4.8,
        acceptableRadiusMeters: 100.0,
      },
      obdProtocol: {
        enabled: false,
        boxOpenedAtDoorstep: false,
        itemSerialChecked: false,
        tamperTapeIntact: true,
      }
    },

    // TAB 3: OCR EXTRACTION
    ocrData: {
      engine: "Google Gemini 1.5 Flash Vision (fallback: Regex Extractor)",
      manifestAwb: "BLD-994827104",
      scanConfidence: 0.994,
      processedAt: "2026-09-04T18:25:39+05:30",
      rawExtractedFields: {
        waybill_number: "BLD-994827104",
        booking_date: "2026-09-01",
        shipper_name: "Razorpay Hub Bhiwandi WH-02",
        recipient_name: "Aarav Sharma",
        shipping_pincode: "400050",
        product_description: "Smart Electronics / Audio Headset Pro",
        declared_value_inr: 14500.00,
        declared_weight_kg: 2.40,
        actual_manifest_weight_kg: 2.36,
        pod_status: "DELIVERED",
        receiver_relation: "SELF",
        otp_verified_flag: "Y",
        signature_captured: "TRUE",
        delivery_agent_code: "4821"
      }
    },

    // TAB 4: CUSTOMER RAG
    customerRag: {
      vectorStore: "ChromaDB (cosine similarity)",
      collection: "merchant_omnichannel_transcripts",
      queryEvaluated: "Customer reported non-receipt, damage, refund request or transit pilferage for order K8d9X3mN0pQ",
      matchedTranscripts: isDSP1023 ? [
        {
          source: "Zendesk Ticket #ZEN-4910",
          timestamp: "2026-09-03T11:14:00+05:30",
          customerChannel: "Email",
          messageSnippet: "Hi, I just opened the parcel delivered today and the screen is severely cracked inside the packaging. Please replace.",
          intent: "DAMAGED_PRODUCT_REPORT",
          sentimentScore: -0.88,
          relevanceDistance: 0.12,
          impactOnDispute: "Fairness Gate Auto-Trip: Merchant liable for transit damage. Contestation blocked to avoid ₹1,500 bank fee."
        }
      ] : [
        {
          source: "WhatsApp Business API",
          timestamp: "2026-09-02T15:02:14+05:30",
          customerChannel: "WhatsApp",
          messageSnippet: "Bot: Your package has been delivered! How was your experience? Aarav: Got it, thanks! Package was intact.",
          intent: "DELIVERY_CONFIRMATION",
          sentimentScore: 0.92,
          relevanceDistance: 0.14,
          impactOnDispute: "Corroborates courier telemetry. Directly refutes Product Not Received (PNR) claim."
        }
      ],
      regulatoryCitation: "Visa Compelling Evidence 3.0 (CE 3.0) Section 5.4.2 & NPCI UDIR Clause 8.1.b: Documented delivery confirmation with OTP and positive post-delivery customer acknowledgment constitutes definitive rebutting evidence against friendly fraud."
    },

    // TAB 5: RAW JSON PAYLOAD
    rawDatabaseRecord: {
      dispute_id: disputeId || "DSP-1024",
      gateway_dispute_id: "disp_O6pQ7zWq82KL9a",
      payment_id: "pay_O5fT8xRm49JK1b",
      amount_paise: 1450000,
      currency: "INR",
      reason_code: "10.4",
      status: isDSP1023 ? "AUTO_ACCEPTED" : "AUTO_CONTESTED",
      score: isDSP1023 ? 84 : 95,
      audit_job: {
        id: "job_829104",
        status: "COMPLETED",
        worker_lease_uuid: "7b4c9102-491a-4281-b519-729401829abc",
        lease_expires_at: "2026-09-04T18:30:41Z",
        attempts: 1,
        max_attempts: 3
      },
      telemetry: {
        otp_verified: true,
        gps_distance_meters: 42.1,
        weight_origin_g: 2400,
        weight_doorstep_g: 2356,
        delta_g: -44,
        pod_signed: true,
        device_matched: true
      },
      fairness_gate: {
        checked: true,
        passed: !isDSP1023,
        defect_ticket: isDSP1023 ? "ZEN-4910" : null,
        weight_tampered: false,
        penalty_avoided: isDSP1023
      },
      document_metadata: {
        sha256: isDSP1023
          ? "4a2d89b1c7e6f30458129038dcefa71092b38fca615284092bce37482910fa72"
          : "9f83ab29c4d8e57201fa87c92b3d6812e34f71a980bc2e541f6a09de38b9104c",
        template: "app/templates/npci_udir_packet.md.j2",
        compiler: "Jinja2 Deterministic Byte-Stable Engine v2.1"
      }
    },

    // TAB 6: NPCI UDIR LEGAL EVIDENCE PACKET
    udirLegalPacketMarkdown: `### NPCI UNIFIED DISPUTE & ISSUE RESOLUTION (UDIR)
#### LEGAL EVIDENCE REPRESENTMENT BRIEF — ZERO-HALLUCINATION ARBITRATION SUBMISSION

**TO:** Dispute Resolution Arbiter (NPCI / Visa / Acquiring Bank)  
**MERCHANT ACQUIRER:** Razorpay Software Private Limited  
**DISPUTE REFERENCE:** ${disputeId || "DSP-1024"} | Gateway ID: disp_O6pQ7zWq82KL9a  
**TRANSACTION IDENTIFIER:** pay_O5fT8xRm49JK1b | Order ID: order_K8d9X3mN0pQ  
**DISPUTED VALUE:** INR 14,500.00 | Reason Code: 10.4 (Product Not Received)  
**SUBMISSION DATE:** 2026-09-04 18:25:41 IST  
**CRYPTOGRAPHIC EVIDENCE DIGEST (SHA-256):**  
\`9f83ab29c4d8e57201fa87c92b3d6812e34f71a980bc2e541f6a09de38b9104c\`

---

#### 1. EXECUTIVE DEFENSE SUMMARY
The merchant respectfully contests chargeback dispute **${disputeId || "DSP-1024"}** in its entirety. The cardholder's claim of *Product Not Received* is categorically refuted by immutable physical courier telemetry, a verified single-use doorstep OTP entered on the carrier handset, and precision GPS geofencing confirmed within 42 meters of the registered cardholder address.

#### 2. PHYSICAL COURIER TELEMETRY RECONCILIATION
* **Logistics Partner:** BlueDart Express (AWB: BLD-994827104)
* **Delivery Confirmation Timestamp:** 2026-09-02 14:22:18 IST
* **Single-Use Doorstep OTP:** VERIFIED (Auth Token 8492 entered on BlueDart Handset #DRV-MUM-4821)
* **GPS Proximity:** Latitude 19.0563° N, Longitude 72.8279° E  
  *Linear distance from shipping destination: 42.1 meters (Within standard NPCI 100m threshold)*
* **Scale Weight Verification:**
  * Hub Dispatch Weight: 2,400 grams (Calibrated Bhiwandi Scale #03)
  * Doorstep Delivery Weight: 2,356 grams (Van Handheld Scale)
  * Recorded Delta: -44 grams (1.83% variance; zero package tampering)

#### 3. CUSTOMER COMMUNICATIONS AUDIT (CHROMA RAG)
Semantic query of customer omnichannel communications across WhatsApp, Email, and Zendesk reveals zero complaint tickets or damage reports prior to this chargeback. On 2026-09-02 at 15:02 IST, the cardholder confirmed receipt of the package via WhatsApp automated delivery notification.

#### 4. LEGAL COMPLIANCE & CE 3.0 / NPCI UDIR CITATION
Pursuant to Visa Compelling Evidence 3.0 (CE 3.0) Section 5.4.2 and NPCI Unified Dispute Resolution Guidelines Clause 8.1, the combination of:
1. Two-factor physical delivery authentication (Doorstep OTP + Carrier Manifest Signature),
2. Sub-50m GPS geofencing corroboration, and
3. Weight scale stability between fulfillment hub and recipient doorstep
constitutes irrefutable proof of successful consignment delivery.

**MERCHANT PRAYER:** The merchant requests immediate reversal of the disputed charge of INR 14,500.00 and restoration of merchant funds with zero network penalty.

---
*Generated deterministically by Razorpay Dispute Defender Engine. Byte-stable template rendered via Jinja2.*`
  };
}
