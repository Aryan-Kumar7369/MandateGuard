import React, { useState } from 'react';
import { FileText, Sliders, CheckCircle2, RotateCcw, ArrowRight } from 'lucide-react';
import { parsePromptToMandate, createMandate } from '../lib/api';

export default function MandateReviewCard({ onMandateCreated }) {
  const [prompt, setPrompt] = useState('');
  const [parsedRules, setParsedRules] = useState(null);
  const [loading, setLoading] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [createdMandateId, setCreatedMandateId] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

  const samplePrompts = [
    'Allow DevOps agent to spend up to $300 on software from GitHub or AWS with $50 approval threshold expiring in 7 days',
    'Permit shopping assistant to buy electronics under $150 from Amazon for US delivery',
    'Authorize travel agent to spend up to $800 on flights with $200 threshold expiring tomorrow'
  ];

  const handleParsePrompt = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setErrorMsg(null);
    setConfirmed(false);
    setCreatedMandateId(null);
    try {
      const data = await parsePromptToMandate(prompt);
      setParsedRules(data.proposed_rules);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAndCreate = async () => {
    if (!parsedRules) return;
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await createMandate({
        user_id: 'executive_controller@paypal.com',
        rules: parsedRules,
      });
      setCreatedMandateId(data.id);
      setConfirmed(true);
      if (onMandateCreated) onMandateCreated(data.id);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-blue-50 text-[#0070ba] flex items-center justify-center">
            <FileText className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-base text-[#001c3f]">Natural Language Mandate Compiler</h3>
            <p className="text-xs text-slate-500">Translate spending intentions into cryptographically verifiable schemas</p>
          </div>
        </div>
      </div>

      <div className="space-y-3">
        <label className="text-xs font-semibold text-slate-700 block">
          Enter Spending Authority Instruction
        </label>
        <textarea
          className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs sm:text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0070ba] focus:bg-white transition"
          rows={3}
          placeholder="e.g., Allow DevOps agent to spend up to $400 on cloud services with $100 single transaction threshold..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
        />

        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-slate-500 font-medium">Quick Suggestions:</span>
          {samplePrompts.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setPrompt(sample)}
              className="text-[11px] bg-slate-100 hover:bg-slate-200 text-slate-600 px-2 py-0.5 rounded-md truncate max-w-xs transition"
            >
              Suggestion {idx + 1}
            </button>
          ))}
        </div>

        <button
          onClick={handleParsePrompt}
          disabled={loading || !prompt.trim()}
          className="w-full flex items-center justify-center space-x-2 py-2.5 bg-[#0070ba] hover:bg-[#005ea6] text-white text-xs font-bold rounded-xl shadow-sm transition disabled:opacity-50"
        >
          <span>{loading ? 'Compiling Rules...' : 'Compile Intent into Structured Mandate'}</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>

      {errorMsg && (
        <div className="mt-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
          {errorMsg}
        </div>
      )}

      {parsedRules && (
        <div className="mt-5 border border-slate-200 rounded-xl p-4 bg-slate-50/70 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-200 pb-2">
            <div className="flex items-center space-x-1.5">
              <Sliders className="w-4 h-4 text-[#0070ba]" />
              <span className="text-xs font-bold text-[#001c3f]">Human Review & Configuration Verification</span>
            </div>
            <span className="text-[10px] font-bold bg-amber-100 text-amber-800 px-2 py-0.5 rounded">
              Pending Authorization
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Cumulative Budget ($)</label>
              <input
                type="number"
                className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 font-mono text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
                value={parsedRules.cumulative_budget}
                onChange={(e) => setParsedRules({ ...parsedRules, cumulative_budget: parseFloat(e.target.value) || 0 })}
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Approval Threshold ($)</label>
              <input
                type="number"
                className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 font-mono text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
                value={parsedRules.approval_threshold}
                onChange={(e) => setParsedRules({ ...parsedRules, approval_threshold: parseFloat(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-600 font-semibold block mb-1">Authorized Categories</label>
            <input
              type="text"
              className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
              value={parsedRules.allowed_categories ? parsedRules.allowed_categories.join(', ') : ''}
              onChange={(e) => setParsedRules({
                ...parsedRules,
                allowed_categories: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
              })}
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Permitted Merchants</label>
              <input
                type="text"
                className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
                value={parsedRules.merchant_constraints?.allow ? parsedRules.merchant_constraints.allow.join(', ') : ''}
                onChange={(e) => setParsedRules({
                  ...parsedRules,
                  merchant_constraints: {
                    ...parsedRules.merchant_constraints,
                    allow: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  },
                })}
              />
            </div>
            <div>
              <label className="text-slate-600 font-semibold block mb-1">Blocked Merchants</label>
              <input
                type="text"
                className="w-full bg-white border border-slate-200 rounded-lg px-3 py-1.5 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
                value={parsedRules.merchant_constraints?.deny ? parsedRules.merchant_constraints.deny.join(', ') : ''}
                onChange={(e) => setParsedRules({
                  ...parsedRules,
                  merchant_constraints: {
                    ...parsedRules.merchant_constraints,
                    deny: e.target.value.split(',').map((s) => s.trim()).filter(Boolean),
                  },
                })}
              />
            </div>
          </div>

          {confirmed && (
            <div className="bg-emerald-50 border border-emerald-200 p-3 rounded-xl flex items-center justify-between text-xs text-emerald-800">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span className="font-semibold">Mandate successfully created and saved</span>
              </div>
              <span className="font-mono text-emerald-700 font-bold">{createdMandateId}</span>
            </div>
          )}

          <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-200">
            <button
              onClick={() => { setParsedRules(null); setConfirmed(false); }}
              className="flex items-center space-x-1 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-medium text-slate-600 hover:bg-slate-100 transition"
            >
              <RotateCcw className="w-3 h-3" />
              <span>Discard</span>
            </button>
            <button
              onClick={handleConfirmAndCreate}
              disabled={loading || confirmed}
              className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold transition disabled:opacity-50"
            >
              {confirmed ? 'Mandate Saved' : 'Confirm & Persist Mandate'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
