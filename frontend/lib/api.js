const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';

export async function revokeMandate(mandateId) {
  const res = await fetch(`${API_BASE}/mandates/${mandateId}/revoke`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to revoke mandate');
  return res.json();
}

export async function verifyAuditChain() {
  const res = await fetch(`${API_BASE}/audit/verify`);
  if (!res.ok) throw new Error('Failed to verify audit integrity');
  return res.json();
}

export async function parsePromptToMandate(prompt) {
  const res = await fetch(`${API_BASE}/mandates/parse-prompt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt }),
  });
  if (!res.ok) throw new Error('Failed to parse natural language mandate');
  return res.json();
}