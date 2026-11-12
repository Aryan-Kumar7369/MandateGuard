import React, { useState } from 'react';
import { GitFork, Layers, ChevronRight, CheckCircle2, ShieldAlert } from 'lucide-react';
import { getDelegationTree } from '../lib/api';

function TreeNode({ node, depth = 0 }) {
  return (
    <div className={`space-y-2 ${depth > 0 ? 'ml-6 border-l-2 border-[#0070ba]/30 pl-4 mt-2' : ''}`}>
      <div className="bg-white border border-slate-200 rounded-xl p-3 shadow-xs hover:border-[#0070ba]/40 transition">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-bold text-[#001c3f]">
              {depth === 0 ? 'Root Mandate:' : 'Sub-Mandate:'} {node.mandate_id}
            </span>
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                node.is_revoked
                  ? 'bg-rose-100 text-rose-700 border border-rose-200'
                  : 'bg-emerald-100 text-emerald-700 border border-emerald-200'
              }`}
            >
              {node.is_revoked ? 'REVOKED' : 'ACTIVE'}
            </span>
          </div>
          <span className="text-xs font-mono font-bold text-[#0070ba]">
            ${node.cumulative_budget.toFixed(2)}
          </span>
        </div>

        <div className="text-[11px] text-slate-500 mt-2 flex flex-wrap items-center justify-between gap-1">
          <span>Owner: <strong className="text-slate-700 font-mono">{node.user_id}</strong></span>
          <span>
            Categories:{' '}
            <strong className="text-slate-700">
              {node.allowed_categories && node.allowed_categories.length > 0
                ? node.allowed_categories.join(', ')
                : 'All'}
            </strong>
          </span>
        </div>
      </div>

      {node.children && node.children.length > 0 && (
        <div className="space-y-2">
          {node.children.map((child) => (
            <TreeNode key={child.mandate_id} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function DelegationChainTree({ defaultRootId = 'm_corp_root' }) {
  const [rootId, setRootId] = useState(defaultRootId);
  const [treeData, setTreeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTree = async () => {
    if (!rootId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getDelegationTree(rootId.trim());
      setTreeData(data);
    } catch (err) {
      setError(err.message);
      setTreeData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
            <GitFork className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-base text-[#001c3f]">Agent Delegation & Narrowing Map</h3>
            <p className="text-xs text-slate-500">Multi-agent authority delegation with mathematical narrowing bounds</p>
          </div>
        </div>
      </div>

      <div className="flex space-x-2 mb-4">
        <input
          type="text"
          className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-mono text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-[#0070ba]"
          placeholder="Root Mandate ID (e.g. m_corp_root)"
          value={rootId}
          onChange={(e) => setRootId(e.target.value)}
        />
        <button
          onClick={fetchTree}
          disabled={loading || !rootId.trim()}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold rounded-xl transition disabled:opacity-50"
        >
          {loading ? 'Building Tree...' : 'Render Hierarchy'}
        </button>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
          {error}
        </div>
      )}

      {treeData && (
        <div className="bg-slate-50/70 border border-slate-200 rounded-xl p-4">
          <TreeNode node={treeData} depth={0} />
        </div>
      )}

      {!treeData && !error && (
        <div className="p-6 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-xl">
          Enter a root mandate identifier and click "Render Hierarchy" to inspect child agent delegation limits.
        </div>
      )}
    </div>
  );
}
