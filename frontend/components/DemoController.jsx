import React, { useState } from 'react';
import { Play, Database, ShieldAlert, Zap, CheckCircle2 } from 'lucide-react';
import { seedDemoEnvironment, triggerDemoAct1, triggerDemoAct2, triggerDemoAct3 } from '../lib/api';

export default function DemoController({ onEventTriggered }) {
  const [loadingAction, setLoadingAction] = useState(null);
  const [lastActionResult, setLastActionResult] = useState(null);

  const handleSeed = async () => {
    setLoadingAction('seed');
    setLastActionResult(null);
    try {
      const res = await seedDemoEnvironment();
      setLastActionResult({ type: 'success', text: 'Seeded test environment with root mandate and sub-mandates' });
      if (onEventTriggered) onEventTriggered('SEED');
    } catch (err) {
      setLastActionResult({ type: 'error', text: err.message });
    } finally {
      setLoadingAction(null);
    }
  };

  const handleAct1 = async () => {
    setLoadingAction('act1');
    setLastActionResult(null);
    try {
      const res = await triggerDemoAct1();
      setLastActionResult({ type: 'allow', text: `Act 1 Result: ${res.decision} - ${res.reason}` });
      if (onEventTriggered) onEventTriggered('ACT1');
    } catch (err) {
      setLastActionResult({ type: 'error', text: err.message });
    } finally {
      setLoadingAction(null);
    }
  };

  const handleAct2 = async () => {
    setLoadingAction('act2');
    setLastActionResult(null);
    try {
      const res = await triggerDemoAct2();
      setLastActionResult({ type: 'block', text: `Act 2 Result: ${res.decision} - ${res.reason}` });
      if (onEventTriggered) onEventTriggered('ACT2');
    } catch (err) {
      setLastActionResult({ type: 'error', text: err.message });
    } finally {
      setLoadingAction(null);
    }
  };

  const handleAct3 = async () => {
    setLoadingAction('act3');
    setLastActionResult(null);
    try {
      const res = await triggerDemoAct3();
      setLastActionResult({ type: 'revoke', text: `Act 3 Result: Kill-switch engaged. Subsequent decision: ${res.subsequent_decision}` });
      if (onEventTriggered) onEventTriggered('ACT3');
    } catch (err) {
      setLastActionResult({ type: 'error', text: err.message });
    } finally {
      setLoadingAction(null);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="h-2.5 w-2.5 rounded-full bg-[#0070ba] animate-ping" />
            <h3 className="font-bold text-sm text-[#001c3f]">Hackathon Presentation Walkthrough Controls</h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Execute the three-act agentic security narrative in real time
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={handleSeed}
            disabled={loadingAction !== null}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg border border-slate-300 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold transition disabled:opacity-50"
          >
            <Database className="w-3.5 h-3.5 text-slate-600" />
            <span>{loadingAction === 'seed' ? 'Resetting...' : 'Reset & Seed Demo'}</span>
          </button>

          <button
            onClick={handleAct1}
            disabled={loadingAction !== null}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow transition disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 text-white" />
            <span>{loadingAction === 'act1' ? 'Executing...' : 'Act 1: Standard Purchase'}</span>
          </button>

          <button
            onClick={handleAct2}
            disabled={loadingAction !== null}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow transition disabled:opacity-50"
          >
            <ShieldAlert className="w-3.5 h-3.5 text-white" />
            <span>{loadingAction === 'act2' ? 'Attacking...' : 'Act 2: Sub-Agent Expansion'}</span>
          </button>

          <button
            onClick={handleAct3}
            disabled={loadingAction !== null}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-[#001c3f] hover:bg-[#002f6c] text-white text-xs font-semibold shadow transition disabled:opacity-50"
          >
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>{loadingAction === 'act3' ? 'Revoking...' : 'Act 3: Emergency Kill-Switch'}</span>
          </button>
        </div>
      </div>

      {lastActionResult && (
        <div className={`mt-3 p-2.5 rounded-lg text-xs font-medium border flex items-center justify-between ${
          lastActionResult.type === 'allow'
            ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
            : lastActionResult.type === 'block'
            ? 'bg-rose-50 border-rose-200 text-rose-800'
            : lastActionResult.type === 'revoke'
            ? 'bg-amber-50 border-amber-200 text-amber-800'
            : 'bg-blue-50 border-blue-200 text-blue-800'
        }`}>
          <span>{lastActionResult.text}</span>
          <CheckCircle2 className="w-4 h-4 ml-2 flex-shrink-0" />
        </div>
      )}
    </div>
  );
}
