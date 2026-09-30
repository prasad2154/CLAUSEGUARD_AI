import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, X, FileText, ShieldAlert, BookOpen, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const SAMPLE_SEARCH_RESULTS = [
  { id: '1', title: 'Master Services Agreement (MSA_2026_Final.pdf)', type: 'contract', path: '/review/doc-001', category: 'General Commercial' },
  { id: '2', title: 'Non-Disclosure Agreement (NDA_AcmeCorp.docx)', type: 'contract', path: '/review/doc-002', category: 'Confidentiality' },
  { id: '3', title: 'Uncapped Liability & Indemnification Risk', type: 'risk', path: '/playbook', category: 'Liability' },
  { id: '4', title: 'Governing Law & Jurisdiction Rule (Delaware/NY)', type: 'rule', path: '/playbook', category: 'Compliance' },
  { id: '5', title: 'SaaS Enterprise Subscription Agreement', type: 'contract', path: '/review/doc-003', category: 'SaaS & IP' },
];

export default function SearchModal({ isOpen, onClose }: SearchModalProps) {
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else setQuery('');
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const filtered = query.trim() === ''
    ? SAMPLE_SEARCH_RESULTS
    : SAMPLE_SEARCH_RESULTS.filter(item =>
        item.title.toLowerCase().includes(query.toLowerCase()) ||
        item.category.toLowerCase().includes(query.toLowerCase())
      );

  const handleSelect = (path: string) => {
    navigate(path);
    onClose();
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/80 backdrop-blur-md"
        />

        {/* Search Panel */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: -20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -20 }}
          className="relative w-full max-w-2xl bg-[#0B0F17] border border-white/10 rounded-2xl shadow-2xl z-10 text-gray-200 overflow-hidden"
        >
          {/* Input Bar */}
          <div className="p-4 border-b border-white/10 flex items-center space-x-3 bg-white/[0.02]">
            <Search className="w-5 h-5 text-indigo-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search contracts, clauses, playbook rules, or risks..."
              className="w-full bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none"
              autoFocus
            />
            <button onClick={onClose} className="p-1 rounded-lg text-gray-400 hover:text-white">
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Results List */}
          <div className="max-h-96 overflow-y-auto p-2 space-y-1">
            {filtered.length === 0 ? (
              <div className="p-8 text-center text-sm text-gray-500">
                No matching contracts or playbook rules found for "{query}".
              </div>
            ) : (
              filtered.map((item) => (
                <div
                  key={item.id}
                  onClick={() => handleSelect(item.path)}
                  className="flex items-center justify-between p-3 rounded-xl hover:bg-white/[0.05] cursor-pointer group transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-2 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400">
                      {item.type === 'contract' && <FileText className="w-4 h-4" />}
                      {item.type === 'risk' && <ShieldAlert className="w-4 h-4 text-amber-400" />}
                      {item.type === 'rule' && <BookOpen className="w-4 h-4 text-purple-400" />}
                    </div>
                    <div>
                      <div className="text-sm font-medium text-white group-hover:text-indigo-300 transition-colors">
                        {item.title}
                      </div>
                      <div className="text-xs text-gray-500">
                        {item.category} • {item.type.toUpperCase()}
                      </div>
                    </div>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-600 group-hover:text-white group-hover:translate-x-1 transition-all" />
                </div>
              ))
            )}
          </div>

          <div className="p-3 bg-white/[0.02] border-t border-white/5 flex items-center justify-between text-[11px] text-gray-500">
            <span>Press <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-gray-300">Esc</kbd> to close</span>
            <span>Use <kbd className="px-1.5 py-0.5 rounded bg-white/10 text-gray-300">⌘K</kbd> anytime</span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
