import { request } from './client';
import { getMockAuditDetails } from '../mock/mockAudits';

export async function getAudit(id) {
  const fallback = getMockAuditDetails(id);
  return request(`/audit/${id}`, { method: 'GET' }, fallback);
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
