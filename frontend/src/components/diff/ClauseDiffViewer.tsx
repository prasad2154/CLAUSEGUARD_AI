import React, { useState } from 'react';
import { 
  PlusCircle, 
  MinusCircle, 
  AlertTriangle, 
  CheckCircle, 
  Filter, 
  Layers,
  ArrowRight,
  ShieldAlert,
  Sparkles
} from 'lucide-react';
import { ClauseDiff } from '@/lib/types';

interface ClauseDiffViewerProps {
  diffs: ClauseDiff[];
  docAName?: string;
  docBName?: string;
  onSelectDiff?: (diff: ClauseDiff) => void;
}

export const ClauseDiffViewer: React.FC<ClauseDiffViewerProps> = ({
  diffs,
  docAName = 'Baseline Agreement (v1)',
  docBName = 'Redline Draft (v2)',
  onSelectDiff,
}) => {
  const [filter, setFilter] = useState<'ALL' | 'MODIFIED' | 'ADDED' | 'REMOVED' | 'HIGH_RISK'>('ALL');
  const [selectedDiffIndex, setSelectedDiffIndex] = useState<number | null>(0);

  const filteredDiffs = diffs.filter((d) => {
    if (filter === 'ALL') return true;
    if (filter === 'HIGH_RISK') return d.risk_impact === 'HIGH' || d.risk_impact === 'CRITICAL';
    return d.change_type === filter;
  });

  const getBadgeStyle = (type: string) => {
    switch (type) {
      case 'ADDED':
        return 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30';
      case 'REMOVED':
        return 'bg-rose-500/15 text-rose-400 border-rose-500/30';
      case 'MODIFIED':
        return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      default:
        return 'bg-slate-500/15 text-slate-400 border-slate-500/30';
    }
  };

  const getRiskBadge = (risk?: string) => {
    switch (risk?.toUpperCase()) {
      case 'CRITICAL':
      case 'HIGH':
        return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'MEDIUM':
        return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      case 'LOW':
        return 'bg-blue-500/20 text-blue-300 border-blue-500/40';
      default:
        return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40';
    }
  };

  return (
    <div className="h-full flex flex-col min-h-0 bg-[#090d16] text-gray-200">
      {/* Diff Toolbar Header */}
      <div className="flex-none p-4 border-b border-white/10 bg-[#0f1624]/90 backdrop-blur-md flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-2">
          <Layers className="w-4 h-4 text-indigo-400" />
          <span className="font-semibold text-sm text-white">Semantic Version Diff</span>
          <span className="px-2 py-0.5 rounded-full text-xs font-mono bg-white/10 text-gray-300">
            {filteredDiffs.length} differences
          </span>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center space-x-1.5 bg-[#090d16] p-1 rounded-xl border border-white/10 text-xs">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-2.5 py-1 rounded-lg transition font-medium ${
              filter === 'ALL' ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
            }`}
          >
            All ({diffs.length})
          </button>
          <button
            onClick={() => setFilter('HIGH_RISK')}
            className={`px-2.5 py-1 rounded-lg transition font-medium flex items-center space-x-1 ${
              filter === 'HIGH_RISK' ? 'bg-rose-600 text-white shadow-sm' : 'text-rose-400 hover:bg-rose-950/30'
            }`}
          >
            <ShieldAlert className="w-3 h-3" />
            <span>High Risk</span>
          </button>
          <button
            onClick={() => setFilter('MODIFIED')}
            className={`px-2.5 py-1 rounded-lg transition font-medium ${
              filter === 'MODIFIED' ? 'bg-amber-600 text-white shadow-sm' : 'text-amber-400 hover:bg-amber-950/30'
            }`}
          >
            Modified
          </button>
          <button
            onClick={() => setFilter('ADDED')}
            className={`px-2.5 py-1 rounded-lg transition font-medium ${
              filter === 'ADDED' ? 'bg-emerald-600 text-white shadow-sm' : 'text-emerald-400 hover:bg-emerald-950/30'
            }`}
          >
            Added
          </button>
          <button
            onClick={() => setFilter('REMOVED')}
            className={`px-2.5 py-1 rounded-lg transition font-medium ${
              filter === 'REMOVED' ? 'bg-rose-600 text-white shadow-sm' : 'text-rose-400 hover:bg-rose-950/30'
            }`}
          >
            Removed
          </button>
        </div>
      </div>

      {/* Main Diff Content Split Panes */}
      <div className="flex-1 min-h-0 flex flex-col lg:flex-row overflow-hidden">
        {/* Left Column: Difference List */}
        <div className="w-full lg:w-80 flex-none border-b lg:border-b-0 lg:border-r border-white/10 h-64 lg:h-full overflow-y-auto overscroll-contain custom-scrollbar p-3 space-y-2.5 bg-[#0b101a]/70">
          {filteredDiffs.map((diff, index) => {
            const isSelected = selectedDiffIndex === index;
            return (
              <div
                key={index}
                onClick={() => {
                  setSelectedDiffIndex(index);
                  if (onSelectDiff) onSelectDiff(diff);
                }}
                className={`p-3 rounded-xl border cursor-pointer transition-all ${
                  isSelected
                    ? 'border-indigo-500/60 bg-indigo-950/30 shadow-lg shadow-indigo-500/10'
                    : 'border-white/5 bg-[#121927]/60 hover:bg-[#162032] hover:border-white/10'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${getBadgeStyle(diff.change_type)}`}>
                    {diff.change_type}
                  </span>
                  {diff.risk_impact && diff.risk_impact !== 'NONE' && (
                    <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded-full border ${getRiskBadge(diff.risk_impact)}`}>
                      {diff.risk_impact} Risk
                    </span>
                  )}
                </div>
                <h4 className="text-xs font-semibold text-white truncate">
                  {diff.clause_title || diff.section || 'General Provision'}
                </h4>
                <p className="text-[11px] text-gray-400 line-clamp-2 mt-1">
                  {diff.risk_explanation || 'Click to view comparative clause diff text.'}
                </p>
              </div>
            );
          })}

          {filteredDiffs.length === 0 && (
            <div className="text-center py-12 text-gray-500 text-xs">
              No differences matching selected criteria.
            </div>
          )}
        </div>

        {/* Right Column: Comparative Side-by-Side Inspector */}
        <div className="flex-1 min-h-0 h-full overflow-y-auto overscroll-contain custom-scrollbar p-6 bg-[#090d16]">
          {selectedDiffIndex !== null && filteredDiffs[selectedDiffIndex] ? (
            (() => {
              const activeDiff = filteredDiffs[selectedDiffIndex];
              return (
                <div className="space-y-6 max-w-5xl mx-auto">
                  {/* Analysis Callout */}
                  <div className="p-4 rounded-2xl border border-indigo-500/30 bg-gradient-to-r from-indigo-950/40 to-[#0e1628] flex items-start space-x-3.5">
                    <div className="w-8 h-8 rounded-xl bg-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0 mt-0.5">
                      <Sparkles className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-bold text-white">
                          {activeDiff.clause_title || activeDiff.section}
                        </h3>
                        <span className={`text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full border ${getBadgeStyle(activeDiff.change_type)}`}>
                          {activeDiff.change_type}
                        </span>
                      </div>
                      <p className="text-xs text-indigo-200/90 mt-1 leading-relaxed">
                        {activeDiff.risk_explanation || 'Material difference detected during autonomous contract audit.'}
                      </p>
                    </div>
                  </div>

                  {/* Side-by-Side Clause Split */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Baseline Version v1 */}
                    <div className="flex flex-col rounded-2xl border border-white/10 bg-[#0f1624] overflow-hidden shadow-xl">
                      <div className="px-4 py-3 border-b border-white/10 bg-white/[0.02] flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <MinusCircle className="w-3.5 h-3.5 text-rose-400" />
                          <span className="text-xs font-semibold text-gray-300">{docAName}</span>
                        </div>
                        {activeDiff.page_a && (
                          <span className="text-[10px] font-mono bg-white/5 px-2 py-0.5 rounded text-gray-400">
                            Page {activeDiff.page_a}
                          </span>
                        )}
                      </div>
                      <div className="p-4 flex-1 text-xs font-mono leading-relaxed overflow-y-auto max-h-96 custom-scrollbar text-gray-300 whitespace-pre-wrap">
                        {activeDiff.text_a ? (
                          <div className={activeDiff.change_type === 'REMOVED' || activeDiff.change_type === 'MODIFIED' ? 'diff-deletion p-3 rounded-lg' : ''}>
                            {activeDiff.text_a}
                          </div>
                        ) : (
                          <span className="text-gray-500 italic">Clause does not exist in baseline version (Omitted).</span>
                        )}
                      </div>
                    </div>

                    {/* Redline Draft v2 */}
                    <div className="flex flex-col rounded-2xl border border-white/10 bg-[#0f1624] overflow-hidden shadow-xl">
                      <div className="px-4 py-3 border-b border-white/10 bg-white/[0.02] flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <PlusCircle className="w-3.5 h-3.5 text-emerald-400" />
                          <span className="text-xs font-semibold text-gray-300">{docBName}</span>
                        </div>
                        {activeDiff.page_b && (
                          <span className="text-[10px] font-mono bg-white/5 px-2 py-0.5 rounded text-gray-400">
                            Page {activeDiff.page_b}
                          </span>
                        )}
                      </div>
                      <div className="p-4 flex-1 text-xs font-mono leading-relaxed overflow-y-auto max-h-96 custom-scrollbar text-gray-300 whitespace-pre-wrap">
                        {activeDiff.text_b ? (
                          <div className={activeDiff.change_type === 'ADDED' ? 'diff-addition p-3 rounded-lg' : activeDiff.change_type === 'MODIFIED' ? 'diff-modification p-3 rounded-lg' : ''}>
                            {activeDiff.text_b}
                          </div>
                        ) : (
                          <span className="text-gray-500 italic">Clause deleted from the active draft.</span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })()
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 text-gray-500">
              <Layers className="w-10 h-10 mb-3 opacity-40" />
              <p className="text-sm font-medium">Select a clause change to view side-by-side comparison</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
