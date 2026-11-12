import React, { useState } from 'react';
import { ShieldAlert, Play, CheckCircle2, XCircle, Activity, Cpu, Layers } from 'lucide-react';
import { runRedTeamSuite } from '../lib/api';

export default function RedTeamDashboard() {
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleRunSuite = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await runRedTeamSuite();
      setReport(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-slate-100 pb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-base text-[#001c3f]">Mandate Adversarial Red Team Harness</h3>
            <p className="text-xs text-slate-500">Automated security stress testing against prompt injection and rule bypass</p>
          </div>
        </div>
        <button
          onClick={handleRunSuite}
          disabled={loading}
          className="flex items-center justify-center space-x-2 px-4 py-2.5 bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold rounded-xl shadow-sm transition disabled:opacity-50"
        >
          <Play className="w-3.5 h-3.5" />
          <span>{loading ? 'Executing Adversarial Attacks...' : 'Run Red Team Suite'}</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
          {error}
        </div>
      )}

      {report && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <span className="text-[11px] text-slate-500 font-medium block">Defense Enforcement Rate</span>
              <span className="text-xl font-extrabold font-mono text-emerald-600">
                {report.defense_rate}%
              </span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <span className="text-[11px] text-slate-500 font-medium block">Attacks Neutralized</span>
              <span className="text-xl font-extrabold font-mono text-slate-800">
                {report.defended_attacks} / {report.total_attacks}
              </span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <span className="text-[11px] text-slate-500 font-medium block">Average Latency</span>
              <span className="text-xl font-extrabold font-mono text-[#0070ba]">
                {report.avg_latency_ms} ms
              </span>
            </div>
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
              <span className="text-[11px] text-slate-500 font-medium block">p95 Evaluation Latency</span>
              <span className="text-xl font-extrabold font-mono text-[#001c3f]">
                {report.p95_latency_ms} ms
              </span>
            </div>
          </div>

          <div className="border border-slate-200 rounded-xl overflow-hidden">
            <div className="bg-slate-50 px-4 py-2.5 border-b border-slate-200 text-xs font-bold text-[#001c3f] flex items-center justify-between">
              <span>Evaluated Attack Vectors & Defenses</span>
              <span className="font-mono text-slate-500 text-[11px]">Enforcement Layer Isolation</span>
            </div>

            <div className="divide-y divide-slate-100">
              {report.results.map((att) => (
                <div key={att.vector_id} className="p-3.5 hover:bg-slate-50/60 transition flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div className="space-y-1 max-w-xl">
                    <div className="flex items-center space-x-2">
                      <span className="font-mono text-xs font-bold text-slate-800">{att.name}</span>
                      <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded font-mono">
                        {att.category}
                      </span>
                    </div>
                    <p className="text-xs text-slate-500 leading-snug">{att.details}</p>
                  </div>

                  <div className="flex items-center space-x-3 self-end sm:self-center">
                    <span className="text-[11px] font-mono text-slate-500 hidden md:block">
                      {att.enforcing_layer}
                    </span>
                    <span className="text-[11px] font-mono text-slate-400">
                      {att.latency_ms}ms
                    </span>
                    <span
                      className={`inline-flex items-center space-x-1 text-[11px] font-bold px-2.5 py-1 rounded-full ${
                        att.defended
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-rose-100 text-rose-800'
                      }`}
                    >
                      {att.defended ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>NEUTRALIZED</span>
                        </>
                      ) : (
                        <>
                          <XCircle className="w-3.5 h-3.5" />
                          <span>BYPASSED</span>
                        </>
                      )}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {!report && !error && (
        <div className="p-8 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl space-y-2">
          <p>The Red Team harness fires adversarial vectors across prompt injection, delegation expansion, merchant spoofing, destination injection, and cryptographic tampering.</p>
          <p>Click "Run Red Team Suite" to evaluate defensive enforcement live.</p>
        </div>
      )}
    </div>
  );
}
