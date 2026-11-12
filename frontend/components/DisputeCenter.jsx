import React, { useState, useEffect } from 'react';
import { Scale, FileText, CheckCircle2, XCircle, RefreshCw, Play, ShieldCheck, Lock, ExternalLink } from 'lucide-react';
import { listDisputes, syncDisputes, getDisputeEvidenceBundle, getRecoursePreview, simulateDispute } from '../lib/api';

export default function DisputeCenter() {
  const [disputes, setDisputes] = useState([]);
  const [selectedDisputeId, setSelectedDisputeId] = useState(null);
  const [evidenceBundle, setEvidenceBundle] = useState(null);
  const [recoursePreview, setRecoursePreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchDisputes = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listDisputes();
      setDisputes(data);
      if (data.length > 0 && !selectedDisputeId) {
        setSelectedDisputeId(data[0].dispute_id);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDisputes();
  }, []);

  useEffect(() => {
    if (!selectedDisputeId) return;
    const loadDetails = async () => {
      setLoading(true);
      setError(null);
      try {
        const [bundle, recourse] = await Promise.all([
          getDisputeEvidenceBundle(selectedDisputeId),
          getRecoursePreview(selectedDisputeId),
        ]);
        setEvidenceBundle(bundle);
        setRecoursePreview(recourse);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    loadDetails();
  }, [selectedDisputeId]);

  const handleSync = async () => {
    setActionLoading(true);
    try {
      await syncDisputes();
      await fetchDisputes();
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSimulate = async () => {
    setActionLoading(true);
    try {
      await simulateDispute('PAYPAL_TX_GITHUB_101', 45.0, 'UNAUTHORIZED_AGENT_TRANSACTION');
      await fetchDisputes();
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <Scale className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-base text-[#001c3f]">Dispute Evidence & Protection Recourse Center</h3>
            <p className="text-xs text-slate-500">Automated evidence bundle compilation for PayPal Agentic Commerce disputes</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleSync}
            disabled={actionLoading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${actionLoading ? 'animate-spin' : ''}`} />
            <span>Sync Disputes</span>
          </button>
          <button
            onClick={handleSimulate}
            disabled={actionLoading}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-[#0070ba] hover:bg-[#005ea6] text-white text-xs font-semibold shadow transition disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" />
            <span>Simulate Dispute</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/50 space-y-3">
          <span className="text-xs font-bold text-[#001c3f] block border-b border-slate-200 pb-2">
            Disputed Transactions
          </span>

          {disputes.length === 0 ? (
            <p className="text-xs text-slate-400 py-4 text-center">No active disputes recorded. Click "Simulate Dispute" to test.</p>
          ) : (
            <div className="space-y-2">
              {disputes.map((d) => (
                <div
                  key={d.dispute_id}
                  onClick={() => setSelectedDisputeId(d.dispute_id)}
                  className={`p-3 rounded-xl border cursor-pointer transition ${
                    selectedDisputeId === d.dispute_id
                      ? 'bg-white border-[#0070ba] shadow-xs ring-1 ring-[#0070ba]'
                      : 'bg-white/80 border-slate-200 hover:bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-slate-800">{d.dispute_id}</span>
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
                      {d.status}
                    </span>
                  </div>
                  <div className="text-[11px] text-slate-500 mt-1 flex justify-between">
                    <span>{d.reason}</span>
                    <span className="font-bold text-slate-800">${d.amount.toFixed(2)}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-4">
          {recoursePreview && (
            <div className="border border-slate-200 rounded-xl p-4 bg-slate-50/70">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2 mb-3">
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  <span className="text-xs font-bold text-[#001c3f]">Recourse Eligibility & Protection Readiness</span>
                </div>
                <span className="text-xs font-extrabold font-mono text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded-full">
                  {recoursePreview.readiness_percentage}% Readiness Score
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mb-3">
                {recoursePreview.checklist.map((item, idx) => (
                  <div key={idx} className="bg-white p-2.5 rounded-lg border border-slate-200 flex items-start space-x-2">
                    {item.satisfied ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
                    )}
                    <div>
                      <span className="text-xs font-bold text-slate-800 block">{item.rule}</span>
                      <p className="text-[11px] text-slate-500 leading-snug">{item.details}</p>
                    </div>
                  </div>
                ))}
              </div>

              <div className="p-3 bg-blue-50/70 border border-blue-200 rounded-lg text-xs text-slate-700 leading-relaxed">
                <span className="font-bold text-[#0070ba] block mb-0.5">Policy Assessment Analysis:</span>
                {recoursePreview.advisory_explanation}
              </div>
            </div>
          )}

          {evidenceBundle && (
            <div className="border border-slate-200 rounded-xl p-4 bg-white space-y-3">
              <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                <div className="flex items-center space-x-2">
                  <FileText className="w-4 h-4 text-[#0070ba]" />
                  <span className="text-xs font-bold text-[#001c3f]">Cryptographic Evidence Packet</span>
                </div>
                <span className="text-[10px] font-mono text-slate-400">
                  Assembled: {new Date(evidenceBundle.assembled_at).toLocaleTimeString()}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block font-sans">Mandate</span>
                  <span className="font-bold truncate block">{evidenceBundle.mandate_id}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block font-sans">Order ID</span>
                  <span className="font-bold truncate block">{evidenceBundle.order_id || 'N/A'}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block font-sans">PayPal Order Ref</span>
                  <span className="font-bold truncate block">{evidenceBundle.paypal_order_id || 'N/A'}</span>
                </div>
                <div className="bg-slate-50 p-2 rounded border border-slate-200">
                  <span className="text-[10px] text-slate-400 block font-sans">Chain Verified</span>
                  <span className="font-bold text-emerald-600 block">
                    {evidenceBundle.chain_integrity_valid ? 'VALID' : 'TAMPERED'}
                  </span>
                </div>
              </div>

              {evidenceBundle.mandate_signature && (
                <div className="p-2.5 rounded bg-slate-50 border border-slate-200 text-xs">
                  <span className="text-[10px] text-slate-500 font-bold block uppercase tracking-wide">
                    Cryptographic Passkey Token (FIDO2 / Ed25519)
                  </span>
                  <span className="font-mono text-[11px] text-slate-700 break-all">
                    {evidenceBundle.mandate_signature}
                  </span>
                </div>
              )}

              {evidenceBundle.audit_trail && evidenceBundle.audit_trail.length > 0 && (
                <div className="space-y-1.5 pt-1">
                  <span className="text-xs font-bold text-slate-700 block">
                    Tamper-Evident SHA-256 Event Chain ({evidenceBundle.audit_trail.length} blocks)
                  </span>
                  <div className="max-h-40 overflow-y-auto space-y-1 pr-1 font-mono text-[11px]">
                    {evidenceBundle.audit_trail.map((ev) => (
                      <div key={ev.id} className="p-2 bg-slate-50 rounded border border-slate-200 flex justify-between items-center">
                        <div className="truncate mr-2">
                          <span className="font-bold text-[#0070ba] mr-2">{ev.event_type}</span>
                          <span className="text-slate-400 text-[10px]">Hash: {ev.current_hash.substring(0, 16)}...</span>
                        </div>
                        <span className="text-[10px] text-slate-400 flex-shrink-0">
                          {new Date(ev.created_at).toLocaleTimeString()}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!evidenceBundle && !loading && (
            <div className="p-12 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
              Select a dispute or click "Simulate Dispute" to view the compiled cryptographic evidence packet.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
