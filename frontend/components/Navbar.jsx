import React from 'react';
import { ShieldCheck, RefreshCw, Radio } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, onVerifyAudit, isVerifying, auditStatus }) {
  const tabs = [
    { id: 'overview', label: 'Live Monitoring' },
    { id: 'mandate', label: 'Create Mandate' },
    { id: 'delegation', label: 'Agent Hierarchy' },
    { id: 'merchant', label: 'Merchant Signal' },
    { id: 'redteam', label: 'Red Team Testing' },
    { id: 'disputes', label: 'Dispute Evidence' },
  ];

  return (
    <header className="bg-[#001c3f] text-white border-b border-[#0c2f5d] sticky top-0 z-50 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#003087] to-[#0070ba] flex items-center justify-center shadow-inner">
              <ShieldCheck className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight text-white">MandateGuard</span>
                <span className="text-[10px] uppercase font-bold tracking-wider bg-[#0070ba] text-white px-2 py-0.5 rounded-full">
                  PayPal Agentic Rail
                </span>
              </div>
              <p className="text-xs text-slate-300 hidden sm:block">
                Cryptographic Pre-Flight Authorization for Autonomous Agents
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <div className="hidden md:flex items-center space-x-1.5 px-3 py-1 rounded-full bg-[#0c2f5d] text-xs text-emerald-400 font-medium">
              <Radio className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
              <span>Real-Time Gate Connected</span>
            </div>

            <button
              onClick={onVerifyAudit}
              disabled={isVerifying}
              className="flex items-center space-x-2 px-3.5 py-1.5 rounded-lg bg-[#0070ba] hover:bg-[#005ea6] text-white text-xs font-semibold shadow transition-all duration-150 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isVerifying ? 'animate-spin' : ''}`} />
              <span>{isVerifying ? 'Verifying...' : 'Verify Ledger Integrity'}</span>
            </button>
          </div>
        </div>

        <nav className="flex space-x-1 sm:space-x-4 border-t border-[#0c2f5d] pt-1 overflow-x-auto">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-3 text-xs sm:text-sm font-semibold border-b-2 whitespace-nowrap transition-colors duration-150 ${
                  isActive
                    ? 'border-[#0070ba] text-white bg-[#0c2f5d]/40 rounded-t'
                    : 'border-transparent text-slate-300 hover:text-white hover:border-slate-400'
                }`}
              >
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
