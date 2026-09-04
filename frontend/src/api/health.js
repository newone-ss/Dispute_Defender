import { request } from './client';

export async function getHealth() {
  return request('/healthz', { method: 'GET' }, {
    status: 'offline',
    database: 'unknown',
    service: 'Dispute Defender (Offline Fallback)',
  });
}
