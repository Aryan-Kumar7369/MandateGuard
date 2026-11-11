'use client';

import React, { useEffect, useState } from 'react';
import { revokeMandate, verifyAuditChain } from '../lib/api';
import MandateReviewCard from '../components/MandateReviewCard';
import PasskeySigner from '../components/PasskeySigner';
import MerchantVerifyBadge from '../components/MerchantVerifyBadge';
import BudgetGauge from '../components/BudgetGauge';
import DelegationChainTree from '../components/DelegationChainTree';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';

export default function Dashboard() {
  const [events, setEvents] = useState([]);
  const [mandates, setMandates] = useState({});
  const [auditStatus, setAuditStatus] = useState(null);
  const [verifyingAudit, setVerifyingAudit] = useState(false);
  const [activeMandateToken, setActiveMandateToken] = useState(null);

  useEffect(() => {
    const eventSource = new EventSource(`${API_BASE}/events/stream`);

    const handleEvent = (type, data) => {
      const newEvt = {
        id: Math.random().toString(36).substring(7),
        type,
        data,
        timestamp: new Date().toLocaleTimeString(),
      };
      setEvents((prev) => [newEvt, ...prev.slice(0, 49)]);

      if (type === 'MANDATE_REVOKED') {
        setMandates((prev) => ({
          ...prev,
          [data.mandate_id]: { is_revoked: true },
        }));
      }

      if (type === 'MANDATE_CREATED') {
        setMandates((prev) => ({
          ...prev,
          [data.mandate_id]: { is_revoked: false },
        }));
      }
    };

    eventSource.addEventListener('PRE_FLIGHT_EVALUATED', (e) => {
      handleEvent('PRE_FLIGHT_EVALUATED', JSON.parse(e.data));
    });

    eventSource.addEventListener('MANDATE_REVOKED', (e) => {
      handleEvent('MANDATE_REVOKED', JSON.parse(e.data));
    });

    eventSource.addEventListener('MANDATE_CREATED', (e) => {
      handleEvent('MANDATE_CREATED', JSON.parse(e.data));
    });

    return () => {
      eventSource.close();
    };
  }, []);

  const handleRevoke = async (mandateId) => {
    try {
      await revokeMandate(mandateId);
      setMandates((prev) => ({
        ...prev,
        [mandateId]: { is_revoked: true },
      }));
    } catch (err) {
      alert(`Error revoking mandate ${mandateId}: ${err}`);
    }
  };

  const handleVerifyIntegrity = async () => {
    setVerifyingAudit(true);
    try {
      const result = await verifyAuditChain();
      setAuditStatus(result);
    } catch (err) {
      alert(`Audit verification error: ${err}`);
    } finally {
      setVerifyingAudit(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6 font-sans space-y-6">
      <header className="flex justify-between items-center border-b border-slate-800 pb-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-indigo-400">MandateGuard Control Center</h1>
          <p className="text-sm text-slate-400">Live Intent Security, Biometric Governance & Chain Intelligence Dashboard</p>
        </div>
        <div className="flex items-center space-x-4">
          <button
            onClick={handleVerifyIntegrity}
            disabled={verifyingAudit}
            className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 rounded text-sm font-semibold transition disabled:opacity-50 shadow-lg"
          >
            {verifyingAudit ? 'Verifying...' : 'Verify Audit Hash-Chain'}
          </button>
        </div>
      </header>

      {auditStatus && (
        <div className={`p-4 rounded border ${auditStatus.is_valid ? 'bg-emerald-950/50 border-emerald-500 text-emerald-200' : 'bg-rose-950/50 border-rose-500 text-rose-200'}`}>
          <div className="flex items-center justify-between">
            <span className="font-semibold">{auditStatus.is_valid ? '✔ AUDIT CHAIN INTEGRITY VALID' : '✖ TAMPER DETECTED IN AUDIT LOG'}</span>
            <span className="text-xs">Verified Events: {auditStatus.total_events}</span>
          </div>
          <p className="text-sm mt-1">{auditStatus.message}</p>
        </div>
      )}

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <MandateReviewCard apiBase={API_BASE} />
        <PasskeySigner apiBase={API_BASE} onSigned={(token) => setActiveMandateToken(token)} />
        <MerchantVerifyBadge apiBase={API_BASE} />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <BudgetGauge apiBase={API_BASE} />
        <DelegationChainTree apiBase={API_BASE} />
      </section>

      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold border-b border-slate-800 pb-2 mb-4 text-rose-400">Emergency Kill-Switch</h2>
          <div className="space-y-4">
            {Object.keys(mandates).length === 0 ? (
              <p className="text-sm text-slate-500 italic">No mandates registered in active session stream.</p>
            ) : (
              Object.entries(mandates).map(([id, state]) => (
                <div key={id} className="flex justify-between items-center bg-slate-950 p-3 rounded border border-slate-800">
                  <div>
                    <span className="text-sm font-mono block">{id}</span>
                    <span className={`text-xs ${state.is_revoked ? 'text-rose-400' : 'text-emerald-400'}`}>
                      {state.is_revoked ? 'REVOKED' : 'ACTIVE'}
                    </span>
                  </div>
                  {!state.is_revoked && (
                    <button
                      onClick={() => handleRevoke(id)}
                      className="px-3 py-1 bg-rose-600 hover:bg-rose-700 text-white rounded text-xs font-semibold transition"
                    >
                      REVOKE NOW
                    </button>
                  )}
                </div>
              ))
            )}
          </div>
        </div>

        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-lg p-5">
          <div className="flex justify-between items-center border-b border-slate-800 pb-2 mb-4">
            <h2 className="text-lg font-semibold text-indigo-300">Live Agent Activity Feed</h2>
            <span className="flex items-center text-xs text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 mr-2 animate-ping" />
              SSE Stream Connected
            </span>
          </div>

          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
            {events.length === 0 ? (
              <p className="text-sm text-slate-500 italic">Waiting for agent pre-flight transactions...</p>
            ) : (
              events.map((evt) => (
                <div key={evt.id} className="bg-slate-950 border border-slate-800 p-3 rounded text-sm font-mono">
                  <div className="flex justify-between text-xs text-slate-400 mb-1">
                    <span className="font-semibold text-indigo-400">{evt.type}</span>
                    <span>{evt.timestamp}</span>
                  </div>
                  {evt.type === 'PRE_FLIGHT_EVALUATED' && (
                    <div>
                      <div className="flex justify-between">
                        <span>Mandate: {evt.data.mandate_id}</span>
                        <span className={`font-bold ${evt.data.decision === 'ALLOW' ? 'text-emerald-400' : evt.data.decision === 'BLOCK' ? 'text-rose-400' : 'text-amber-400'}`}>
                          {evt.data.decision}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-1">{evt.data.reason}</p>
                    </div>
                  )}
                  {evt.type === 'MANDATE_REVOKED' && (
                    <div className="text-rose-400 font-semibold">
                      MANDATE REVOKED: {evt.data.mandate_id}
                    </div>
                  )}
                  {evt.type === 'MANDATE_CREATED' && (
                    <div className="text-emerald-400 font-semibold">
                      NEW MANDATE REGISTERED: {evt.data.mandate_id}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </section>
    </div>
  );
}