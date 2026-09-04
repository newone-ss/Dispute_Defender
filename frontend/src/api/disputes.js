import { request } from './client';
import { MOCK_DISPUTES } from '../mock/mockDisputes';

export async function getDisputes(params = {}) {
  // Try real API, fallback to mock filtered data
  const fallback = MOCK_DISPUTES.filter((item) => {
    if (params.status && params.status !== 'ALL' && item.status !== params.status) {
      return false;
    }
    if (params.search) {
      const q = params.search.toLowerCase();
      const matchId = item.id.toLowerCase().includes(q);
      const matchCust = item.customerName.toLowerCase().includes(q);
      const matchAwb = item.awb?.toLowerCase().includes(q);
      const matchOrder = item.orderId.toLowerCase().includes(q);
      if (!matchId && !matchCust && !matchAwb && !matchOrder) return false;
    }
    return true;
  });

  const queryString = new URLSearchParams(params).toString();
  const endpoint = `/disputes${queryString ? `?${queryString}` : ''}`;

  return request(endpoint, { method: 'GET' }, fallback);
}

export async function getDispute(id) {
  const fallback = MOCK_DISPUTES.find((d) => d.id === id) || MOCK_DISPUTES[0];
  return request(`/disputes/${id}`, { method: 'GET' }, fallback);
}

export async function overrideDispute(id, payload) {
  const fallbackResponse = {
    success: true,
    disputeId: id,
    previousStatus: payload.previousStatus || 'NEEDS_REVIEW',
    newStatus: payload.newStatus,
    operatorNotes: payload.notes,
    overrideTimestamp: new Date().toISOString(),
    sha256AuditHash: 'f48291048291ba837201948572019bca837162534890129bcfe8291048291aa',
  };

  const action =
    payload.action ||
    (payload.newStatus?.toLowerCase().includes('contest') ? 'contest' : 'accept');

  const backendPayload = {
    action,
    operator_note: payload.notes || payload.operator_note || 'Manual operator override',
    ...payload,
  };

  return request(`/disputes/${id}/override`, {
    method: 'POST',
    body: JSON.stringify(backendPayload),
  }, fallbackResponse);
}
