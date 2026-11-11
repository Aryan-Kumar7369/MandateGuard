import React, { useState } from 'react';

export function BudgetGauge({ apiBase = 'http://localhost:8000/api/v1' }) {
  const [mandateId, setMandateId] = useState('');
  const [budgetInfo, setBudgetInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBudget = async () => {
    if (!mandateId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/mandates/${encodeURIComponent(mandateId.trim())}/budget`);
      if (!res.ok) {
        throw new Error(`Mandate '${mandateId}' not found.`);
      }
      const data = await res.json();
      setBudgetInfo(data);
    } catch (err) {
      setError(err.message);
      setBudgetInfo(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-xl font-bold text-sky-400">Remaining Budget Visualizer</h3>
          <p className="text-xs text-slate-400">Real-time budget exhaustion tracking & velocity warning</p>
        </div>
        <span className="text-xs bg-indigo-500/20 text-indigo-300 px-2.5 py-1 rounded-full font-mono">
          Day 14 Core
        </span>
      </div>

      <div className="flex space-x-2">
        <input
          type="text"
          className="flex-1 bg-slate-950 border border-slate-700 rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-sky-500"
          placeholder="Enter Mandate ID (e.g. m_corp_root)"
          value={mandateId}
          onChange={(e) => setMandateId(e.target.value)}
        />
        <button
          onClick={fetchBudget}
          disabled={loading || !mandateId.trim()}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 rounded text-xs font-bold transition"
        >
          {loading ? 'Fetching...' : 'Inspect Gauge'}
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs p-3 rounded-lg">
          {error}
        </div>
      )}

      {budgetInfo && (
        <div className="bg-slate-950 border border-slate-800 rounded-xl p-4 space-y-4">
          <div className="flex justify-between items-baseline">
            <span className="text-xs text-slate-400 font-mono">{budgetInfo.mandate_id}</span>
            <span className={`text-xs px-2 py-0.5 rounded font-mono font-bold ${
              budgetInfo.is_revoked ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'
            }`}>
              {budgetInfo.is_revoked ? 'REVOKED' : 'ACTIVE'}
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400">Spent: ${budgetInfo.spent_amount.toFixed(2)}</span>
              <span className="font-bold text-sky-400">Total: ${budgetInfo.cumulative_budget.toFixed(2)}</span>
            </div>
            
            <div className="w-full h-3 bg-slate-800 rounded-full overflow-hidden p-0.5">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  budgetInfo.usage_percentage > 85 ? 'bg-rose-500' : budgetInfo.usage_percentage > 60 ? 'bg-amber-500' : 'bg-emerald-400'
                }`}
                style={{ width: `${budgetInfo.usage_percentage}%` }}
              />
            </div>

            <div className="flex justify-between text-[11px] font-mono text-slate-400 pt-1">
              <span>Used: {budgetInfo.usage_percentage}%</span>
              <span className="text-emerald-400 font-bold">Remaining: ${budgetInfo.remaining_budget.toFixed(2)}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default BudgetGauge;