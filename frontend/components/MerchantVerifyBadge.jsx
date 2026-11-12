import React, { useState } from 'react';
import { Store, ShieldCheck, CheckCircle2, XCircle, Lock, ArrowRight } from 'lucide-react';
import { verifyMerchantSignal } from '../lib/api';

export default function MerchantVerifyBadge({ defaultMandateId = 'm_corp_devops' }) {
  const [mandateId, setMandateId] = useState(defaultMandateId);
  const [amount, setAmount] = useState(45);
  const [merchant, setMerchant] = useState('GitHub');
  const [category, setCategory] = useState('software');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleVerifySignal = async () => {
    if (!mandateId.trim()) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await verifyMerchantSignal({
        mandate_id: mandateId.trim(),
        amount: parseFloat(amount) || 0,
        merchant: merchant.trim(),
        category: category.trim(),
      });
      setResult(data);
    } catch (err) {
      setResult({
        is_valid: false,
        badge_status: 'ERROR',
        message: err.message,
        remaining_budget: 0,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <Store className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-base text-[#001c3f]">Merchant Verification Signal</h3>
            <p className="text-xs text-slate-500">Privacy-preserving pre-checkout verification badge</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
        <div>
          <label className="text-xs font-semibold text-slate-600 block mb-1">Mandate Identifier</label>
          <input
            type="text"
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
            placeholder="e.g. m_corp_devops"
            value={mandateId}
            onChange={(e) => setMandateId(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs font-semibold text-slate-600 block mb-1">Transaction Value ($)</label>
          <input
            type="number"
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
        <div>
          <label className="text-xs font-semibold text-slate-600 block mb-1">Merchant Storefront</label>
          <input
            type="text"
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
            value={merchant}
            onChange={(e) => setMerchant(e.target.value)}
          />
        </div>
        <div>
          <label className="text-xs font-semibold text-slate-600 block mb-1">Product Category</label>
          <input
            type="text"
            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs text-slate-800 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
          />
        </div>
      </div>

      <button
        onClick={handleVerifySignal}
        disabled={loading || !mandateId.trim()}
        className="w-full flex items-center justify-center space-x-2 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl shadow-sm transition disabled:opacity-50"
      >
        <span>{loading ? 'Evaluating Merchant Rail...' : 'Query Merchant Verification Signal'}</span>
        <ArrowRight className="w-3.5 h-3.5" />
      </button>

      {result && (
        <div
          className={`mt-4 p-4 rounded-xl border ${
            result.is_valid
              ? 'bg-emerald-50/80 border-emerald-300 text-emerald-900'
              : 'bg-rose-50/80 border-rose-300 text-rose-900'
          }`}
        >
          <div className="flex items-center justify-between pb-2 border-b border-current/10">
            <div className="flex items-center space-x-2">
              {result.is_valid ? (
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              ) : (
                <XCircle className="w-5 h-5 text-rose-600" />
              )}
              <span className="font-extrabold text-sm tracking-wide font-mono">
                {result.badge_status}
              </span>
            </div>
            <span className="text-xs font-mono font-bold">
              Remaining: ${Number(result.remaining_budget || 0).toFixed(2)}
            </span>
          </div>

          <p className="text-xs mt-2 leading-relaxed opacity-90">{result.message}</p>

          <div className="mt-3 pt-2 border-t border-current/10 flex items-center justify-between text-[11px] font-mono">
            <span className="flex items-center space-x-1">
              <Lock className="w-3 h-3" />
              <span>Token: {result.verification_token || 'N/A'}</span>
            </span>
            <span className="font-bold">Zero Financial Data Exposed</span>
          </div>
        </div>
      )}
    </div>
  );
}
