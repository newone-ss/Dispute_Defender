export const MOCK_METRICS = {
  netProtectedINR: 503686.31,
  roiBoostPercentage: 76.8,
  bankPenaltiesAvoidedINR: 18000.00,
  penaltiesAvoidedCount: 12,
  penaltyPerLossINR: 1500,
  autoContestWinRate: 85.0,
  totalDisputesProcessed: 50,
  totalExposureINR: 656074.33,
  directRevenueRecoveredINR: 467898.00,
  humanReviewRecoveredINR: 17788.31,

  decisionDistribution: [
    {
      status: "AUTO_CONTESTED",
      label: "Auto Contested",
      count: 32,
      percentage: 64.0,
      amountINR: 550468.24,
      color: "#10b981", // emerald
      description: "Contested with cryptographic NPCI UDIR packet",
    },
    {
      status: "NEEDS_REVIEW",
      label: "Needs Review",
      count: 6,
      percentage: 12.0,
      amountINR: 35576.61,
      color: "#f59e0b", // amber
      description: "Ambiguous signals queued for risk officer manual check",
    },
    {
      status: "AUTO_ACCEPTED",
      label: "Auto Accepted",
      count: 12,
      percentage: 24.0,
      amountINR: 70029.48,
      color: "#f43f5e", // rose
      description: "Zero-liability release avoiding ₹1,500 bank penalty",
    },
  ],

  telemetryCompliance: {
    otpVerificationRate: 88.0,
    gpsGeofenceCompliance: 76.5,
    weightScaleMatchRate: 82.0,
    podSignatureMatchRate: 91.5,
    obdProtocolRate: 20.0,
  },

  accuracyMetrics: {
    overallAccuracy: 100.0,
    fairnessGateAccuracy: 100.0,
    obdRoutingAccuracy: 100.0,
  },

  activityTimeline: [
    { hour: "08:00", contested: 2, reviewed: 0, accepted: 1, savedINR: 34500 },
    { hour: "10:00", contested: 5, reviewed: 1, accepted: 2, savedINR: 88200 },
    { hour: "12:00", contested: 8, reviewed: 2, accepted: 3, savedINR: 142000 },
    { hour: "14:00", contested: 7, reviewed: 1, accepted: 2, savedINR: 115000 },
    { hour: "16:00", contested: 6, reviewed: 1, accepted: 3, savedINR: 78500 },
    { hour: "18:00", contested: 4, reviewed: 1, accepted: 1, savedINR: 45486 },
  ]
};
