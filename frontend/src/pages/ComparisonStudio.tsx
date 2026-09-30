import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { 
  Scale, 
  AlertTriangle, 
  Loader2,
  ChevronDown
} from 'lucide-react';

import { documentApi, compareApi } from '../lib/api';
import { Document, CompareResponse } from '../lib/types';

export default function ComparisonStudio() {
  const [searchParams] = useSearchParams();

  const [documents, setDocuments] = useState<Document[]>([]);
  const [docAId, setDocAId] = useState<string>(searchParams.get('docA') || '');
  const [docBId, setDocBId] = useState<string>(searchParams.get('docB') || '');
  const [loadingDocs, setLoadingDocs] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [filter, setFilter] = useState<'ALL' | 'MODIFIED' | 'ADDED' | 'REMOVED' | 'HIGH_RISK'>('ALL');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadDocs() {
      try {
        const res = await documentApi.list(0, 100);
        setDocuments(res.documents);
        if (!docAId && res.documents.length > 0) {
          setDocAId(res.documents[0].id);
        }
        if (!docBId && res.documents.length > 1) {
          setDocBId(res.documents[1].id);
        }
      } catch (err) {
        console.error('Failed to load documents:', err);
      } finally {
        setLoadingDocs(false);
      }
    }
    loadDocs();
  }, []);

  const handleRunComparison = async () => {
    if (!docAId || !docBId) return;
    if (docAId === docBId) {
      setError('Please choose two distinct contracts to compare.');
      return;
    }

    try {
      setComparing(true);
      setError(null);
      const res = await compareApi.compare(docAId, docBId);
      setResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Comparison failed');
    } finally {
      setComparing(false);
    }
  };

  const filteredDiffs = result?.differences.filter((diff) => {
    if (filter === 'ALL') return true;
    if (filter === 'HIGH_RISK') return diff.risk_impact === 'HIGH' || diff.risk_impact === 'CRITICAL';
    return diff.change_type === filter;
  }) || [];

  return (
    <div className="flex-1 h-full min-h-0 overflow-y-auto overscroll-contain custom-scrollbar p-4 sm:p-8 max-w-7xl mx-auto w-full space-y-8 pb-24">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-extrabold text-white tracking-tight flex items-center space-x-3">
            <Scale className="w-8 h-8 text-indigo-400" />
            <span>Version Comparison Studio</span>
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Detect additions, deletions, subtle word alterations, and legal risk shifts between contract drafts.
          </p>
        </div>
      </div>

      {/* Contract Selectors */}
      <div className="glass p-6 rounded-3xl border border-white/10 shadow-2xl space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative">
          {/* Base Document A */}
          <div className="space-y-2">
            <label className="text-xs uppercase font-semibold tracking-wider text-gray-400 block">
              Original / Base Draft (Document A)
            </label>
            <div className="relative">
              <select
                value={docAId}
                onChange={(e) => setDocAId(e.target.value)}
                disabled={loadingDocs || comparing}
                className="w-full px-4 py-3 rounded-2xl bg-white/[0.04] border border-white/10 text-white text-xs appearance-none focus:outline-none focus:border-indigo-500 transition"
              >
                {documents.map((d) => (
                  <option key={d.id} value={d.id} className="bg-slate-900 text-white">
                    {d.name} ({d.clause_count} clauses)
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-gray-400 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>

          {/* Revised Document B */}
          <div className="space-y-2">
            <label className="text-xs uppercase font-semibold tracking-wider text-gray-400 block">
              Revised / Counterparty Redline (Document B)
            </label>
            <div className="relative">
              <select
                value={docBId}
                onChange={(e) => setDocBId(e.target.value)}
                disabled={loadingDocs || comparing}
                className="w-full px-4 py-3 rounded-2xl bg-white/[0.04] border border-white/10 text-white text-xs appearance-none focus:outline-none focus:border-indigo-500 transition"
              >
                {documents.map((d) => (
                  <option key={d.id} value={d.id} className="bg-slate-900 text-white">
                    {d.name} ({d.clause_count} clauses)
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-gray-400 absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-400" />
            <span>{error}</span>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <button
            onClick={handleRunComparison}
            disabled={!docAId || !docBId || comparing}
            className="flex items-center space-x-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-semibold hover:from-indigo-600 hover:to-purple-700 transition shadow-lg shadow-indigo-500/25 disabled:opacity-50"
          >
            {comparing ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Diffing Clauses & Analyzing Risk...</span>
              </>
            ) : (
              <>
                <Scale className="w-4 h-4" />
                <span>Run Version Comparison</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {result && (
        <div className="space-y-6">
          {/* Summary KPI Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="glass p-4 rounded-2xl border border-white/5">
              <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                Modified Clauses
              </span>
              <p className="text-2xl font-display font-bold text-amber-400 mt-1 font-mono">
                {result.summary.modified}
              </p>
            </div>
            <div className="glass p-4 rounded-2xl border border-white/5">
              <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                Added Clauses
              </span>
              <p className="text-2xl font-display font-bold text-emerald-400 mt-1 font-mono">
                {result.summary.added}
              </p>
            </div>
            <div className="glass p-4 rounded-2xl border border-white/5">
              <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">
                Removed Clauses
              </span>
              <p className="text-2xl font-display font-bold text-rose-400 mt-1 font-mono">
                {result.summary.removed}
              </p>
            </div>
            <div className="glass p-4 rounded-2xl border border-rose-500/20 bg-rose-950/10">
              <span className="text-[10px] uppercase font-bold text-rose-300 tracking-wider">
                High Risk Shifts
              </span>
              <p className="text-2xl font-display font-bold text-rose-400 mt-1 font-mono">
                {result.summary.high_risk_changes}
              </p>
            </div>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center space-x-2 pb-2">
            {[
              { key: 'ALL', label: 'All Diffs' },
              { key: 'HIGH_RISK', label: 'High Risk Shifts' },
              { key: 'MODIFIED', label: 'Modified' },
              { key: 'ADDED', label: 'Added' },
              { key: 'REMOVED', label: 'Removed' },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setFilter(tab.key as any)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition ${
                  filter === tab.key
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white/[0.02] text-gray-400 hover:text-white border border-white/5'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Diff Cards List */}
          <div className="space-y-4">
            {filteredDiffs.length === 0 ? (
              <div className="glass p-12 text-center rounded-3xl border border-white/5 text-gray-400 text-xs">
                No differences found matching this filter.
              </div>
            ) : (
              filteredDiffs.map((diff, idx) => (
                <div
                  key={idx}
                  className="glass p-6 rounded-3xl border border-white/10 space-y-4 shadow-xl"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex items-center space-x-3">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                          diff.change_type === 'ADDED'
                            ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                            : diff.change_type === 'REMOVED'
                            ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                            : 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                        }`}
                      >
                        {diff.change_type}
                      </span>
                      <h3 className="text-sm font-bold text-white">
                        {diff.clause_title}
                      </h3>
                    </div>

                    {diff.risk_impact && diff.risk_impact !== 'NONE' && (
                      <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full text-[10px] font-bold uppercase bg-rose-500/20 text-rose-300 border border-rose-500/40">
                        <AlertTriangle className="w-3 h-3" />
                        <span>{diff.risk_impact} Risk Impact</span>
                      </span>
                    )}
                  </div>

                  {/* AI Risk Explanation */}
                  {diff.risk_explanation && (
                    <div className="p-3.5 rounded-xl bg-white/[0.02] border border-white/5 text-xs text-gray-300 leading-relaxed">
                      <span className="font-semibold text-indigo-400 block mb-1">
                        Impact Analysis:
                      </span>
                      {diff.risk_explanation}
                    </div>
                  )}

                  {/* Side-by-Side Clause Diff */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Draft A */}
                    <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
                      <div className="flex items-center justify-between text-[11px] text-gray-400 font-mono">
                        <span className="font-bold text-gray-300">Draft A (Original)</span>
                        {diff.page_a && <span>P.{diff.page_a}</span>}
                      </div>
                      <p className="text-xs text-gray-300 font-mono leading-relaxed">
                        {diff.text_a || <span className="text-gray-600 italic">Clause absent in Draft A</span>}
                      </p>
                    </div>

                    {/* Draft B */}
                    <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
                      <div className="flex items-center justify-between text-[11px] text-gray-400 font-mono">
                        <span className="font-bold text-indigo-400">Draft B (Revised)</span>
                        {diff.page_b && <span>P.{diff.page_b}</span>}
                      </div>
                      <p className="text-xs text-gray-200 font-mono leading-relaxed">
                        {diff.text_b || <span className="text-rose-400/60 italic">Clause deleted in Draft B</span>}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}
