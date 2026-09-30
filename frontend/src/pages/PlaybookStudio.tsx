import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { 
  BookOpen, 
  Plus, 
  Search, 
  X, 
  Loader2, 
  Trash2,
  Filter
} from 'lucide-react';

import { playbookApi } from '../lib/api';
import { PlaybookRule } from '../lib/types';

export default function PlaybookStudio() {
  const [rules, setRules] = useState<PlaybookRule[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);

  // New Rule Form State
  const [newName, setNewName] = useState('');
  const [newCategory, setNewCategory] = useState('Liability & Damages');
  const [newSeverity, setNewSeverity] = useState<'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW'>('HIGH');
  const [newDescription, setNewDescription] = useState('');
  const [newKeywords, setNewKeywords] = useState('');
  const [newRecommendation, setNewRecommendation] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchRules();
  }, []);

  const fetchRules = async () => {
    try {
      setLoading(true);
      const data = await playbookApi.list();
      setRules(data);
    } catch (err) {
      console.error('Failed to load playbook rules:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRule = async (rule: PlaybookRule) => {
    try {
      const updated = await playbookApi.update(rule.id, { enabled: !rule.enabled });
      setRules((prev) => prev.map((r) => (r.id === rule.id ? updated : r)));
    } catch (err) {
      alert('Failed to update rule status');
    }
  };

  const handleDeleteRule = async (id: string) => {
    if (!confirm('Are you sure you want to delete this rule?')) return;
    try {
      await playbookApi.delete(id);
      setRules((prev) => prev.map((r) => (r.id === id ? null : r)).filter(Boolean) as PlaybookRule[]);
    } catch (err) {
      alert('Failed to delete rule');
    }
  };

  const handleCreateRule = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim()) return;

    try {
      setSubmitting(true);
      const keywordsArray = newKeywords
        .split(',')
        .map((k) => k.trim())
        .filter(Boolean);

      const created = await playbookApi.create({
        name: newName.trim(),
        category: newCategory,
        severity: newSeverity,
        description: newDescription.trim(),
        detection_keywords: keywordsArray,
        recommendation: newRecommendation.trim(),
        enabled: true,
        missing_indicator: false,
      });

      setRules((prev) => [created, ...prev]);
      setShowAddModal(false);
      // Reset form
      setNewName('');
      setNewDescription('');
      setNewKeywords('');
      setNewRecommendation('');
    } catch (err: any) {
      alert(err?.response?.data?.detail || 'Failed to create playbook rule');
    } finally {
      setSubmitting(false);
    }
  };

  const categories = ['All', ...Array.from(new Set(rules.map((r) => r.category)))];

  const filteredRules = rules.filter((rule) => {
    const matchesCategory = selectedCategory === 'All' || rule.category === selectedCategory;
    const matchesSearch =
      rule.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (rule.description && rule.description.toLowerCase().includes(searchQuery.toLowerCase()));
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="flex-1 h-full min-h-0 overflow-y-auto overscroll-contain custom-scrollbar p-4 sm:p-8 max-w-7xl mx-auto w-full space-y-8 pb-24">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-extrabold text-white tracking-tight flex items-center space-x-3">
            <BookOpen className="w-8 h-8 text-indigo-400" />
            <span>Playbook & Risk Rules</span>
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Configure the legal compliance standards, liability thresholds, and required clause rules enforced by the AI agents.
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-semibold hover:from-indigo-600 hover:to-purple-700 transition shadow-lg shadow-indigo-500/25"
        >
          <Plus className="w-4 h-4" />
          <span>New Playbook Rule</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 p-4 rounded-2xl glass border border-white/5">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search rules, keywords, or legal explanations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-gray-500 text-xs focus:outline-none focus:border-indigo-500 transition"
          />
        </div>

        <div className="flex items-center space-x-2 overflow-x-auto pb-1 md:pb-0">
          <Filter className="w-4 h-4 text-gray-400 shrink-0 mr-1" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition ${
                selectedCategory === cat
                  ? 'bg-indigo-500 text-white shadow-md shadow-indigo-500/30'
                  : 'text-gray-400 hover:text-white bg-white/[0.02] hover:bg-white/5 border border-white/5'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Rules List */}
      {loading ? (
        <div className="py-24 text-center">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
          <p className="text-gray-400 text-xs">Loading playbook rules...</p>
        </div>
      ) : filteredRules.length === 0 ? (
        <div className="glass rounded-3xl p-12 text-center border border-dashed border-white/10">
          <BookOpen className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <h3 className="text-white font-semibold text-base mb-1">No rules found</h3>
          <p className="text-gray-400 text-xs max-w-sm mx-auto mb-6">
            Adjust search criteria or create a new risk policy.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {filteredRules.map((rule) => (
            <motion.div
              key={rule.id}
              layout
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className={`p-6 rounded-3xl border transition-all duration-300 flex flex-col justify-between ${
                rule.enabled
                  ? 'glass border-white/10'
                  : 'bg-white/[0.01] border-white/5 opacity-50'
              }`}
            >
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center space-x-2.5">
                    <span
                      className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        rule.severity === 'CRITICAL'
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
                          : rule.severity === 'HIGH'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40'
                          : 'bg-blue-500/20 text-blue-300 border border-blue-500/40'
                      }`}
                    >
                      {rule.severity}
                    </span>
                    <span className="text-xs text-gray-400 font-medium">
                      {rule.category}
                    </span>
                  </div>

                  {/* Toggle Button */}
                  <button
                    onClick={() => handleToggleRule(rule)}
                    className={`w-11 h-6 flex items-center rounded-full p-1 cursor-pointer transition-colors ${
                      rule.enabled ? 'bg-indigo-600' : 'bg-white/10'
                    }`}
                  >
                    <div
                      className={`bg-white w-4 h-4 rounded-full shadow-md transform transition-transform ${
                        rule.enabled ? 'translate-x-5' : 'translate-x-0'
                      }`}
                    />
                  </button>
                </div>

                <div>
                  <h3 className="text-base font-bold text-white mb-1.5">
                    {rule.name}
                  </h3>
                  <p className="text-xs text-gray-300 leading-relaxed font-sans">
                    {rule.description}
                  </p>
                </div>

                {/* Keywords Chips */}
                {rule.detection_keywords && rule.detection_keywords.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {rule.detection_keywords.map((kw, i) => (
                      <span
                        key={i}
                        className="px-2 py-0.5 rounded-md bg-white/[0.04] text-[10px] text-gray-400 font-mono border border-white/5"
                      >
                        #{kw}
                      </span>
                    ))}
                  </div>
                )}

                {/* Recommendation Draft */}
                {rule.recommendation && (
                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 text-xs text-gray-300 leading-relaxed">
                    <span className="text-[10px] uppercase font-bold text-indigo-400 block mb-1">
                      Enforced Standard & Remediation
                    </span>
                    {rule.recommendation}
                  </div>
                )}
              </div>

              <div className="pt-4 mt-4 border-t border-white/5 flex items-center justify-between text-[11px] text-gray-500">
                <span>
                  {rule.missing_indicator ? 'Flags when ABSENT' : 'Scans clause text'}
                </span>
                <button
                  onClick={() => handleDeleteRule(rule.id)}
                  className="text-gray-500 hover:text-rose-400 transition"
                  title="Remove Rule"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* New Rule Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="glass p-6 rounded-3xl border border-white/10 max-w-lg w-full space-y-4 shadow-2xl"
          >
            <div className="flex items-center justify-between pb-3 border-b border-white/10">
              <h2 className="text-lg font-bold text-white">Create New Playbook Rule</h2>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-gray-400 hover:text-white"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateRule} className="space-y-4 text-xs">
              <div>
                <label className="text-gray-400 font-semibold block mb-1">Rule Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g., Unilateral Non-Compete"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-gray-400 font-semibold block mb-1">Category</label>
                  <select
                    value={newCategory}
                    onChange={(e) => setNewCategory(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Liability & Damages">Liability & Damages</option>
                    <option value="Indemnification">Indemnification</option>
                    <option value="Compliance & Legal">Compliance & Legal</option>
                    <option value="Data Security & IP">Data Security & IP</option>
                    <option value="Confidentiality">Confidentiality</option>
                    <option value="Termination">Termination</option>
                  </select>
                </div>

                <div>
                  <label className="text-gray-400 font-semibold block mb-1">Severity</label>
                  <select
                    value={newSeverity}
                    onChange={(e) => setNewSeverity(e.target.value as any)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-white/10 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="LOW">LOW</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-gray-400 font-semibold block mb-1">Description</label>
                <textarea
                  rows={2}
                  placeholder="Explain why this clause creates risk..."
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-gray-400 font-semibold block mb-1">Detection Keywords (comma-separated)</label>
                <input
                  type="text"
                  placeholder="e.g., non-compete, covenant, restriction"
                  value={newKeywords}
                  onChange={(e) => setNewKeywords(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div>
                <label className="text-gray-400 font-semibold block mb-1">Recommended Redline / Remedy</label>
                <textarea
                  rows={2}
                  placeholder="Suggested replacement text or acceptable threshold..."
                  value={newRecommendation}
                  onChange={(e) => setNewRecommendation(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-3 border-t border-white/10">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl text-gray-400 hover:text-white"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white font-semibold shadow-lg shadow-indigo-500/25"
                >
                  {submitting ? 'Creating Rule...' : 'Save Playbook Rule'}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </div>
  );
}
