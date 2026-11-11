import React, { useState } from 'react';

function TreeNode({ node, depth = 0 }) {
  return (
    <div className={`space-y-2 ${depth > 0 ? 'ml-6 border-l-2 border-indigo-500/40 pl-4 mt-3' : ''}`}>
      <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-mono font-bold text-indigo-400">
              {depth === 0 ? '👑 Root Mandate:' : '↳ Sub-Mandate:'} {node.mandate_id}
            </span>
            <span className={`text-[10px] px-2 py-0.5 rounded font-mono ${
              node.is_revoked ? 'bg-rose-500/20 text-rose-300' : 'bg-emerald-500/20 text-emerald-300'
            }`}>
              {node.is_revoked ? 'REVOKED' : 'ACTIVE'}
            </span>
          </div>
          <span className="text-xs font-mono text-slate-300 font-bold">
            ${node.cumulative_budget.toFixed(2)}
          </span>
        </div>

        <div className="text-[11px] text-slate-400 flex justify-between font-mono">
          <span>Owner: {node.user_id}</span>
          <span>Categories: {node.allowed_categories ? node.allowed_categories.join(', ') : 'All'}</span>
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

export function DelegationChainTree({ apiBase = 'http://localhost:8000/api/v1' }) {
  const [rootId, setRootId] = useState('');
  const [treeData, setTreeData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTree = async () => {
    if (!rootId.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`${apiBase}/delegations/tree/${encodeURIComponent(rootId.trim())}`);
      if (!res.ok) throw new Error(`Delegation tree for '${rootId}' not found.`);
      const data = await res.json();
      setTreeData(data);
    } catch (err) {
      setError(err.message);
      setTreeData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 text-white space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="text-xl font-bold text-sky-400">Hierarchical Delegation Chain Tree</h3>
          <p className="text-xs text-slate-400">Multi-hop sub-mandate delegation & authority narrowing map</p>
        </div>
        <span className="text-xs bg-purple-500/20 text-purple-300 px-2.5 py-1 rounded-full font-mono">
          Day 14 Tree
        </span>
      </div>

      <div className="flex space-x-2">
        <input
          type="text"
          className="flex-1 bg-slate-950 border border-slate-700 rounded px-3 py-2 text-xs font-mono text-white focus:outline-none focus:border-sky-500"
          placeholder="Root Mandate ID (e.g. m_corp_root)"
          value={rootId}
          onChange={(e) => setRootId(e.target.value)}
        />
        <button
          onClick={fetchTree}
          disabled={loading || !rootId.trim()}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:bg-slate-800 rounded text-xs font-bold transition"
        >
          {loading ? 'Building Tree...' : 'Render Tree'}
        </button>
      </div>

      {error && (
        <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 text-xs p-3 rounded-lg">
          {error}
        </div>
      )}

      {treeData && (
        <div className="pt-2">
          <TreeNode node={treeData} depth={0} />
        </div>
      )}
    </div>
  );
}

export default DelegationChainTree;