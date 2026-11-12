import React from 'react';
import { Activity, ShieldAlert, CheckCircle2, XCircle, AlertTriangle, Radio, Zap } from 'lucide-react';

export default function LiveActivityFeed({ events, mandates, onRevoke }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-rose-50 text-rose-600 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#001c3f]">Emergency Kill-Switch</h3>
              <p className="text-xs text-slate-500">Immediate, zero-latency authorization revocation</p>
            </div>
          </div>
          <span className="text-[11px] font-semibold bg-rose-50 text-rose-700 px-2 py-0.5 rounded-full border border-rose-100">
            Kill-Switch
          </span>
        </div>

        <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
          {Object.keys(mandates).length === 0 ? (
            <p className="text-xs text-slate-400 py-6 text-center italic">
              No mandates registered in active session stream. Seed demo data or create a mandate.
            </p>
          ) : (
            Object.entries(mandates).map(([id, state]) => (
              <div
                key={id}
                className="p-3 rounded-xl border border-slate-200 bg-slate-50/70 hover:bg-slate-50 transition flex items-center justify-between"
              >
                <div className="space-y-0.5">
                  <span className="text-xs font-mono font-bold text-slate-800 block truncate max-w-[140px] sm:max-w-[180px]">
                    {id}
                  </span>
                  <span
                    className={`inline-block text-[10px] font-bold px-2 py-0.5 rounded-full ${
                      state.is_revoked
                        ? 'bg-rose-100 text-rose-700'
                        : 'bg-emerald-100 text-emerald-700'
                    }`}
                  >
                    {state.is_revoked ? 'REVOKED' : 'ACTIVE'}
                  </span>
                </div>

                {!state.is_revoked ? (
                  <button
                    onClick={() => onRevoke(id)}
                    className="flex items-center space-x-1 px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold shadow-xs transition"
                  >
                    <Zap className="w-3 h-3" />
                    <span>REVOKE</span>
                  </button>
                ) : (
                  <span className="text-[11px] font-mono text-rose-600 font-bold">LOCKED</span>
                )}
              </div>
            ))
          )}
        </div>
      </div>

      <div className="lg:col-span-2 bg-white border border-slate-200 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-lg bg-blue-50 text-[#0070ba] flex items-center justify-center">
              <Activity className="w-4 h-4" />
            </div>
            <div>
              <h3 className="font-bold text-base text-[#001c3f]">Live Agent Pre-Flight Stream</h3>
              <p className="text-xs text-slate-500">Autonomous agent payment evaluation events via Server-Sent Events</p>
            </div>
          </div>
          <span className="flex items-center space-x-1.5 text-xs text-emerald-600 font-semibold bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
            <Radio className="w-3.5 h-3.5 animate-pulse text-emerald-600" />
            <span>SSE Active</span>
          </span>
        </div>

        <div className="space-y-2.5 max-h-[460px] overflow-y-auto pr-1">
          {events.length === 0 ? (
            <p className="text-xs text-slate-400 py-12 text-center italic">
              Listening for agent pre-flight decisions and checkout authorizations...
            </p>
          ) : (
            events.map((evt) => (
              <div
                key={evt.id}
                className="p-3.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50/80 transition space-y-1.5"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-mono font-bold text-[#0070ba]">{evt.type}</span>
                  <span className="text-slate-400 font-mono text-[11px]">{evt.timestamp}</span>
                </div>

                {evt.type === 'PRE_FLIGHT_EVALUATED' && (
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono text-slate-700">
                        Mandate: <strong>{evt.data.mandate_id}</strong>
                      </span>
                      <span
                        className={`inline-flex items-center space-x-1 text-xs font-extrabold px-2.5 py-0.5 rounded-full ${
                          evt.data.decision === 'ALLOW'
                            ? 'bg-emerald-100 text-emerald-800'
                            : evt.data.decision === 'BLOCK'
                            ? 'bg-rose-100 text-rose-800'
                            : 'bg-amber-100 text-amber-800'
                        }`}
                      >
                        {evt.data.decision === 'ALLOW' && <CheckCircle2 className="w-3.5 h-3.5" />}
                        {evt.data.decision === 'BLOCK' && <XCircle className="w-3.5 h-3.5" />}
                        {evt.data.decision === 'ASK_HUMAN' && <AlertTriangle className="w-3.5 h-3.5" />}
                        <span>{evt.data.decision}</span>
                      </span>
                    </div>
                    <p className="text-xs text-slate-600 mt-1 leading-snug">{evt.data.reason}</p>
                  </div>
                )}

                {evt.type === 'MANDATE_REVOKED' && (
                  <div className="text-xs font-bold text-rose-700 flex items-center space-x-1.5">
                    <XCircle className="w-4 h-4 text-rose-600" />
                    <span>MANDATE REVOKED: {evt.data.mandate_id}</span>
                  </div>
                )}

                {evt.type === 'MANDATE_CREATED' && (
                  <div className="text-xs font-bold text-emerald-700 flex items-center space-x-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>MANDATE REGISTERED: {evt.data.mandate_id}</span>
                  </div>
                )}

                {evt.type === 'DISPUTE_CREATED' && (
                  <div className="text-xs font-bold text-amber-700 flex items-center space-x-1.5">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span>DISPUTE FILED: {evt.data.dispute_id} ({evt.data.reason})</span>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
