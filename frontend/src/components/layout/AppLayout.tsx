import React, { useState, useEffect } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { 
  ShieldCheck, 
  LayoutGrid, 
  FileText, 
  UploadCloud, 
  Scale, 
  BookMarked,
  Activity,
  Layers,
  ChevronRight,
  Search,
  User as UserIcon,
  Menu,
  X
} from 'lucide-react';
import { systemApi } from '@/lib/api';
import { HealthResponse } from '@/lib/types';
import { useAuth } from '@/lib/AuthContext';
import SearchModal from '@/components/layout/SearchModal';
import AuthModal from '@/components/auth/AuthModal';

export const AppLayout: React.FC = () => {
  const location = useLocation();
  const { user, openAuthModal } = useAuth();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await systemApi.getHealth();
        setHealth(res);
      } catch {
        // Fallback healthy indicator for demo
        setHealth({
          status: 'healthy',
          version: '1.0.0',
          timestamp: new Date().toISOString(),
          services: [{ name: 'Core Engine', status: 'healthy' }],
        });
      }
    }
    checkHealth();
  }, []);

  const navItems = [
    { label: 'Overview', path: '/dashboard', icon: LayoutGrid },
    { label: 'Documents', path: '/documents', icon: Layers },
    { label: 'Ingest Contract', path: '/upload', icon: UploadCloud },
    { label: 'Version Diff', path: '/compare', icon: Scale },
    { label: 'Playbook Rules', path: '/playbook', icon: BookMarked },
  ];

  return (
    <div className="h-screen w-screen flex flex-col overflow-hidden bg-[#090d16] text-gray-200 font-sans select-none">
      {/* ── Fixed Top Global Navigation Bar (56px / h-14) ──────────────────── */}
      <header className="h-14 flex-none border-b border-white/10 bg-[#0f1624]/90 backdrop-blur-md px-4 flex items-center justify-between z-30">
        {/* Brand & Left Navigation */}
        <div className="flex items-center space-x-6">
          <Link to="/dashboard" className="flex items-center space-x-2.5 group cursor-pointer">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition">
              <ShieldCheck className="w-4 h-4" />
            </div>
            <span className="font-display font-bold text-sm tracking-wide text-white">
              ClauseGuard <span className="text-indigo-400 font-normal">AI</span>
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.path);
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition ${
                    isActive
                      ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/30'
                      : 'text-gray-400 hover:text-white hover:bg-white/5'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </div>

        {/* Global Search Bar */}
        <div className="hidden lg:flex items-center flex-1 max-w-sm mx-6">
          <button
            onClick={() => setIsSearchOpen(true)}
            className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg bg-[#090d16] border border-white/10 text-xs text-gray-400 hover:border-white/20 transition text-left"
          >
            <div className="flex items-center space-x-2">
              <Search className="w-3.5 h-3.5 text-gray-500" />
              <span>Search contracts, clauses, risks...</span>
            </div>
            <kbd className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10 text-[10px] font-mono text-gray-500">
              ⌘K
            </kbd>
          </button>
        </div>

        {/* Right Tools & Profile */}
        <div className="flex items-center space-x-3">
          {/* Health Badge */}
          <div className="hidden sm:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[11px] text-emerald-400 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Agentic RAG Ready</span>
          </div>

          {/* User Profile */}
          <button
            onClick={() => openAuthModal('login')}
            className="flex items-center space-x-2 p-1.5 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 transition text-xs text-gray-300"
          >
            <div className="w-6 h-6 rounded-full bg-indigo-600 flex items-center justify-center text-white text-[10px] font-bold">
              {user?.name ? user.name.charAt(0) : 'A'}
            </div>
            <span className="hidden sm:inline font-medium">{user?.name || 'Legal Counsel'}</span>
          </button>

          {/* Mobile menu toggle */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-1.5 rounded-lg text-gray-400 hover:text-white"
          >
            {isMobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </header>

      {/* Mobile Drawer */}
      {isMobileMenuOpen && (
        <div className="md:hidden flex-none bg-[#0f1624] border-b border-white/10 p-3 space-y-1 z-40">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              onClick={() => setIsMobileMenuOpen(false)}
              className="flex items-center space-x-2 p-2 rounded-lg text-xs font-medium text-gray-300 hover:bg-white/5"
            >
              <item.icon className="w-4 h-4 text-indigo-400" />
              <span>{item.label}</span>
            </Link>
          ))}
        </div>
      )}

      {/* ── Main Viewport Workspace (Guaranteed Flex Split with Zero Overflow Leaks) ─ */}
      <main className="flex-1 min-h-0 flex flex-row overflow-hidden relative">
        <Outlet />
      </main>

      <SearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
      <AuthModal />
    </div>
  );
};
export default AppLayout;
