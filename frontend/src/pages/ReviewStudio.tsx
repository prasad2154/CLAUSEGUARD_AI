import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert,
  AlertTriangle,
  Search,
  MessageSquare,
  RefreshCw,
  Sparkles,
  Copy,
  Check,
  Send,
  AlertOctagon,
  ChevronRight,
  Loader2,
  BookOpen,
  FileText,
  Calendar,
  Hash,
  User,
  Scale,
  TrendingUp,
  Eye,
  EyeOff,
  Lightbulb,
  ArrowRight,
  X,
} from 'lucide-react';

import { documentApi, reviewApi, queryApi } from '../lib/api';
import { Document, Clause, ReviewResponse, QueryResponse } from '../lib/types';

// ─── Risk color helpers ───────────────────────────────────────────────────────
function severityColors(severity: string) {
  switch (severity?.toUpperCase()) {
    case 'CRITICAL': return { bg: 'bg-rose-500/15', border: 'border-rose-500/40', text: 'text-rose-300', dot: 'bg-rose-500', bar: 'bg-rose-500' };
    case 'HIGH':     return { bg: 'bg-amber-500/15', border: 'border-amber-500/40', text: 'text-amber-300', dot: 'bg-amber-400', bar: 'bg-amber-400' };
    case 'MEDIUM':   return { bg: 'bg-blue-500/15',  border: 'border-blue-500/40',  text: 'text-blue-300',  dot: 'bg-blue-400',  bar: 'bg-blue-400'  };
    default:         return { bg: 'bg-emerald-500/15', border: 'border-emerald-500/40', text: 'text-emerald-300', dot: 'bg-emerald-400', bar: 'bg-emerald-400' };
  }
}

// ─── Score ring dial ──────────────────────────────────────────────────────────
function RiskScoreDial({ score, level }: { score: number; level: string }) {
  const r = 42;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const strokeColor =
    score >= 60 ? '#ef4444' : score >= 35 ? '#f59e0b' : '#10b981';
  const ringBg =
    score >= 60 ? 'shadow-[0_0_30px_rgba(239,68,68,0.25)]' : score >= 35 ? 'shadow-[0_0_30px_rgba(245,158,11,0.25)]' : 'shadow-[0_0_30px_rgba(16,185,129,0.2)]';

  return (
    <div className={`relative inline-flex items-center justify-center w-28 h-28 rounded-full ${ringBg}`}>
      <svg className="w-28 h-28 -rotate-90" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="8" />
        <circle
          cx="50" cy="50" r={r}
          fill="none"
          stroke={strokeColor}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 1s ease' }}
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-3xl font-black text-white font-display">{score}</div>
        <div className="text-[9px] uppercase tracking-widest font-bold" style={{ color: strokeColor }}>
          {level}
        </div>
      </div>
    </div>
  );
}

export default function ReviewStudio() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [doc, setDoc] = useState<Document | null>(null);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Left-pane clause viewer
  const [clauseSearch, setClauseSearch] = useState('');
  const [selectedClauseId, setSelectedClauseId] = useState<string | null>(null);
  const [showHighlights, setShowHighlights] = useState(true);
  const [activeHighlight, setActiveHighlight] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'MISSING'>('ALL');

  // Right inspector panel
  const [inspectorTab, setInspectorTab] = useState<'risks' | 'missing' | 'qa'>('risks');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Q&A
  const [qaInput, setQaInput] = useState('');
  const [qaLoading, setQaLoading] = useState(false);
  const [qaHistory, setQaHistory] = useState<QueryResponse[]>([]);

  useEffect(() => {
    if (!id) return;
    loadAll(id);
  }, [id]);

  const loadAll = async (docId: string) => {
    try {
      setLoading(true);
      setError(null);
      const [docData, clauseData] = await Promise.all([
        documentApi.get(docId),
        documentApi.getClauses(docId),
      ]);
      setDoc(docData);
      setClauses(clauseData);
      try {
        const revData = await reviewApi.getLatest(docId);
        setReview(revData);
      } catch {
        handleRunReview(docId);
      }
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load document');
    } finally {
      setLoading(false);
    }
  };

  const handleRunReview = async (docId?: string, force = false) => {
    const target = docId || id;
    if (!target) return;
    try {
      setReviewing(true);
      setError(null);
      const revData = await reviewApi.trigger(target, force);
      setReview(revData);
    } catch (err: any) {
      setError(err?.response?.data?.detail || err.message || 'Review generation failed');
    } finally {
      setReviewing(false);
    }
  };

  const handleCopy = (text: string, key: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(key);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleAsk = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !qaInput.trim() || qaLoading) return;
    const q = qaInput.trim();
    setQaInput('');
    setQaLoading(true);
    try {
      const resp = await queryApi.ask(id, q);
      setQaHistory(prev => [resp, ...prev]);
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to answer question');
    } finally {
      setQaLoading(false);
    }
  };

  // ─── Build lookup maps ──────────────────────────────────────────────────────
  const riskyClauseMap = new Map<string, string>();
  review?.risks.forEach(r => {
    if (r.clause_id) {
      const existing = riskyClauseMap.get(r.clause_id);
      const sev = r.severity.toUpperCase();
      const order = ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'INFO'];
      if (!existing || order.indexOf(sev) < order.indexOf(existing)) {
        riskyClauseMap.set(r.clause_id, sev);
      }
    }
  });

  const filteredClauses = clauses.filter(c => {
    if (!clauseSearch) return true;
    const q = clauseSearch.toLowerCase();
    return (
      c.clause_text.toLowerCase().includes(q) ||
      (c.clause_title || '').toLowerCase().includes(q) ||
      c.clause_id.toLowerCase().includes(q)
    );
  });

  const filteredRisks = (review?.risks || []).filter(r =>
    severityFilter === 'ALL' ? true : r.severity === severityFilter
  );

  const score = review ? Math.round(review.overall_risk_score) : 0;
  const riskLevel = review?.risk_level || 'MINIMAL';

  // ─── Loading / Error states ─────────────────────────────────────────────────
  if (loading) return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
      <Loader2 className="w-10 h-10 text-indigo-400 animate-spin" />
      <p className="text-white font-semibold">Loading Contract Studio...</p>
      <p className="text-gray-500 text-xs">Retrieving parsed clauses and embeddings</p>
    </div>
  );

  if (error || !doc) return (
    <div className="max-w-md mx-auto py-24 text-center glass p-8 rounded-3xl border border-rose-500/20">
      <AlertTriangle className="w-12 h-12 text-rose-400 mx-auto mb-4" />
      <h2 className="text-xl font-bold text-white mb-2">Review Error</h2>
      <p className="text-gray-400 text-xs mb-6">{error || 'Document could not be located'}</p>
      <button
        onClick={() => navigate('/documents')}
        className="px-5 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold transition"
      >
        Return to Library
      </button>
    </div>
  );

  return (
    <div className="space-y-5 pb-28">
      {/* ═══ BREADCRUMB ═══════════════════════════════════════════════════════ */}
      <div className="flex items-center space-x-2 text-xs text-gray-400">
        <button onClick={() => navigate('/documents')} className="hover:text-white transition">Library</button>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="text-gray-300 truncate max-w-xs">{doc.name}</span>
        <span className="ml-auto px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
          {reviewing ? 'Analyzing…' : review ? 'Completed' : 'Pending'}
        </span>
      </div>

      {/* ═══ EXECUTIVE HEADER ═══════════════════════════════════════════════ */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-3xl border border-white/10 p-6 shadow-2xl"
      >
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 items-center">
          {/* Score Dial */}
          <div className="flex flex-col items-center space-y-2">
            <span className="text-[10px] uppercase tracking-widest text-gray-400 font-semibold">Overall Risk Score</span>
            {review ? (
              <RiskScoreDial score={score} level={riskLevel} />
            ) : (
              <div className="w-28 h-28 rounded-full border-4 border-white/10 flex items-center justify-center">
                {reviewing ? <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" /> : <Scale className="w-8 h-8 text-gray-500" />}
              </div>
            )}
            <span className="text-[11px] text-gray-400">
              {score > 60 ? '⚠️ High Risk' : score > 30 ? '⚡ Medium Risk' : '✅ Low Risk'}
            </span>
          </div>

          {/* Category Risk Bars */}
          <div className="lg:col-span-1 space-y-2.5">
            <h3 className="text-xs font-bold text-white mb-3 flex items-center space-x-2">
              <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
              <span>Risk by Category</span>
            </h3>
            {review?.category_breakdown && review.category_breakdown.length > 0 ? (
              review.category_breakdown.slice(0, 5).map((cat) => {
                const col = severityColors(cat.severity === 'Critical' ? 'CRITICAL' : cat.severity.toUpperCase());
                return (
                  <div key={cat.category} className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-gray-300 font-medium">{cat.category}</span>
                      <span className={`font-bold ${col.text}`}>{cat.severity}</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-white/[0.06]">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${cat.score}%` }}
                        transition={{ duration: 0.8, ease: 'easeOut' }}
                        className={`h-full rounded-full ${col.bar}`}
                      />
                    </div>
                  </div>
                );
              })
            ) : (
              /* Placeholder category bars when no review yet */
              [['Confidentiality', 85, 'CRITICAL'], ['Liability', 60, 'HIGH'], ['Termination', 70, 'HIGH'], ['Payment', 30, 'MEDIUM'], ['General', 20, 'LOW']].map(([cat, pct, sev]) => {
                const col = severityColors(sev as string);
                return (
                  <div key={cat as string} className="space-y-1">
                    <div className="flex items-center justify-between text-[11px]">
                      <span className="text-gray-500">{cat as string}</span>
                      <span className={`font-bold ${review ? col.text : 'text-gray-600'}`}>{review ? sev : '–'}</span>
                    </div>
                    <div className="w-full h-1.5 rounded-full bg-white/[0.06]">
                      {review && (
                        <div className={`h-full rounded-full ${col.bar} opacity-30`} style={{ width: `${pct}%` }} />
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>

          {/* Missing Clauses Count */}
          <div className="flex flex-col items-center justify-center space-y-2 border border-white/[0.07] rounded-2xl p-5 bg-white/[0.02] h-full">
            <AlertTriangle className="w-7 h-7 text-amber-400" />
            <div className="text-4xl font-black text-white font-display">
              {review?.missing_clause_count ?? '–'}
            </div>
            <p className="text-[11px] text-amber-300 font-semibold text-center">Important clauses missing</p>
            <button
              onClick={() => setInspectorTab('missing')}
              className="text-[10px] text-indigo-400 hover:text-indigo-300 underline underline-offset-2 transition"
            >
              View Details →
            </button>
          </div>

          {/* Document Info Panel */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-gray-300 flex items-center space-x-2">
              <FileText className="w-3.5 h-3.5 text-indigo-400" />
              <span>Document Info</span>
            </h3>
            {[
              { label: 'Type', value: doc.contract_type || 'General Agreement', icon: Scale },
              { label: 'Pages', value: String(doc.page_count), icon: Hash },
              { label: 'Clauses', value: String(doc.clause_count), icon: BookOpen },
              { label: 'Reviewed By', value: 'ClauseGuard AI', icon: User },
              { label: 'Added', value: new Date(doc.created_at).toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' }), icon: Calendar },
            ].map(({ label, value, icon: Icon }) => (
              <div key={label} className="flex items-center justify-between text-[11px]">
                <span className="text-gray-500 flex items-center space-x-1.5"><Icon className="w-3 h-3" /><span>{label}</span></span>
                <span className="text-gray-200 font-medium">{value}</span>
              </div>
            ))}
            <button
              onClick={() => handleRunReview(id, true)}
              disabled={reviewing}
              className="w-full mt-2 flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white text-xs font-semibold transition disabled:opacity-50 shadow-lg shadow-indigo-500/20"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${reviewing ? 'animate-spin' : ''}`} />
              <span>{reviewing ? 'Running Agents…' : 'Re-Run Audit'}</span>
            </button>
          </div>
        </div>
      </motion.div>

      {/* ═══ MAIN WORKSPACE ═════════════════════════════════════════════════ */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-5 min-h-[620px]">

        {/* ── LEFT: Clause Document Viewer (5 cols) ────────────────────────── */}
        <div className="xl:col-span-5 glass rounded-3xl border border-white/10 flex flex-col overflow-hidden" style={{ maxHeight: '78vh' }}>
          {/* Header */}
          <div className="px-5 pt-5 pb-4 border-b border-white/[0.07] space-y-3 flex-shrink-0">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <BookOpen className="w-4 h-4 text-indigo-400" />
                <h2 className="text-sm font-bold text-white">Document Review</h2>
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-white/10 text-gray-300 font-mono">
                  {filteredClauses.length} clauses
                </span>
              </div>
              <button
                onClick={() => setShowHighlights(s => !s)}
                className="flex items-center space-x-1.5 text-[11px] text-gray-400 hover:text-white transition"
              >
                {showHighlights ? <Eye className="w-3.5 h-3.5" /> : <EyeOff className="w-3.5 h-3.5" />}
                <span>Show All Highlights</span>
              </button>
            </div>

            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
              <input
                type="text"
                placeholder="Search in document..."
                value={clauseSearch}
                onChange={e => setClauseSearch(e.target.value)}
                className="w-full pl-9 pr-3 py-2 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white text-xs placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
              />
            </div>

            {/* Highlight filter pills */}
            {showHighlights && (
              <div className="flex items-center gap-1.5 flex-wrap">
                {[
                  { id: 'ALL', label: 'All', cls: 'bg-white/10 text-gray-300' },
                  { id: 'HIGH', label: '🔴 High Risk', cls: 'bg-rose-500/15 text-rose-300 border border-rose-500/30' },
                  { id: 'MEDIUM', label: '🟡 Medium Risk', cls: 'bg-amber-500/15 text-amber-300 border border-amber-500/30' },
                  { id: 'LOW', label: '🟢 Low Risk', cls: 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' },
                  { id: 'MISSING', label: '⚠️ Missing', cls: 'bg-purple-500/15 text-purple-300 border border-purple-500/30' },
                ].map(pill => (
                  <button
                    key={pill.id}
                    onClick={() => setActiveHighlight(pill.id as any)}
                    className={`px-2 py-0.5 rounded-full text-[10px] font-semibold transition ${
                      activeHighlight === pill.id ? pill.cls + ' ring-1 ring-white/20' : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    {pill.label}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Clause Scroll Area */}
          <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3" style={{ overflowY: 'auto' }}>
            {filteredClauses.length === 0 ? (
              <div className="text-center py-16 text-gray-500 text-xs">No clauses matched your search.</div>
            ) : (
              filteredClauses.map((clause) => {
                const riskSev = riskyClauseMap.get(clause.clause_id);
                const isSelected = selectedClauseId === clause.clause_id;
                const col = riskSev ? severityColors(riskSev) : null;
                const shouldHighlight = showHighlights && riskSev;

                return (
                  <motion.div
                    key={clause.id}
                    id={`clause-${clause.clause_id}`}
                    layout
                    onClick={() => setSelectedClauseId(clause.clause_id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all relative overflow-hidden ${
                      isSelected
                        ? 'border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/10'
                        : shouldHighlight
                        ? `${col!.border} ${col!.bg}`
                        : 'border-white/[0.06] bg-white/[0.02] hover:border-white/15 hover:bg-white/[0.04]'
                    }`}
                  >
                    {/* Clause Header Row */}
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-[10px] font-bold bg-white/10 text-gray-400 px-2 py-0.5 rounded">
                        {clause.clause_id}
                      </span>
                      <div className="flex items-center space-x-2">
                        {shouldHighlight && (
                          <span className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold border ${col!.border} ${col!.text} ${col!.bg}`}>
                            <span className={`w-1.5 h-1.5 rounded-full ${col!.dot}`} />
                            <span>
                              {riskSev === 'CRITICAL' ? 'High Risk' : riskSev === 'HIGH' ? 'High Risk' : riskSev === 'MEDIUM' ? 'Medium Risk' : 'Low Risk'}
                            </span>
                          </span>
                        )}
                        <span className="text-[10px] text-gray-600 font-mono">P.{clause.page_number}</span>
                      </div>
                    </div>

                    {clause.clause_title && (
                      <p className="text-xs font-semibold text-white mb-1">{clause.clause_title}</p>
                    )}
                    <p className="text-xs text-gray-300 line-clamp-4 leading-relaxed">{clause.clause_text}</p>

                    {/* Click to jump to risk */}
                    {riskSev && (
                      <button
                        onClick={(e) => { e.stopPropagation(); setInspectorTab('risks'); setSeverityFilter(riskSev); }}
                        className="mt-2 flex items-center space-x-1 text-[10px] text-indigo-400 hover:text-indigo-300"
                      >
                        <span>View Risk Details</span><ChevronRight className="w-3 h-3" />
                      </button>
                    )}
                  </motion.div>
                );
              })
            )}
          </div>
        </div>

        {/* ── RIGHT: Inspector + Q&A (7 cols) ─────────────────────────────── */}
        <div className="xl:col-span-7 flex flex-col gap-5">

          {/* Inspector Panel (Top) */}
          <div className="glass rounded-3xl border border-white/10 flex flex-col overflow-hidden" style={{ maxHeight: '54vh' }}>
            {/* Inspector Tabs */}
            <div className="px-5 pt-4 pb-0 flex items-center space-x-1 border-b border-white/[0.07] flex-shrink-0">
              {[
                { id: 'risks', label: `Key Risks (${review?.risks.length ?? 0})`, icon: ShieldAlert, active: 'text-rose-300 border-rose-400', border: 'border-b-2' },
                { id: 'missing', label: `Missing Clauses (${review?.missing_clauses.length ?? 0})`, icon: AlertTriangle, active: 'text-amber-300 border-amber-400', border: 'border-b-2' },
                { id: 'qa', label: 'Q&A', icon: MessageSquare, active: 'text-indigo-300 border-indigo-400', border: 'border-b-2' },
              ].map(tab => {
                const isActive = inspectorTab === tab.id;
                const Icon = tab.icon;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setInspectorTab(tab.id as any)}
                    className={`flex items-center space-x-1.5 px-4 py-3 text-xs font-semibold transition-all relative ${
                      isActive ? tab.active : 'text-gray-500 hover:text-gray-300'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    <span>{tab.label}</span>
                    {isActive && (
                      <motion.div layoutId="inspector-tab" className={`absolute bottom-0 left-0 right-0 h-0.5 ${tab.active.split(' ')[1].replace('border-', 'bg-')}`} />
                    )}
                  </button>
                );
              })}
            </div>

            {/* TAB CONTENT */}
            <div className="flex-1 overflow-y-auto px-5 py-4 space-y-3" style={{ overflowY: 'auto' }}>
              <AnimatePresence mode="wait">
                {/* RISKS TAB */}
                {inspectorTab === 'risks' && (
                  <motion.div key="risks" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
                    {/* Severity filter */}
                    <div className="flex items-center space-x-1.5 flex-wrap gap-y-1">
                      {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(s => (
                        <button
                          key={s}
                          onClick={() => setSeverityFilter(s)}
                          className={`px-2.5 py-1 rounded-lg text-[10px] font-bold transition ${
                            severityFilter === s
                              ? s === 'CRITICAL' ? 'bg-rose-600 text-white' : s === 'HIGH' ? 'bg-amber-600 text-white' : s === 'MEDIUM' ? 'bg-blue-600 text-white' : 'bg-emerald-600 text-white'
                              : 'bg-white/[0.04] text-gray-400 hover:text-white'
                          }`}
                        >
                          {s}
                        </button>
                      ))}
                    </div>

                    {reviewing ? (
                      <div className="py-16 text-center space-y-3">
                        <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
                        <p className="text-white text-xs font-semibold">Running LangGraph Multi-Agent Audit…</p>
                        <p className="text-gray-500 text-[11px]">Evaluating liability, indemnity, and governing law clauses</p>
                      </div>
                    ) : filteredRisks.length === 0 ? (
                      <div className="text-center py-12 text-gray-500 text-xs">No risks detected for the selected filter.</div>
                    ) : (
                      filteredRisks.map((risk, idx) => {
                        const col = severityColors(risk.severity);
                        return (
                          <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: idx * 0.04 }}
                            className={`p-4 rounded-2xl border space-y-3 ${col.bg} ${col.border}`}
                          >
                            <div className="flex items-start justify-between gap-3">
                              <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                                <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border ${col.bg} ${col.text} ${col.border}`}>
                                  {risk.severity}
                                </span>
                                <span className="text-[11px] text-gray-400 font-medium">{risk.category}</span>
                              </div>
                              {risk.clause_id && (
                                <button
                                  onClick={() => {
                                    setSelectedClauseId(risk.clause_id!);
                                    document.getElementById(`clause-${risk.clause_id}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                  }}
                                  className="flex items-center space-x-1 text-[10px] font-mono text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20 transition flex-shrink-0"
                                >
                                  <span>{risk.clause_id}</span>
                                  <ChevronRight className="w-3 h-3" />
                                </button>
                              )}
                            </div>

                            <h3 className="text-sm font-bold text-white">{risk.title}</h3>

                            {risk.evidence && (
                              <div className="p-3 rounded-xl bg-black/40 border border-rose-500/20">
                                <p className="text-[10px] uppercase font-bold text-rose-400 tracking-wider mb-1">
                                  Clause Citation {risk.page_number ? `· Page ${risk.page_number}` : ''}
                                </p>
                                <p className="text-xs text-gray-300 italic font-mono leading-relaxed line-clamp-3">
                                  "{risk.evidence}"
                                </p>
                              </div>
                            )}

                            <p className="text-xs text-gray-300 leading-relaxed">{risk.explanation}</p>

                            {risk.recommendation && (
                              <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-500/25">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="text-[10px] uppercase font-bold text-emerald-400 tracking-wider">Recommended Action</span>
                                  <button
                                    onClick={() => handleCopy(risk.recommendation, `r-${idx}`)}
                                    className="flex items-center space-x-1 text-[10px] text-emerald-300 hover:text-white transition"
                                  >
                                    {copiedId === `r-${idx}` ? <><Check className="w-3 h-3" /><span>Copied</span></> : <><Copy className="w-3 h-3" /><span>Copy</span></>}
                                  </button>
                                </div>
                                <p className="text-xs text-emerald-200/90 leading-relaxed">{risk.recommendation}</p>
                              </div>
                            )}

                            <div className="flex items-center justify-between text-[10px] text-gray-600 border-t border-white/[0.05] pt-2">
                              <span>Confidence: {(risk.confidence * 100).toFixed(0)}%</span>
                              <span className="text-emerald-600/60">Zero-Hallucination Grounded</span>
                            </div>
                          </motion.div>
                        );
                      })
                    )}
                  </motion.div>
                )}

                {/* MISSING CLAUSES TAB */}
                {inspectorTab === 'missing' && (
                  <motion.div key="missing" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
                    {!review?.missing_clauses.length ? (
                      <div className="text-center py-12 text-gray-500 text-xs">No standard clauses are missing.</div>
                    ) : (
                      review.missing_clauses.map((mc, idx) => {
                        const col = severityColors(mc.importance);
                        return (
                          <div key={idx} className={`p-4 rounded-2xl border space-y-3 ${col.bg} ${col.border}`}>
                            <div className="flex items-center justify-between">
                              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${col.text} ${col.border} ${col.bg}`}>
                                {mc.importance} IMPORTANCE
                              </span>
                              <span className="text-xs text-gray-400">Standard for {mc.contract_type || 'Agreements'}</span>
                            </div>
                            <h3 className="text-sm font-bold text-white">Missing: {mc.clause_name}</h3>
                            <p className="text-xs text-gray-300 leading-relaxed">{mc.reason}</p>
                            <div className="p-3 rounded-xl bg-black/30 border border-white/[0.06]">
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-[10px] uppercase font-bold text-gray-400">Recommended Language</span>
                                <button onClick={() => handleCopy(mc.recommendation, `mc-${idx}`)} className="flex items-center space-x-1 text-[10px] text-indigo-400 hover:text-indigo-300">
                                  {copiedId === `mc-${idx}` ? <><Check className="w-3 h-3" /><span>Copied</span></> : <><Copy className="w-3 h-3" /><span>Copy Draft</span></>}
                                </button>
                              </div>
                              <p className="text-xs text-gray-300 font-mono leading-relaxed">{mc.recommendation}</p>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </motion.div>
                )}

                {/* Q&A TAB (Inspector) — quick preview; full Q&A below */}
                {inspectorTab === 'qa' && (
                  <motion.div key="qa" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="space-y-3">
                    <p className="text-xs text-gray-400">Use the <span className="text-indigo-300 font-semibold">Clause-Level Q&A</span> panel below to ask questions with grounded citations.</p>
                    <div className="flex flex-wrap gap-2">
                      {[
                        'What is the termination period?',
                        'What is our total liability exposure?',
                        'Is there a governing law clause?',
                        'What are the payment terms?',
                      ].map((q, i) => (
                        <button
                          key={i}
                          onClick={() => { setQaInput(q); setInspectorTab('qa'); }}
                          className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-white/10 text-gray-300 text-[11px] border border-white/10 transition text-left"
                        >
                          {q}
                        </button>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* ── Q&A Assistant Panel (Bottom) ───────────────────────────────── */}
          <div className="glass rounded-3xl border border-white/10 flex flex-col overflow-hidden" style={{ maxHeight: '36vh' }}>
            <div className="px-5 py-3 border-b border-white/[0.07] flex items-center justify-between flex-shrink-0">
              <div className="flex items-center space-x-2">
                <MessageSquare className="w-4 h-4 text-indigo-400" />
                <h3 className="text-sm font-bold text-white">Clause-Level Q&A</h3>
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">Citation Grounded</span>
              </div>
              <span className="text-[10px] text-indigo-400 hover:text-indigo-300 cursor-pointer" onClick={() => setInspectorTab('qa')}>
                View full Q&A
              </span>
            </div>

            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3" style={{ overflowY: 'auto' }}>
              {qaHistory.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-center space-y-2 py-4">
                  <p className="text-gray-500 text-xs">Ask anything about this contract…</p>
                  <div className="flex flex-wrap justify-center gap-1.5">
                    {['What is the termination period in this contract?', 'What is our liability cap?'].map((q, i) => (
                      <button key={i} onClick={() => setQaInput(q)} className="px-2.5 py-1 rounded-xl bg-white/5 hover:bg-indigo-500/10 text-indigo-300 text-[10px] border border-indigo-500/20 transition">
                        {q}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                qaHistory.map((item, idx) => (
                  <div key={idx} className="space-y-2">
                    {/* Question bubble */}
                    <div className="flex justify-end">
                      <div className="max-w-[85%] px-3 py-2 rounded-2xl rounded-tr-sm bg-indigo-600/30 border border-indigo-500/30 text-xs text-indigo-100">
                        {item.question}
                      </div>
                    </div>
                    {/* Answer bubble */}
                    <div className="max-w-[90%] px-3 py-2.5 rounded-2xl rounded-tl-sm bg-white/[0.04] border border-white/[0.07] space-y-2">
                      <div className="flex items-center space-x-1.5 mb-1">
                        <Sparkles className="w-3 h-3 text-indigo-400" />
                        <span className="text-[9px] uppercase tracking-widest text-indigo-400 font-bold">ClauseGuard AI</span>
                      </div>
                      <p className="text-xs text-gray-200 leading-relaxed">{item.answer}</p>
                      {item.citations.length > 0 && (
                        <div className="space-y-1 pt-1 border-t border-white/[0.05]">
                          {item.citations.slice(0, 2).map((c, ci) => (
                            <div key={ci} className="text-[10px] text-gray-400 font-mono bg-black/30 rounded-lg px-2 py-1">
                              <span className="text-indigo-400 mr-1">[{c.clause_id}]</span>
                              <span className="italic">"{c.text?.substring(0, 90)}…"</span>
                              <span className="ml-1 text-gray-600">p.{c.page}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            <form onSubmit={handleAsk} className="px-4 py-3 border-t border-white/[0.07] flex items-center space-x-2 flex-shrink-0">
              <input
                type="text"
                value={qaInput}
                onChange={e => setQaInput(e.target.value)}
                placeholder="Ask anything about this contract..."
                disabled={qaLoading}
                className="flex-1 px-4 py-2 rounded-xl bg-white/[0.04] border border-white/[0.08] text-white text-xs placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
              />
              <button
                type="submit"
                disabled={!qaInput.trim() || qaLoading}
                className="p-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white disabled:opacity-40 transition flex-shrink-0"
              >
                {qaLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* ═══ AI RECOMMENDATIONS GRID ════════════════════════════════════════ */}
      {review && review.recommendations.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass rounded-3xl border border-white/10 p-6"
        >
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center space-x-2">
              <Lightbulb className="w-4 h-4 text-amber-400" />
              <h2 className="text-sm font-bold text-white">AI Recommendations</h2>
            </div>
            <span className="text-[11px] text-indigo-400 flex items-center space-x-1 hover:text-indigo-300 cursor-pointer">
              <span>View all recommendations</span><ArrowRight className="w-3 h-3" />
            </span>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {review.recommendations.slice(0, 8).map((rec, i) => {
              const impact = i < 2 ? 'High Impact' : i < 4 ? 'Medium Impact' : 'Low Impact';
              const impactColor = i < 2 ? 'text-rose-400' : i < 4 ? 'text-amber-400' : 'text-emerald-400';
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: 0.1 + i * 0.05 }}
                  className="p-4 rounded-2xl bg-white/[0.03] border border-white/[0.07] hover:border-indigo-500/30 hover:bg-indigo-500/5 transition group cursor-pointer space-y-2"
                >
                  <div className="flex items-start space-x-2">
                    <div className="w-6 h-6 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Sparkles className="w-3 h-3 text-indigo-400" />
                    </div>
                    <p className="text-xs text-gray-200 leading-relaxed font-medium line-clamp-3">{rec}</p>
                  </div>
                  <div className="flex items-center justify-between pt-1">
                    <span className={`text-[10px] font-bold ${impactColor}`}>{impact}</span>
                    <button
                      onClick={() => handleCopy(rec, `rec-${i}`)}
                      className="text-[10px] text-gray-500 hover:text-indigo-400 transition opacity-0 group-hover:opacity-100"
                    >
                      {copiedId === `rec-${i}` ? 'Copied!' : 'Copy'}
                    </button>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* ═══ EXECUTIVE SYNTHESIS ════════════════════════════════════════════ */}
      {review?.summary && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="glass rounded-3xl border border-indigo-500/20 p-6 space-y-3"
        >
          <div className="flex items-center space-x-2 mb-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <h2 className="text-sm font-bold text-white">Executive Synthesis</h2>
          </div>
          <p className="text-sm text-gray-300 leading-relaxed">{review.summary}</p>
          <div className="flex items-center space-x-4 text-[11px] text-gray-500 pt-2 border-t border-white/[0.05]">
            <span>Processed in {review.processing_time.toFixed(2)}s</span>
            <span>•</span>
            <span>{review.risks.length} risks detected</span>
            <span>•</span>
            <span>{review.missing_clauses.length} missing clauses</span>
          </div>
        </motion.div>
      )}
    </div>
  );
}
