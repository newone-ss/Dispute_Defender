import { request } from './client';
import { MOCK_METRICS } from '../mock/mockMetrics';

function normalizeMetrics(data) {
  if (!data) return data;
  const netProtected = data.netProtectedINR ?? data.net_inr_saved ?? data.protected_inr ?? 0;
  const penaltiesAvoided = data.bankPenaltiesAvoidedINR ?? data.bank_penalties_avoided ?? 0;
  const winRate = data.autoContestWinRate ?? data.win_rate ?? data.win_rate_percent ?? 85.0;
  const autoAccepted = data.auto_accepted_count ?? data.penaltiesAvoidedCount ?? 0;
  const autoContested = data.auto_contested_count ?? data.contested_count ?? 0;
  const needsReview = data.needs_review_count ?? 0;
  const total = data.totalDisputesProcessed ?? data.total_disputes ?? (autoContested + autoAccepted + needsReview);

  const decisionDistribution = data.decisionDistribution || [
    {
      status: "AUTO_CONTESTED",
      label: "Auto Contested",
      count: autoContested,
      percentage: total > 0 ? Math.round((autoContested / total) * 100) : 64.0,
      amountINR: netProtected,
      color: "#10b981",
      description: "Contested with cryptographic NPCI UDIR packet",
    },
    {
      status: "NEEDS_REVIEW",
      label: "Needs Review",
      count: needsReview,
      percentage: total > 0 ? Math.round((needsReview / total) * 100) : 12.0,
      amountINR: Math.round(netProtected * 0.08),
      color: "#f59e0b",
      description: "Ambiguous signals queued for risk officer manual check",
    },
    {
      status: "AUTO_ACCEPTED",
      label: "Auto Accepted",
      count: autoAccepted,
      percentage: total > 0 ? Math.round((autoAccepted / total) * 100) : 24.0,
      amountINR: penaltiesAvoided,
      color: "#f43f5e",
      description: "Zero-liability release avoiding ₹1,500 bank penalty",
    },
  ];

  return {
    ...data,
    netProtectedINR: netProtected,
    roiBoostPercentage: data.roiBoostPercentage ?? 76.8,
    bankPenaltiesAvoidedINR: penaltiesAvoided,
    penaltiesAvoidedCount: autoAccepted,
    penaltyPerLossINR: 1500,
    autoContestWinRate: winRate,
    totalDisputesProcessed: total,
    totalExposureINR: data.totalExposureINR ?? (netProtected + penaltiesAvoided),
    directRevenueRecoveredINR: data.directRevenueRecoveredINR ?? netProtected,
    humanReviewRecoveredINR: data.humanReviewRecoveredINR ?? 0,
    decisionDistribution,
    telemetryCompliance: data.telemetryCompliance || {
      otpVerificationRate: 88.0,
      gpsGeofenceCompliance: 76.5,
      weightScaleMatchRate: 82.0,
      podSignatureMatchRate: 91.5,
      obdProtocolRate: 20.0,
    },
    hourlyTrend: data.hourlyTrend || [
      { hour: "10:00", contested: 4, reviewed: 1, accepted: 1, savedINR: 48000 },
      { hour: "11:00", contested: 6, reviewed: 2, accepted: 2, savedINR: 82000 },
      { hour: "12:00", contested: 5, reviewed: 0, accepted: 3, savedINR: 75000 },
      { hour: "13:00", contested: 10, reviewed: 2, accepted: 4, savedINR: 182000 },
      { hour: "14:00", contested: 7, reviewed: 1, accepted: 2, savedINR: 115000 },
    ],
    activityTimeline: data.activityTimeline || [
      { hour: "08:00", contested: Math.max(1, Math.round(autoContested * 0.15)), accepted: Math.max(0, Math.round(autoAccepted * 0.15)), reviewed: 0 },
      { hour: "10:00", contested: Math.max(2, Math.round(autoContested * 0.25)), accepted: Math.max(1, Math.round(autoAccepted * 0.25)), reviewed: 1 },
      { hour: "12:00", contested: Math.max(2, Math.round(autoContested * 0.30)), accepted: Math.max(1, Math.round(autoAccepted * 0.30)), reviewed: 2 },
      { hour: "14:00", contested: Math.max(1, Math.round(autoContested * 0.20)), accepted: Math.max(1, Math.round(autoAccepted * 0.20)), reviewed: 1 },
      { hour: "16:00", contested: Math.max(1, Math.round(autoContested * 0.10)), accepted: Math.max(0, Math.round(autoAccepted * 0.10)), reviewed: 1 },
      { hour: "18:00", contested: Math.max(0, Math.round(autoContested * 0.05)), accepted: Math.max(0, Math.round(autoAccepted * 0.05)), reviewed: 0 },
    ],
  };
}

export async function getDashboard() {
  const data = await request('/dashboard/metrics', { method: 'GET' }, MOCK_METRICS);
  return normalizeMetrics(data);
}
