import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FileText, 
  Search, 
  Trash2, 
  ShieldAlert, 
  Scale, 
  Calendar, 
  Clock, 
  Layers, 
  Loader2, 
  Plus, 
  Filter
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { documentApi } from '../lib/api';
import { Document } from '../lib/types';

export default function DocumentLibrary() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedType, setSelectedType] = useState<string>('All');
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      const res = await documentApi.list(0, 100);
      setDocuments(res.documents);
    } catch (err) {
      console.error('Failed to load documents:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocuments();
  }, []);

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to permanently delete this contract and all its vector embeddings?')) {
      return;
    }
    try {
      setDeletingId(id);
      await documentApi.delete(id);
      setDocuments(prev => prev.filter(d => d.id !== id));
    } catch (err) {
      alert('Failed to delete document');
    } finally {
      setDeletingId(null);
    }
  };

  // Derive available categories
  const types = ['All', ...Array.from(new Set(documents.map(d => d.contract_type || 'Commercial Agreement')))];

  const filteredDocs = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          (doc.contract_type && doc.contract_type.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesType = selectedType === 'All' || doc.contract_type === selectedType || (!doc.contract_type && selectedType === 'Commercial Agreement');
    return matchesSearch && matchesType;
  });

  return (
    <div className="flex-1 h-full min-h-0 overflow-y-auto overscroll-contain custom-scrollbar p-4 sm:p-8 max-w-7xl mx-auto w-full space-y-8 pb-24">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-display font-extrabold text-white tracking-tight">
            Contract Vault
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            Browse and manage all parsed, embedded, and reviewed legal agreements.
          </p>
        </div>

        <button
          onClick={() => navigate('/upload')}
          className="flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white text-xs font-semibold hover:from-indigo-600 hover:to-purple-700 transition shadow-lg shadow-indigo-500/25"
        >
          <Plus className="w-4 h-4" />
          <span>Upload Contract</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-4 p-4 rounded-2xl glass border border-white/5">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-gray-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by contract name or clause type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-xl bg-white/[0.04] border border-white/10 text-white placeholder-gray-500 text-xs focus:outline-none focus:border-indigo-500 transition"
          />
        </div>

        <div className="flex items-center space-x-2 overflow-x-auto pb-1 md:pb-0">
          <Filter className="w-4 h-4 text-gray-400 shrink-0 mr-1" />
          {types.map((type) => (
            <button
              key={type}
              onClick={() => setSelectedType(type)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium whitespace-nowrap transition ${
                selectedType === type
                  ? 'bg-indigo-500 text-white shadow-md shadow-indigo-500/30'
                  : 'text-gray-400 hover:text-white bg-white/[0.02] hover:bg-white/5 border border-white/5'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Document Grid */}
      {loading ? (
        <div className="py-24 text-center">
          <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mx-auto mb-3" />
          <p className="text-gray-400 text-xs">Loading contract vault...</p>
        </div>
      ) : filteredDocs.length === 0 ? (
        <div className="glass rounded-3xl p-12 text-center border border-dashed border-white/10">
          <FileText className="w-12 h-12 text-gray-600 mx-auto mb-3" />
          <h3 className="text-white font-semibold text-base mb-1">No contracts found</h3>
          <p className="text-gray-400 text-xs max-w-sm mx-auto mb-6">
            {searchQuery ? 'Try adjusting your search filters.' : 'Upload your first contract to begin AI-powered risk detection.'}
          </p>
          <button
            onClick={() => navigate('/upload')}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold transition"
          >
            Ingest First Document
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <AnimatePresence>
            {filteredDocs.map((doc) => (
              <motion.div
                key={doc.id}
                layout
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.96 }}
                className="glass p-6 rounded-2xl border border-white/5 hover:border-indigo-500/40 transition-all duration-300 flex flex-col justify-between group shadow-xl"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-4">
                    <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 shrink-0">
                      <FileText className="w-5 h-5" />
                    </div>
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-white/5 text-gray-300 border border-white/10">
                      {doc.contract_type || 'Commercial'}
                    </span>
                  </div>

                  <h3 className="text-white font-semibold text-base line-clamp-2 mb-2 group-hover:text-indigo-300 transition">
                    {doc.name}
                  </h3>

                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-400 my-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <div className="flex items-center space-x-2">
                      <Layers className="w-3.5 h-3.5 text-indigo-400" />
                      <span>{doc.clause_count} Clauses</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <FileText className="w-3.5 h-3.5 text-purple-400" />
                      <span>{doc.page_count} Pages</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Clock className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{doc.processing_time ? `${doc.processing_time.toFixed(1)}s` : 'Instant'}</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Calendar className="w-3.5 h-3.5 text-blue-400" />
                      <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-white/5 flex items-center justify-between gap-2">
                  <button
                    onClick={() => handleDelete(doc.id)}
                    disabled={deletingId === doc.id}
                    title="Delete document and embeddings"
                    className="p-2 rounded-xl text-gray-500 hover:text-rose-400 hover:bg-rose-500/10 transition"
                  >
                    {deletingId === doc.id ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      <Trash2 className="w-4 h-4" />
                    )}
                  </button>

                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => navigate(`/compare?docA=${doc.id}`)}
                      title="Compare against another version"
                      className="p-2 rounded-xl text-gray-400 hover:text-white hover:bg-white/10 transition"
                    >
                      <Scale className="w-4 h-4" />
                    </button>
                    <button
                      onClick={() => navigate(`/review/${doc.id}`)}
                      className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/30 text-xs font-semibold transition"
                    >
                      <ShieldAlert className="w-3.5 h-3.5" />
                      <span>Review Risks</span>
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
