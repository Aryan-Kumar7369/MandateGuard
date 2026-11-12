'use client';

import React, { useEffect, useState } from 'react';
import Navbar from '../components/Navbar';
import DemoController from '../components/DemoController';
import MandateReviewCard from '../components/MandateReviewCard';
import PasskeySigner from '../components/PasskeySigner';
import BudgetGauge from '../components/BudgetGauge';
import DelegationChainTree from '../components/DelegationChainTree';
import MerchantVerifyBadge from '../components/MerchantVerifyBadge';
import RedTeamDashboard from '../components/RedTeamDashboard';
import DisputeCenter from '../components/DisputeCenter';
import LiveActivityFeed from '../components/LiveActivityFeed';
import { revokeMandate, verifyAuditChain } from '../lib/api';
import { ShieldCheck, ShieldAlert, CheckCircle2, Lock, ArrowUpRight } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:8000/api/v1';

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('overview');
  const [events, setEvents] = useState([]);
  const [mandates, setMandates] = useState({
    m_corp_root: { is_revoked: false },
    m_corp_devops: { is_revoked: false },
  });
  const [auditStatus, setAuditStatus] = useState(null);
  const [verifyingAudit, setVerifyingAudit] = useState(false);

  useEffect(() => {
    let eventSource;
    try {
      eventSource = new EventSource(`${API_BASE}/events/stream`);

      const handleIncoming = (type, data) => {
        const item = {
          id: Math.random().toString(36).substring(7),
          type,
          data,
          timestamp: new Date().toLocaleTimeString(),
        };
        setEvents((prev) => [item, ...prev.slice(0, 49)]);

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
        handleIncoming('PRE_FLIGHT_EVALUATED', JSON.parse(e.data));
      });

      eventSource.addEventListener('MANDATE_REVOKED', (e) => {
        handleIncoming('MANDATE_REVOKED', JSON.parse(e.data));
      });

      eventSource.addEventListener('MANDATE_CREATED', (e) => {
        handleIncoming('MANDATE_CREATED', JSON.parse(e.data));
      });

      eventSource.addEventListener('DISPUTE_CREATED', (e) => {
        handleIncoming('DISPUTE_CREATED', JSON.parse(e.data));
      });
    } catch (err) {
    }

    return () => {
      if (eventSource) eventSource.close();
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
      alert(`Error revoking mandate: ${err.message}`);
    }
  };

  const handleVerifyIntegrity = async () => {
    setVerifyingAudit(true);
    try {
      const result = await verifyAuditChain();
      setAuditStatus(result);
    } catch (err) {
      alert(`Audit verification error: ${err.message}`);
    } finally {
      setVerifyingAudit(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f7fa] text-slate-800 font-sans flex flex-col">
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onVerifyAudit={handleVerifyIntegrity}
        isVerifying={verifyingAudit}
        auditStatus={auditStatus}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        <DemoController
          onEventTriggered={(act) => {
            if (act === 'SEED') {
              setMandates({
                m_corp_root: { is_revoked: false },
                m_corp_devops: { is_revoked: false },
              });
            }
          }}
        />

        {auditStatus && (
          <div
            className={`p-4 rounded-2xl border shadow-xs transition-all duration-200 ${
              auditStatus.is_valid
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-rose-50 border-rose-300 text-rose-900'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {auditStatus.is_valid ? (
                  <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                ) : (
                  <ShieldAlert className="w-5 h-5 text-rose-600" />
                )}
                <span className="font-extrabold text-sm tracking-wide">
                  {auditStatus.is_valid
                    ? 'AUDIT CHAIN INTEGRITY CONFIRMED (SHA-256 ZERO TAMPER)'
                    : 'AUDIT LEDGER TAMPER DETECTED'}
                </span>
              </div>
              <span className="text-xs font-mono font-bold bg-white/80 px-2.5 py-1 rounded-full border border-current/20">
                Verified Blocks: {auditStatus.total_events_verified || auditStatus.total_events || 0}
              </span>
            </div>
            <p className="text-xs mt-1.5 leading-relaxed opacity-90">{auditStatus.message}</p>
          </div>
        )}

        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-1">
                <BudgetGauge defaultMandateId="m_corp_devops" />
              </div>
              <div className="lg:col-span-2">
                <MerchantVerifyBadge defaultMandateId="m_corp_devops" />
              </div>
            </div>

            <LiveActivityFeed
              events={events}
              mandates={mandates}
              onRevoke={handleRevoke}
            />
          </div>
        )}

        {activeTab === 'mandate' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MandateReviewCard
              onMandateCreated={(id) => {
                setMandates((prev) => ({ ...prev, [id]: { is_revoked: false } }));
              }}
            />
            <PasskeySigner apiBase={API_BASE} />
          </div>
        )}

        {activeTab === 'delegation' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <DelegationChainTree defaultRootId="m_corp_root" />
            </div>
            <div className="lg:col-span-1">
              <BudgetGauge defaultMandateId="m_corp_devops" />
            </div>
          </div>
        )}

        {activeTab === 'merchant' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <MerchantVerifyBadge defaultMandateId="m_corp_devops" />
            <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
              <div className="flex items-center space-x-2 text-[#001c3f] font-bold text-base border-b border-slate-100 pb-3">
                <Lock className="w-4 h-4 text-[#0070ba]" />
                <span>Merchant Privacy Invariants</span>
              </div>
              <ul className="space-y-3 text-xs text-slate-600 leading-relaxed">
                <li className="flex items-start space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>
                    <strong>Zero Financial Leakage:</strong> The merchant receives a verifiable Boolean signal with a cryptographic token without knowing total account balance or full mandate terms.
                  </span>
                </li>
                <li className="flex items-start space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>
                    <strong>Pre-Flight Rejection:</strong> If an agent attempts to spend outside permitted categories or merchants, checkout fails before cart authorization.
                  </span>
                </li>
                <li className="flex items-start space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>
                    <strong>Instant Revocation Propagation:</strong> If a human activates the kill-switch, merchant signals immediately report MANDATE_REVOKED.
                  </span>
                </li>
              </ul>
            </div>
          </div>
        )}

        {activeTab === 'redteam' && (
          <div>
            <RedTeamDashboard />
          </div>
        )}

        {activeTab === 'disputes' && (
          <div>
            <DisputeCenter />
          </div>
        )}
      </main>

      <footer className="bg-white border-t border-slate-200 py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 rounded bg-[#0070ba] flex items-center justify-center text-white">
              <ShieldCheck className="w-3.5 h-3.5" />
            </div>
            <span className="font-bold text-slate-700">MandateGuard</span>
            <span>- Provable Permission for AI Agents That Spend</span>
          </div>
          <span className="text-[11px] text-slate-400 font-mono">
            PayPal Orders v2 Sandbox &bull; FIDO2 Passkeys &bull; Ed25519 &bull; SHA-256
          </span>
        </div>
      </footer>
    </div>
  );
}
