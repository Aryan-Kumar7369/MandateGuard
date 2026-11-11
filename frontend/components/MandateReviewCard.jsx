import React, { useState } from "react";

export default function MandateReviewCard({ apiBase = "http://localhost:8000/api/v1" }) {
  const [prompt, setPrompt] = useState("");
  const [parsedRules, setParsedRules] = useState(null);
  const [loading, setLoading] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [createdMandateId, setCreatedMandateId] = useState(null);

  const handleParsePrompt = async () => {
    setLoading(true);
    setConfirmed(false);
    setCreatedMandateId(null);
    try {
      const res = await fetch(`${apiBase}/mandates/parse-prompt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ prompt })
      });
      if (!res.ok) throw new Error("Failed to parse mandate prompt");
      const data = await res.json();
      setParsedRules(data.proposed_rules);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmAndCreate = async () => {
    if (!parsedRules) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/mandates/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: "user_human_reviewer",
          rules: parsedRules
        })
      });
      if (res.ok) {
        const data = await res.json();
        setCreatedMandateId(data.id);
        setConfirmed(true);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-bold text-sky-400">Natural Language Mandate Creation</h3>
        <span className="text-xs bg-sky-500/20 text-sky-300 px-2.5 py-1 rounded-full font-mono">
          Day 4 Core
        </span>
      </div>
      
      <textarea
        className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-sm focus:outline-none focus:border-sky-500"
        rows={3}
        placeholder="e.g., Allow DevOps agent to spend up to $500 on AWS or GitHub with $100 approval threshold..."
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />

      <button
        onClick={handleParsePrompt}
        disabled={loading || !prompt.trim()}
        className="px-4 py-2 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 rounded-lg text-sm font-semibold transition-colors"
      >
        {loading ? "Parsing Intent via LLM..." : "Parse Rules for Human Review"}
      </button>

      {parsedRules && (
        <div className="bg-slate-950 border border-slate-700 rounded-lg p-4 space-y-4 mt-4">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <span className="text-sm font-bold text-amber-400">Human Review & Confirmation Required</span>
            <span className="text-xs bg-amber-500/20 text-amber-300 px-2 py-0.5 rounded font-mono">
              Unconfirmed Draft
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium">Cumulative Budget ($)</label>
              <input
                type="number"
                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5 mt-1 text-white font-mono"
                value={parsedRules.cumulative_budget}
                onChange={(e) => setParsedRules({ ...parsedRules, cumulative_budget: parseFloat(e.target.value) || 0 })}
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Approval Threshold ($)</label>
              <input
                type="number"
                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5 mt-1 text-white font-mono"
                value={parsedRules.approval_threshold}
                onChange={(e) => setParsedRules({ ...parsedRules, approval_threshold: parseFloat(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div>
            <label className="text-xs text-slate-400 font-medium">Allowed Categories (comma separated)</label>
            <input
              type="text"
              className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5 mt-1 text-xs text-white"
              value={parsedRules.allowed_categories ? parsedRules.allowed_categories.join(", ") : ""}
              onChange={(e) => setParsedRules({ ...parsedRules, allowed_categories: e.target.value.split(",").map(s => s.trim()).filter(Boolean) })}
            />
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium">Allowed Merchants</label>
              <input
                type="text"
                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5 mt-1 text-xs text-white"
                value={parsedRules.merchant_constraints?.allow ? parsedRules.merchant_constraints.allow.join(", ") : ""}
                onChange={(e) => setParsedRules({
                  ...parsedRules,
                  merchant_constraints: {
                    ...parsedRules.merchant_constraints,
                    allow: e.target.value.split(",").map(s => s.trim()).filter(Boolean)
                  }
                })}
              />
            </div>
            <div>
              <label className="text-slate-400 font-medium">Denied Merchants</label>
              <input
                type="text"
                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1.5 mt-1 text-xs text-white"
                value={parsedRules.merchant_constraints?.deny ? parsedRules.merchant_constraints.deny.join(", ") : ""}
                onChange={(e) => setParsedRules({
                  ...parsedRules,
                  merchant_constraints: {
                    ...parsedRules.merchant_constraints,
                    deny: e.target.value.split(",").map(s => s.trim()).filter(Boolean)
                  }
                })}
              />
            </div>
          </div>

          {confirmed && (
            <div className="bg-emerald-950/50 border border-emerald-500/30 p-3 rounded-lg text-xs space-y-1">
              <div className="font-bold text-emerald-400">Mandate Confirmed & Created Successfully ✓</div>
              <div className="font-mono text-slate-300">Mandate ID: {createdMandateId}</div>
            </div>
          )}

          <div className="pt-2 flex items-center justify-end space-x-3">
            <button
              onClick={() => { setParsedRules(null); setConfirmed(false); }}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs rounded font-medium"
            >
              Discard
            </button>
            <button
              onClick={handleConfirmAndCreate}
              disabled={loading || confirmed}
              className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-xs font-bold rounded transition-colors"
            >
              {confirmed ? "Mandate Created ✓" : "Confirm & Save Mandate"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}