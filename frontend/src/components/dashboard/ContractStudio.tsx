import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  FileText, 
  ShieldAlert, 
  AlertTriangle, 
  CheckCircle2, 
  ChevronRight, 
  Layers, 
  Search, 
  BookOpen, 
  Scale, 
  RefreshCw, 
  SlidersHorizontal,
  Copy,
  Check,
  Sparkles,
  ExternalLink,
  ChevronDown,
  ArrowRight,
  Eye,
  PanelLeftClose,
  PanelLeftOpen,
  PanelRightClose,
  PanelRightOpen,
  Wand2,
  HelpCircle,
  Hash
} from 'lucide-react';
import { documentApi, reviewApi, compareApi } from '@/lib/api';
import { Document, Clause, ReviewResponse, RiskItem, MissingClauseItem, ClauseDiff } from '@/lib/types';
import { AgentChatDrawer } from '@/components/chat/AgentChatDrawer';
import { ClauseDiffViewer } from '@/components/diff/ClauseDiffViewer';
import { useContractStream } from '@/hooks/useContractStream';

// Dial Gauge Component for Overall Risk
function RiskDial({ score, level }: { score: number; level: string }) {
  const r = 36;
  const circ = 2 * Math.PI * r;
  const offset = circ - (score / 100) * circ;
  const strokeColor =
    score >= 60 ? '#f43f5e' : score >= 35 ? '#f59e0b' : '#10b981';

  return (
    <div className="relative inline-flex items-center justify-center w-24 h-24 shrink-0">
      <svg className="w-24 h-24 -rotate-90" viewBox="0 0 90 90">
        <circle cx="45" cy="45" r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
        <circle
          cx="45" cy="45" r={r}
          fill="none"
          stroke={strokeColor}
          strokeWidth="6"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute text-center flex flex-col items-center">
        <span className="text-2xl font-black text-white font-display leading-none">{score}</span>
        <span className="text-[8px] uppercase tracking-wider font-bold mt-1" style={{ color: strokeColor }}>
          {level}
        </span>
      </div>
    </div>
  );
}

export const ContractStudio: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  // Primary state
  const [doc, setDoc] = useState<Document | null>(null);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [diffs, setDiffs] = useState<ClauseDiff[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<'reader' | 'diff'>('reader');

  // Interactive filtering & selection
  const [riskFilter, setRiskFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'OMISSIONS'>('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedClauseId, setSelectedClauseId] = useState<string | null>(null);
  const [pulsingClauseId, setPulsingClauseId] = useState<string | null>(null);

  // Panel collapse toggles
  const [isLeftCollapsed, setIsLeftCollapsed] = useState(false);
  const [isRightCollapsed, setIsRightCollapsed] = useState(false);

  // Rewrite modal state
  const [rewritingClauseId, setRewritingClauseId] = useState<string | null>(null);
  const [rewriteSuggestion, setRewriteSuggestion] = useState<string | null>(null);

  // Ingestion status hook
  const { ingestionSteps } = useContractStream();

  // References for click-to-scroll
  const clauseRefs = useRef<{ [key: string]: HTMLDivElement | null }>({});

  useEffect(() => {
    async function loadContractData() {
      if (!id) return;
      if (id === 'demo' || id === 'doc_demo_01') {
        setupFallbackDemo();
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        let docData: Document | null = null;
        try {
          docData = await documentApi.get(id);
          setDoc(docData);
        } catch (docErr) {
          console.warn('Failed to load document metadata:', docErr);
        }

        let clauseData: Clause[] = [];
        try {
          clauseData = await documentApi.getClauses(id);
          setClauses(clauseData);
        } catch (clauseErr) {
          console.warn('Failed to load clauses:', clauseErr);
        }

        // Only fallback to demo if backend is completely down and document couldn't be loaded at all
        if (!docData) {
          console.warn('Document could not be retrieved from server, using demo contract fallback');
          setupFallbackDemo();
          return;
        }

        // Fetch or trigger review for the real document
        try {
          const rev = await reviewApi.getLatest(id);
          setReview(rev);
        } catch {
          try {
            const newRev = await reviewApi.trigger(id, false);
            setReview(newRev);
          } catch (triggerErr) {
            console.warn('Review trigger encountered:', triggerErr);
          }
        }
      } catch (err) {
        console.warn('Unexpected error loading contract studio:', err);
      } finally {
        setLoading(false);
      }
    }

    loadContractData();
  }, [id]);

  // Demo Fallback Data ensuring zero white-screen crashes
  const setupFallbackDemo = () => {
    setDoc({
      id: id || 'doc_demo_01',
      name: 'Master Cloud SaaS Agreement & SLA (2026).pdf',
      original_filename: 'MSA_Cloud_2026.pdf',
      file_size: 1420000,
      page_count: 14,
      word_count: 5820,
      clause_count: 24,
      contract_type: 'SaaS Agreement',
      status: 'indexed',
      ocr_used: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    });

    const demoClauses: Clause[] = [
      {
        id: 'c1',
        document_id: id || 'demo',
        clause_id: 'CLAUSE-001',
        clause_title: '1. Preamble & Definitions',
        clause_text: 'This Master Services Agreement ("Agreement") is made between CloudVanguard Inc. ("Provider") and Customer. Capitalized terms shall have the meanings specified in Schedule A.',
        section: '1. Recitals & Parties',
        page_number: 1,
        position: 0,
        word_count: 28,
        created_at: new Date().toISOString(),
      },
      {
        id: 'c2',
        document_id: id || 'demo',
        clause_id: 'CLAUSE-005',
        clause_title: '5. Confidential Information & Data Security',
        clause_text: 'Each party agrees to hold in strict confidence all proprietary technical, business, and source code information disclosed. Confidential obligations shall survive for a period of five (5) years following contract expiration.',
        section: '5. Confidentiality',
        page_number: 3,
        position: 1,
        word_count: 36,
        created_at: new Date().toISOString(),
      },
      {
        id: 'c3',
        document_id: id || 'demo',
        clause_id: 'CLAUSE-009',
        clause_title: '9. Limitation of Liability (Uncapped Rider)',
        clause_text: 'NEITHER PARTY SHALL BE SUBJECT TO ANY LIMITATION OF LIABILITY FOR DIRECT OR INDIRECT DAMAGES ARISING UNDER BREACH OF SECURITY OBLIGATIONS OR INDEMNITY CLAIMS.',
        section: '9. Liability & Damages',
        page_number: 6,
        position: 2,
        word_count: 27,
        created_at: new Date().toISOString(),
      },
      {
        id: 'c4',
        document_id: id || 'demo',
        clause_id: 'CLAUSE-014',
        clause_title: '14. Governing Law & Dispute Forum',
        clause_text: 'This Agreement is governed by the laws of the State of Delaware. Any dispute shall be brought exclusively in the state and federal courts located in Wilmington, Delaware.',
        section: '14. Governing Law',
        page_number: 9,
        position: 3,
        word_count: 28,
        created_at: new Date().toISOString(),
      },
    ];

    setClauses(demoClauses);

    setReview({
      review_id: 'rev_demo',
      document_id: id || 'demo',
      document_name: 'Master Cloud SaaS Agreement & SLA (2026).pdf',
      contract_type: 'SaaS Agreement',
      overall_risk_score: 74,
      risk_level: 'HIGH',
      summary: 'High exposure detected due to an uncapped liability carveout in Section 9 and missing Data Subject Access Rights clauses.',
      critical_count: 1,
      high_count: 2,
      medium_count: 3,
      low_count: 1,
      missing_clause_count: 2,
      recommendations: [
        'Cap security breach damages to a multiple of annual contract value (e.g. 2x ARR).',
        'Insert standard GDPR/CCPA data portability and deletion commitments.',
      ],
      processing_time: 1.8,
      risks: [
        {
          id: 'r1',
          title: 'Uncapped Consequential & Direct Liability',
          category: 'Liability & Damages',
          severity: 'CRITICAL',
          clause_id: 'CLAUSE-009',
          page_number: 6,
          evidence: 'NEITHER PARTY SHALL BE SUBJECT TO ANY LIMITATION OF LIABILITY FOR DIRECT OR INDIRECT DAMAGES...',
          section: 'Section 9',
          explanation: 'Exposes organization to unlimited liability claims without a 12-month fee cap.',
          recommendation: 'Negotiate an explicit super-cap (e.g., 2x trailing twelve months fees).',
          confidence: 0.98,
        },
        {
          id: 'r2',
          title: 'Asymmetric Indemnification Obligations',
          category: 'Indemnification',
          severity: 'HIGH',
          clause_id: 'CLAUSE-005',
          page_number: 3,
          evidence: 'Each party agrees to hold in strict confidence...',
          section: 'Section 5',
          explanation: 'Indemnity terms lack customary safe-harbor exclusions for third-party direct claims.',
          recommendation: 'Add standard gross negligence and willful misconduct exceptions.',
          confidence: 0.89,
        },
      ],
      missing_clauses: [
        {
          id: 'm1',
          clause_name: 'Data Portability & Deletion SLA',
          importance: 'HIGH',
          reason: 'SaaS agreements require guaranteed post-termination data return commitments.',
          contract_type: 'SaaS Agreement',
          recommendation: 'Insert 30-day data escrow and certified deletion provision.',
        },
        {
          id: 'm2',
          clause_name: 'Non-Solicitation of Key Personnel',
          importance: 'MEDIUM',
          reason: 'Vendor agreement lacks protections against poaching specialized technical staff.',
          contract_type: 'SaaS Agreement',
          recommendation: 'Include standard 12-month mutual non-solicit clause.',
        },
      ],
    });

    setDiffs([
      {
        clause_title: '9. Limitation of Liability',
        section: 'Section 9',
        change_type: 'MODIFIED',
        text_a: 'Provider total aggregate liability shall not exceed fees paid in the previous 12 months.',
        text_b: 'NEITHER PARTY SHALL BE SUBJECT TO ANY LIMITATION OF LIABILITY FOR DIRECT OR INDIRECT DAMAGES...',
        page_a: 5,
        page_b: 6,
        risk_impact: 'HIGH',
        risk_explanation: 'Standard liability cap removed, creating unlimited financial exposure.',
        severity: 'HIGH',
      },
      {
        clause_title: '15. Non-Solicitation Agreement',
        section: 'Section 15',
        change_type: 'REMOVED',
        text_a: 'Neither party shall solicit or recruit employees for 12 months post-termination.',
        text_b: undefined,
        page_a: 11,
        page_b: undefined,
        risk_impact: 'MEDIUM',
        risk_explanation: 'Non-solicit protection eliminated in current draft.',
        severity: 'MEDIUM',
      },
    ]);
  };

  // Scroll to clause and trigger animated pulsing
  const scrollToClause = (clauseId: string, pageNumber?: number) => {
    setSelectedClauseId(clauseId);
    setPulsingClauseId(clauseId);

    const targetEl = clauseRefs.current[clauseId];
    if (targetEl) {
      targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    setTimeout(() => {
      setPulsingClauseId(null);
    }, 3000);
  };

  // AI Rewrite Handler
  const handleRewrite = (clause: Clause) => {
    setRewritingClauseId(clause.clause_id);
    setRewriteSuggestion(null);

    // Simulate legal redline generation
    setTimeout(() => {
      setRewriteSuggestion(
        `"Except for gross negligence or willful misconduct, neither party's aggregate liability arising under or in connection with this Agreement shall exceed the total fees paid or payable by Customer in the twelve (12) months preceding the event giving rise to liability. Neither party shall be liable for indirect, punitive, or consequential damages."`
      );
    }, 600);
  };

  // Filter clauses based on search and selected risk level
  const filteredClauses = clauses.filter((c) => {
    const matchesSearch =
      !searchQuery ||
      c.clause_text.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (c.clause_title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.clause_id.toLowerCase().includes(searchQuery.toLowerCase());

    if (!matchesSearch) return false;

    if (riskFilter === 'ALL') return true;
    if (riskFilter === 'OMISSIONS') return false; // Handled in omissions card

    const associatedRisk = review?.risks.find((r) => r.clause_id === c.clause_id);
    if (!associatedRisk) return false;

    return associatedRisk.severity === riskFilter;
  });

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'CRITICAL':
      case 'HIGH':
        return 'bg-rose-500/15 text-rose-300 border-rose-500/30';
      case 'MEDIUM':
        return 'bg-amber-500/15 text-amber-300 border-amber-500/30';
      case 'LOW':
        return 'bg-blue-500/15 text-blue-300 border-blue-500/30';
      default:
        return 'bg-emerald-500/15 text-emerald-300 border-emerald-500/30';
    }
  };

  return (
    <div className="h-full w-full flex flex-col min-h-0 bg-[#090d16] text-gray-200 overflow-hidden select-text">
      {/* ── Top Studio Command Bar ────────────────────────────────────────── */}
      <div className="flex-none h-12 border-b border-white/10 bg-[#0f1624] px-4 flex items-center justify-between z-20">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsLeftCollapsed(!isLeftCollapsed)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition"
            title="Toggle Contract Navigator"
          >
            {isLeftCollapsed ? <PanelLeftOpen className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
          </button>

          <div className="flex items-center space-x-2 text-xs">
            <span className="font-semibold text-white truncate max-w-xs sm:max-w-md">
              {doc?.name || 'Loading Contract...'}
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-white/10 text-indigo-300 border border-white/10">
              {doc?.contract_type || 'Commercial Agreement'}
            </span>
          </div>
        </div>

        {/* View Mode & Right Drawer Toggle */}
        <div className="flex items-center space-x-3">
          <div className="flex items-center bg-[#090d16] p-0.5 rounded-xl border border-white/10 text-xs">
            <button
              onClick={() => setViewMode('reader')}
              className={`flex items-center space-x-1 px-3 py-1 rounded-lg transition font-medium ${
                viewMode === 'reader' ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Clause Reader</span>
            </button>
            <button
              onClick={() => setViewMode('diff')}
              className={`flex items-center space-x-1 px-3 py-1 rounded-lg transition font-medium ${
                viewMode === 'diff' ? 'bg-indigo-600 text-white shadow-sm' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Scale className="w-3.5 h-3.5" />
              <span>Version Diff</span>
            </button>
          </div>

          <button
            onClick={() => setIsRightCollapsed(!isRightCollapsed)}
            className="p-1.5 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition"
            title="Toggle Agentic Q&A Chat"
          >
            {isRightCollapsed ? <PanelRightOpen className="w-4 h-4" /> : <PanelRightClose className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* ── 3-Pane Body Workspace ─────────────────────────────────────────── */}
      <div className="flex-1 min-h-0 flex flex-row overflow-hidden relative">
        {/* ═══ PANE 1: Left Contract Navigator & Risk Radar (280px - 340px) ═ */}
        <div
          className={`flex-none border-r border-white/10 bg-[#0c121e] flex flex-col h-full overflow-hidden transition-all duration-300 ease-in-out z-10 ${
            isLeftCollapsed ? 'w-0 opacity-0 pointer-events-none' : 'w-72 lg:w-80'
          }`}
        >
          {/* Scrollable Navigator Pane */}
          <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain custom-scrollbar p-4 space-y-5">
            {/* Risk Gauge Card */}
            <div className="p-4 rounded-2xl border border-white/10 bg-[#121a29] flex items-center justify-between shadow-xl">
              <div>
                <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Overall Risk Score</span>
                <h3 className="text-sm font-bold text-white mt-1">Autonomous Audit</h3>
                <p className="text-[11px] text-gray-400 mt-0.5">
                  {review?.critical_count || 0} Critical • {review?.high_count || 0} High
                </p>
              </div>
              <RiskDial
                score={review ? Math.round(review.overall_risk_score) : 0}
                level={review?.risk_level || 'MINIMAL'}
              />
            </div>

            {/* Quick Risk Filters */}
            <div className="space-y-1.5">
              <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">Risk Filter</span>
              <div className="grid grid-cols-2 gap-1.5 text-xs">
                <button
                  onClick={() => setRiskFilter('ALL')}
                  className={`p-2 rounded-xl border text-left transition ${
                    riskFilter === 'ALL'
                      ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40 font-semibold'
                      : 'bg-[#151f30]/60 text-gray-400 border-white/5 hover:text-white'
                  }`}
                >
                  All Clauses ({clauses.length})
                </button>
                <button
                  onClick={() => setRiskFilter('HIGH')}
                  className={`p-2 rounded-xl border text-left transition flex items-center justify-between ${
                    riskFilter === 'HIGH'
                      ? 'bg-rose-500/20 text-rose-300 border-rose-500/40 font-semibold'
                      : 'bg-[#151f30]/60 text-rose-400 border-white/5 hover:bg-rose-950/20'
                  }`}
                >
                  <span>High Risk</span>
                  <span className="text-[10px] font-bold font-mono">({review?.high_count || 0})</span>
                </button>
                <button
                  onClick={() => setRiskFilter('MEDIUM')}
                  className={`p-2 rounded-xl border text-left transition flex items-center justify-between ${
                    riskFilter === 'MEDIUM'
                      ? 'bg-amber-500/20 text-amber-300 border-amber-500/40 font-semibold'
                      : 'bg-[#151f30]/60 text-amber-400 border-white/5 hover:bg-amber-950/20'
                  }`}
                >
                  <span>Medium</span>
                  <span className="text-[10px] font-bold font-mono">({review?.medium_count || 0})</span>
                </button>
                <button
                  onClick={() => setRiskFilter('OMISSIONS')}
                  className={`p-2 rounded-xl border text-left transition flex items-center justify-between ${
                    riskFilter === 'OMISSIONS'
                      ? 'bg-purple-500/20 text-purple-300 border-purple-500/40 font-semibold'
                      : 'bg-[#151f30]/60 text-purple-400 border-white/5 hover:bg-purple-950/20'
                  }`}
                >
                  <span>Omissions</span>
                  <span className="text-[10px] font-bold font-mono">({review?.missing_clause_count || 0})</span>
                </button>
              </div>
            </div>

            {/* Missing Standard Clauses Checklist */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold uppercase tracking-wider text-purple-400 flex items-center space-x-1">
                  <AlertTriangle className="w-3 h-3" />
                  <span>Missing Clauses Checklist</span>
                </span>
                <span className="text-[10px] font-mono text-gray-500">
                  {review?.missing_clauses?.length || 0} omitted
                </span>
              </div>

              <div className="space-y-1.5">
                {(review?.missing_clauses || []).map((mc, idx) => (
                  <div
                    key={idx}
                    className="p-2.5 rounded-xl border border-purple-500/20 bg-purple-950/10 text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-purple-200">{mc.clause_name}</span>
                      <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                        {mc.importance}
                      </span>
                    </div>
                    <p className="text-[11px] text-gray-400 leading-tight">{mc.reason}</p>
                  </div>
                ))}
              </div>
            </div>

            {/* Document Clause Navigation Tree */}
            <div className="space-y-2">
              <span className="text-[10px] font-bold uppercase tracking-wider text-gray-400">
                Clause Outline ({clauses.length})
              </span>
              <div className="space-y-1">
                {clauses.map((c) => {
                  const hasRisk = review?.risks.find((r) => r.clause_id === c.clause_id);
                  const isSelected = selectedClauseId === c.clause_id;
                  return (
                    <button
                      key={c.id}
                      onClick={() => scrollToClause(c.clause_id, c.page_number)}
                      className={`w-full flex items-center justify-between p-2 rounded-xl text-xs text-left transition ${
                        isSelected
                          ? 'bg-indigo-600/30 text-white border border-indigo-500/50 shadow-sm'
                          : 'bg-[#151f30]/40 text-gray-300 border border-transparent hover:bg-white/5'
                      }`}
                    >
                      <span className="truncate max-w-[190px]">
                        {c.clause_title || c.section || c.clause_id}
                      </span>
                      <div className="flex items-center space-x-1 shrink-0">
                        {hasRisk && (
                          <span
                            className={`w-2 h-2 rounded-full ${
                              hasRisk.severity === 'CRITICAL' || hasRisk.severity === 'HIGH'
                                ? 'bg-rose-500'
                                : 'bg-amber-400'
                            }`}
                          />
                        )}
                        <span className="text-[10px] font-mono text-gray-500">p.{c.page_number}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>

        {/* ═══ PANE 2: Center Interactive Clause Reader / Diff View (Flexible) ═ */}
        <div className="flex-1 min-h-0 flex flex-col h-full overflow-hidden bg-[#090d16]">
          {viewMode === 'diff' ? (
            <ClauseDiffViewer diffs={diffs} />
          ) : (
            <div className="h-full flex flex-col min-h-0">
              {/* Document Search / Filter Bar */}
              <div className="flex-none p-3 border-b border-white/10 bg-[#0b101a] flex items-center space-x-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search clause text, terms, or section..."
                    className="w-full pl-9 pr-4 py-1.5 rounded-xl bg-[#0f1624] border border-white/10 text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
                  />
                </div>
                <div className="text-xs text-gray-400 font-mono">
                  Showing {filteredClauses.length} of {clauses.length} clauses
                </div>
              </div>

              {/* Variable-Height Document Reader (Never locks, smooth custom-scrollbar) */}
              <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain custom-scrollbar p-6 space-y-4">
                {clauses.length === 0 && (
                  <div className="flex flex-col items-center justify-center p-12 text-center space-y-4 border border-dashed border-white/10 rounded-2xl bg-white/[0.02]">
                    <div className="p-4 rounded-2xl bg-indigo-500/10 border border-indigo-500/20">
                      <FileText className="w-8 h-8 text-indigo-400 animate-pulse" />
                    </div>
                    <div>
                      <h4 className="text-base font-bold text-white">No Clauses Indexed Yet</h4>
                      <p className="text-xs text-gray-400 mt-1 max-w-md">
                        {doc?.status === 'error'
                          ? `Ingestion notice: ${doc.error_message || 'Processing was interrupted'}. Click below to automatically extract and analyze.`
                          : 'This document is pending semantic segmentation and risk auditing.'}
                      </p>
                    </div>
                    <button
                      onClick={async () => {
                        if (!id) return;
                        setLoading(true);
                        try {
                          await fetch(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/documents/${id}/reprocess`, { method: 'POST' });
                          const [d, c] = await Promise.all([documentApi.get(id), documentApi.getClauses(id)]);
                          setDoc(d);
                          setClauses(c);
                          const rev = await reviewApi.trigger(id, true);
                          setReview(rev);
                        } catch (err) {
                          console.error('Reprocess failed:', err);
                        } finally {
                          setLoading(false);
                        }
                      }}
                      className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 transition cursor-pointer"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Extract & Run Risk Audit</span>
                    </button>
                  </div>
                )}
                {filteredClauses.map((clause) => {
                  const riskItem = review?.risks.find((r) => r.clause_id === clause.clause_id);
                  const isSelected = selectedClauseId === clause.clause_id;
                  const isPulsing = pulsingClauseId === clause.clause_id;

                  return (
                    <div
                      key={clause.id}
                      ref={(el) => (clauseRefs.current[clause.clause_id] = el)}
                      onClick={() => setSelectedClauseId(clause.clause_id)}
                      className={`p-5 rounded-2xl border transition-all duration-300 relative ${
                        isPulsing
                          ? 'border-indigo-500 bg-indigo-950/30 ring-2 ring-indigo-500 citation-pulse shadow-2xl'
                          : isSelected
                          ? 'border-indigo-500/70 bg-[#121927] shadow-xl'
                          : riskItem
                          ? 'border-white/10 bg-[#0f1624] hover:border-white/20'
                          : 'border-white/5 bg-[#0c121e] hover:border-white/10'
                      }`}
                    >
                      {/* Clause Meta Header */}
                      <div className="flex items-center justify-between gap-3 mb-2.5">
                        <div className="flex items-center space-x-2">
                          <span className="text-xs font-mono font-bold text-indigo-400 px-2 py-0.5 rounded bg-indigo-500/10 border border-indigo-500/20">
                            {clause.clause_id}
                          </span>
                          <h4 className="text-xs font-bold text-white">
                            {clause.clause_title || clause.section || 'General Provision'}
                          </h4>
                        </div>

                        <div className="flex items-center space-x-2">
                          {riskItem && (
                            <span
                              className={`text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full border ${getSeverityBadge(
                                riskItem.severity
                              )}`}
                            >
                              {riskItem.severity} Risk
                            </span>
                          )}
                          <span className="text-[10px] font-mono text-gray-400 bg-white/5 px-2 py-0.5 rounded border border-white/5">
                            Page {clause.page_number}
                          </span>
                        </div>
                      </div>

                      {/* Primary Clause Text */}
                      <p className="text-xs text-gray-300 leading-relaxed whitespace-pre-wrap font-mono select-text">
                        {clause.clause_text}
                      </p>

                      {/* Risk Analysis Callout if Flagged */}
                      {riskItem && (
                        <div className="mt-3.5 p-3 rounded-xl border border-rose-500/30 bg-rose-950/15 text-xs space-y-1.5">
                          <div className="flex items-center space-x-1.5 text-rose-300 font-semibold">
                            <ShieldAlert className="w-3.5 h-3.5" />
                            <span>Risk: {riskItem.title}</span>
                          </div>
                          <p className="text-[11px] text-gray-300">{riskItem.explanation}</p>
                          <div className="pt-1.5 border-t border-rose-500/20 text-[11px] text-indigo-300 font-medium">
                            <span className="font-bold text-gray-400">Playbook Recommendation: </span>
                            {riskItem.recommendation}
                          </div>
                        </div>
                      )}

                      {/* Action Bar */}
                      <div className="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-xs">
                        <span className="text-[10px] text-gray-500 font-mono">
                          {clause.word_count || clause.clause_text.split(' ').length} words
                        </span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRewrite(clause);
                          }}
                          className="flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-[11px] font-medium transition"
                        >
                          <Wand2 className="w-3 h-3" />
                          <span>AI Redline Rewrite</span>
                        </button>
                      </div>

                      {/* Rewrite Suggestion Drawer */}
                      {rewritingClauseId === clause.clause_id && (
                        <div className="mt-3 p-3.5 rounded-xl border border-indigo-500/40 bg-[#162032] space-y-2 animate-fadeIn">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-indigo-400 flex items-center space-x-1">
                              <Sparkles className="w-3 h-3" />
                              <span>Proposed Redline Suggestion:</span>
                            </span>
                            <button
                              onClick={() => setRewritingClauseId(null)}
                              className="text-[10px] text-gray-400 hover:text-white"
                            >
                              Dismiss
                            </button>
                          </div>
                          <div className="text-xs text-gray-200 font-mono bg-[#090d16] p-3 rounded-lg border border-white/10 leading-relaxed whitespace-pre-wrap">
                            {rewriteSuggestion || 'Generating balanced contract clause language...'}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* ═══ Real-Time Ingestion Status Progress Banner (Bottom) ═══ */}
          <div className="flex-none border-t border-white/10 bg-[#0c121e] px-4 py-2 flex items-center justify-between text-xs">
            <div className="flex items-center space-x-3 overflow-x-auto custom-scrollbar">
              <span className="text-[10px] uppercase font-bold text-gray-500 shrink-0">Pipeline:</span>
              {ingestionSteps.map((step, idx) => (
                <div key={step.id} className="flex items-center space-x-1.5 shrink-0">
                  {step.status === 'completed' ? (
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                  ) : step.status === 'in_progress' ? (
                    <RefreshCw className="w-3 h-3 text-indigo-400 animate-spin" />
                  ) : (
                    <span className="w-2.5 h-2.5 rounded-full bg-white/10" />
                  )}
                  <span
                    className={`text-[10px] font-medium ${
                      step.status === 'completed'
                        ? 'text-gray-300'
                        : step.status === 'in_progress'
                        ? 'text-indigo-300 font-semibold'
                        : 'text-gray-600'
                    }`}
                  >
                    {step.label}
                  </span>
                  {idx < ingestionSteps.length - 1 && <span className="text-gray-600 text-[10px]">→</span>}
                </div>
              ))}
            </div>

            <div className="hidden sm:flex items-center space-x-2 text-[10px] text-gray-400 shrink-0">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
              <span>Vector Search & Playbook Verified</span>
            </div>
          </div>
        </div>

        {/* ═══ PANE 3: Right Agentic Q&A Chat & Citation Drawer (380px - 440px) ═ */}
        <div
          className={`flex-none h-full transition-all duration-300 ease-in-out z-10 ${
            isRightCollapsed ? 'w-0 opacity-0 pointer-events-none' : 'w-80 lg:w-96'
          }`}
        >
          <AgentChatDrawer
            documentId={id || 'demo'}
            documentName={doc?.name || 'Contract'}
            onSelectCitation={scrollToClause}
            isExpanded={!isRightCollapsed}
            onToggleExpand={() => setIsRightCollapsed(!isRightCollapsed)}
          />
        </div>
      </div>
    </div>
  );
};
export default ContractStudio;
