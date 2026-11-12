import React, { useState } from 'react';
import { Wallet, Search, ArrowUpRight, AlertCircle } from 'lucide-react';
import { getMandateBudget } from '../lib/api';

export default function BudgetGauge({ defaultMandateId = 'm_corp_root' }) {
  const [mandateId, setMandateId] = useState(defaultMandateId);
  const [budgetInfo, setBudgetInfo] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchBudget = async () => {
    if (!mandateId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getMandateBudget(mandateId.trim());
      setBudgetInfo(data);
    } catch (err) {
      setError(err.message);
      setBudgetInfo(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-50 text-[#0070ba] flex items-center justify-center">
            <Wallet className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-base text-[#001c3f]">Agent Spend & Budget Utilization</h3>
            <p className="text-xs text-slate-500">Real-time spending exhaustion and velocity monitor</p>
          </div>
        </div>
        <span className="text-[11px] font-semibold bg-blue-50 text-[#0070ba] px-2.5 py-1 rounded-full border border-blue-100">
          Component 6
        </span>
      </div>

      <div className="flex space-x-2 mb-4">
        <div className="relative flex-1">
          <input
            type="text"
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
            placeholder="Enter Mandate ID (e.g. m_corp_root)"
            value={mandateId}
            onChange={(e) => setMandateId(e.target.value)}
          />
        </div>
        <button
          onClick={fetchBudget}
          disabled={loading || !mandateId.trim()}
          className="flex items-center space-x-1.5 px-4 py-2 bg-[#0070ba] hover:bg-[#005ea6] text-white text-xs font-bold rounded-xl transition disabled:opacity-50"
        >
          <Search className="w-3.5 h-3.5" />
          <span>{loading ? 'Inspecting...' : 'Inspect Gauge'}</span>
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {budgetInfo && (
        <div className="space-y-4 pt-1">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-mono font-bold text-slate-700">{budgetInfo.mandate_id}</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                budgetInfo.is_revoked
                  ? 'bg-rose-100 text-rose-700 border border-rose-200'
                  : 'bg-emerald-100 text-emerald-700 border border-emerald-200'
              }`}>
                {budgetInfo.is_revoked ? 'REVOKED' : 'ACTIVE'}
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 my-3">
              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <span className="text-[11px] text-slate-500 block">Spent Amount</span>
                <span className="text-base font-bold font-mono text-slate-800">
                  ${budgetInfo.spent_amount.toFixed(2)}
                </span>
              </div>
              <div className="bg-white p-3 rounded-lg border border-slate-200">
                <span className="text-[11px] text-slate-500 block">Remaining Budget</span>
                <span className="text-base font-bold font-mono text-emerald-600">
                  ${budgetInfo.remaining_budget.toFixed(2)}
                </span>
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-slate-600 font-medium">
                <span>Budget Exhaustion</span>
                <span className="font-mono">{budgetInfo.usage_percentage}%</span>
              </div>
              <div className="w-full h-2.5 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    budgetInfo.usage_percentage > 85
                      ? 'bg-rose-500'
                      : budgetInfo.usage_percentage > 60
                      ? 'bg-amber-500'
                      : 'bg-[#0070ba]'
                  }`}
                  style={{ width: `${Math.min(budgetInfo.usage_percentage, 100)}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] text-slate-400 font-mono">
                <span>$0.00</span>
                <span>Cumulative: ${budgetInfo.cumulative_budget.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {!budgetInfo && !error && (
        <div className="p-6 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
          Enter a mandate ID above or click "Inspect Gauge" to view spending limits and usage metrics.
        </div>
      )}
    </div>
  );
}
