import React, { useState } from "react";

export default function MerchantVerifyBadge({ apiBase = "http://localhost:8000/api/v1" }) {
  const [mandateId, setMandateId] = useState("");
  const [amount, setAmount] = useState(50);
  const [merchant, setMerchant] = useState("GitHub");
  const [category, setCategory] = useState("software");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleVerifySignal = async () => {
    if (!mandateId.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await fetch(`${apiBase}/merchant/verify-signal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          mandate_id: mandateId.trim(),
          amount: parseFloat(amount) || 0,
          merchant: merchant.trim(),
          category: category.trim()
        })
      });
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-xl font-bold text-sky-400">Merchant Mandate Verification Signal</h3>
          <p className="text-xs text-slate-400">Merchant pre-checkout verification badge & authority check</p>
        </div>
        <span className="text-xs bg-emerald-500/20 text-emerald-300 px-2.5 py-1 rounded-full font-mono">
          Day 8 Core
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <label className="text-slate-400 font-medium">Mandate ID</label>
          <input
            type="text"
            className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 mt-1 text-white font-mono focus:outline-none focus:border-sky-500"
            placeholder="e.g. m_corp_root"
            value={mandateId}
            onChange={(e) => setMandateId(e.target.value)}
          />
        </div>
        <div>
          <label className="text-slate-400 font-medium">Cart Amount ($)</label>
          <input
            type="number"
            className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 mt-1 text-white font-mono focus:outline-none focus:border-sky-500"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        <div>
          <label className="text-slate-400 font-medium">Merchant Name</label>
          <input
            type="text"
            className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 mt-1 text-white focus:outline-none focus:border-sky-500"
            placeholder="e.g. GitHub"
            value={merchant}
            onChange={(e) => setMerchant(e.target.value)}
          />
        </div>
        <div>
          <label className="text-slate-400 font-medium">Category</label>
          <input
            type="text"
            className="w-full bg-slate-950 border border-slate-700 rounded px-3 py-2 mt-1 text-white focus:outline-none focus:border-sky-500"
            placeholder="e.g. software"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
        </div>
      </div>

      <button
        onClick={handleVerifySignal}
        disabled={loading || !mandateId.trim()}
        className="w-full py-2.5 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-800 rounded-lg text-sm font-bold transition-all shadow-md"
      >
        {loading ? "Checking Merchant Signal..." : "Verify Mandate Signal"}
      </button>

      {result && (
        <div className={`p-4 rounded-xl border mt-4 ${
          result.is_valid
            ? "bg-emerald-950/40 border-emerald-500/50 text-emerald-200"
            : "bg-rose-950/40 border-rose-500/50 text-rose-200"
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className={`h-3 w-3 rounded-full ${result.is_valid ? "bg-emerald-400 animate-pulse" : "bg-rose-500"}`} />
              <span className="font-extrabold text-sm tracking-wide font-mono">
                {result.badge_status}
              </span>
            </div>
            <span className="text-xs bg-slate-900 border border-slate-700 px-2 py-1 rounded text-slate-300 font-mono">
              Remaining: ${result.remaining_budget.toFixed(2)}
            </span>
          </div>

          <p className="text-xs mt-2 leading-relaxed opacity-90">{result.message}</p>

          {result.is_valid && (
            <div className="mt-3 pt-2 border-t border-emerald-500/30 flex items-center justify-between text-[11px] text-emerald-300 font-mono">
              <span>✔ Mandatory Signatures Intact</span>
              <span>MandateGuard Verified Badge</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}