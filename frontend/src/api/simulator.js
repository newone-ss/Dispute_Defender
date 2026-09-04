import { request } from './client';
import { MOCK_SCENARIO_RESULTS } from '../mock/mockScenarios';

function normalizeSimulationResult(res, scenarioId) {
  if (!res) return res;
  if (res.disputeId && res.decision) return res; // already in mock format
  const isContested = res.status === 'AUTO_CONTESTED' || res.status === 'contested' || res.status === 'MANUALLY_CONTESTED';
  const amount = res.amount_inr ?? (res.amount_paise ? res.amount_paise / 100 : 2499.0);
  return {
    ...res,
    disputeId: res.razorpay_dispute_id || res.id || `disp_sim_${Date.now()}`,
    decision: (typeof res.status === 'string' ? res.status.toUpperCase() : 'AUTO_CONTESTED'),
    reason: res.decision_reason || `Simulated scenario: ${scenarioId}`,
    riskScore: res.score ?? 84,
    financialImpact: {
      amountINR: amount,
      label: isContested ? 'Direct Revenue Defended' : 'Zero Liability Settlement',
      details: isContested ? 'Protected against customer chargeback' : 'Prevented ₹1,500 bank penalty fee',
    },
  };
}

export async function runScenario(scenarioId) {
  const fallback = MOCK_SCENARIO_RESULTS[scenarioId] || MOCK_SCENARIO_RESULTS.winnable_clean;
  const data = await request('/simulator/run', {
    method: 'POST',
    body: JSON.stringify({ scenario: scenarioId }),
  }, fallback);
  return normalizeSimulationResult(data, scenarioId);
}
