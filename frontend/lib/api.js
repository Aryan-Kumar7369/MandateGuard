const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';

export async function revokeMandate(mandateId) {
  const res = await fetch(`${API_BASE}/mandates/${encodeURIComponent(mandateId)}/revoke`, {
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

export async function createMandate(payload) {
  const res = await fetch(`${API_BASE}/mandates/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to create mandate');
  return res.json();
}

export async function getMandateBudget(mandateId) {
  const res = await fetch(`${API_BASE}/mandates/${encodeURIComponent(mandateId)}/budget`);
  if (!res.ok) throw new Error(`Mandate ${mandateId} not found`);
  return res.json();
}

export async function getDelegationTree(mandateId) {
  const res = await fetch(`${API_BASE}/delegations/tree/${encodeURIComponent(mandateId)}`);
  if (!res.ok) throw new Error(`Delegation tree for ${mandateId} not found`);
  return res.json();
}

export async function verifyMerchantSignal(payload) {
  const res = await fetch(`${API_BASE}/merchant/verify-signal`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error('Failed to verify merchant signal');
  return res.json();
}

export async function runRedTeamSuite() {
  const res = await fetch(`${API_BASE}/redteam/run`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to execute red team attack suite');
  return res.json();
}

export async function listDisputes() {
  const res = await fetch(`${API_BASE}/disputes/`);
  if (!res.ok) throw new Error('Failed to fetch disputes');
  return res.json();
}

export async function syncDisputes() {
  const res = await fetch(`${API_BASE}/disputes/sync`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to sync disputes');
  return res.json();
}

export async function getDisputeEvidenceBundle(disputeId) {
  const res = await fetch(`${API_BASE}/disputes/evidence-bundle/${encodeURIComponent(disputeId)}`);
  if (!res.ok) throw new Error(`Failed to load evidence bundle for ${disputeId}`);
  return res.json();
}

export async function getRecoursePreview(disputeId) {
  const res = await fetch(`${API_BASE}/disputes/recourse-preview/${encodeURIComponent(disputeId)}`);
  if (!res.ok) throw new Error(`Failed to load recourse preview for ${disputeId}`);
  return res.json();
}

export async function simulateDispute(orderId, amount, reason) {
  const url = `${API_BASE}/disputes/simulate-event?paypal_order_id=${encodeURIComponent(orderId)}&amount=${amount}&reason=${encodeURIComponent(reason)}`;
  const res = await fetch(url, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to simulate dispute');
  return res.json();
}

export async function seedDemoEnvironment() {
  const res = await fetch(`${API_BASE}/demo/seed`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to seed demo data');
  return res.json();
}

export async function triggerDemoAct1() {
  const res = await fetch(`${API_BASE}/demo/act1`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to execute Act 1');
  return res.json();
}

export async function triggerDemoAct2() {
  const res = await fetch(`${API_BASE}/demo/act2`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to execute Act 2');
  return res.json();
}

export async function triggerDemoAct3() {
  const res = await fetch(`${API_BASE}/demo/act3`, {
    method: 'POST',
  });
  if (!res.ok) throw new Error('Failed to execute Act 3');
  return res.json();
}
