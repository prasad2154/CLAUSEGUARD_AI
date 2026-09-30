import { useState } from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldCheck, 
  LayoutGrid, 
  Layers, 
  UploadCloud, 
  SplitSquareHorizontal, 
  BookMarked,
  Search,
  Bell,
  LogOut,
  User as UserIcon,
  LogIn,
  Sparkles,
  ChevronDown
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useAuth } from '@/lib/AuthContext';
import SearchModal from '@/components/layout/SearchModal';
import AuthModal from '@/components/auth/AuthModal';

export default function MainLayout() {
  const location = useLocation();
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);

  const { user, isAuthenticated, logout, openAuthModal } = useAuth();

  const tabs = [
    { id: 'dashboard', label: 'Overview', path: '/dashboard', icon: LayoutGrid },
    { id: 'documents', label: 'Library', path: '/documents', icon: Layers },
    { id: 'upload', label: 'Analyze', path: '/upload', icon: UploadCloud },
    { id: 'compare', label: 'Compare', path: '/compare', icon: SplitSquareHorizontal },
    { id: 'playbook', label: 'Rules', path: '/playbook', icon: BookMarked },
  ];

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .toUpperCase()
      .substring(0, 2);
  };

  return (
    <div className="min-h-screen w-full mesh-bg flex flex-col items-center relative overflow-x-hidden text-gray-200 font-sans">
      
      {/* Top Header / Command Bar */}
      <header className="w-full max-w-7xl mx-auto px-6 h-20 flex items-center justify-between z-20 mt-2">
        <Link to="/dashboard">
          <motion.div 
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center space-x-3 cursor-pointer group"
          >
            <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg shadow-indigo-500/20 group-hover:shadow-indigo-500/40 transition-all duration-500">
              <ShieldCheck className="w-5 h-5 text-white" />
              <div className="absolute inset-0 rounded-xl ring-1 ring-white/20"></div>
            </div>
            <span className="font-display font-semibold tracking-wide text-lg text-white">ClauseGuard <span className="text-indigo-400 font-light">AI</span></span>
          </motion.div>
        </Link>

        {/* Search Command Input */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="flex-1 max-w-md mx-8"
        >
          <div 
            onClick={() => setIsSearchOpen(true)}
            className="relative group cursor-pointer"
          >
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 group-hover:text-indigo-400 transition-colors" />
            <input 
              type="text" 
              readOnly
              placeholder="Command + K to search contracts..." 
              className="w-full bg-white/[0.04] border border-white/[0.08] rounded-full py-2 pl-10 pr-4 text-sm text-gray-200 placeholder-gray-500 cursor-pointer focus:outline-none focus:ring-1 focus:ring-indigo-500/50 focus:bg-white/[0.06] transition-all duration-300"
            />
          </div>
        </motion.div>

        {/* Right Header Menu */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex items-center space-x-4 relative"
        >
          <button className="p-2 rounded-full hover:bg-white/[0.05] transition-colors relative text-gray-400 hover:text-white">
            <Bell className="w-5 h-5" />
            <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-indigo-500 rounded-full ring-2 ring-[#050505]"></span>
          </button>

          {/* User Profile Avatar Dropdown */}
          <div className="relative">
            <button
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              className="flex items-center space-x-2 p-1.5 rounded-full bg-white/[0.04] hover:bg-white/[0.08] border border-white/10 transition-all cursor-pointer"
            >
              {user?.avatarUrl ? (
                <img src={user.avatarUrl} alt={user.name} className="w-7 h-7 rounded-full object-cover" />
              ) : (
                <div className="w-7 h-7 rounded-full bg-indigo-600/80 flex items-center justify-center text-white text-xs font-bold">
                  {user ? getInitials(user.name) : 'G'}
                </div>
              )}
              <span className="text-xs font-medium text-gray-200 max-w-[100px] truncate hidden sm:inline">
                {user ? user.name.split(' ')[0] : 'Guest'}
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
            </button>

            {/* Dropdown Menu */}
            <AnimatePresence>
              {isUserMenuOpen && (
                <>
                  <div 
                    className="fixed inset-0 z-30" 
                    onClick={() => setIsUserMenuOpen(false)} 
                  />
                  <motion.div
                    initial={{ opacity: 0, y: 10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 10, scale: 0.95 }}
                    className="absolute right-0 mt-2 w-64 bg-[#0B0F17] border border-white/10 rounded-2xl shadow-2xl p-3 z-40 text-xs text-gray-300"
                  >
                    {user ? (
                      <div>
                        <div className="p-2 border-b border-white/10 mb-2">
                          <p className="font-semibold text-white text-sm">{user.name}</p>
                          <p className="text-gray-400 text-[11px] truncate">{user.email}</p>
                          <span className="inline-block mt-1 px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 text-[10px] font-medium border border-indigo-500/30">
                            {user.role}
                          </span>
                        </div>
                        <button
                          onClick={() => { setIsUserMenuOpen(false); openAuthModal('login'); }}
                          className="w-full flex items-center space-x-2 p-2 rounded-xl hover:bg-white/5 text-gray-300 transition-colors text-left"
                        >
                          <UserIcon className="w-4 h-4 text-gray-400" />
                          <span>Switch Account</span>
                        </button>
                        <button
                          onClick={() => { setIsUserMenuOpen(false); logout(); }}
                          className="w-full flex items-center space-x-2 p-2 rounded-xl hover:bg-red-500/10 text-red-400 transition-colors text-left"
                        >
                          <LogOut className="w-4 h-4" />
                          <span>Sign Out</span>
                        </button>
                      </div>
                    ) : (
                      <div>
                        <div className="p-2 border-b border-white/10 mb-2">
                          <p className="font-semibold text-white">Guest Session</p>
                          <p className="text-gray-400 text-[11px]">Sign in to save custom rules & analysis history</p>
                        </div>
                        <button
                          onClick={() => { setIsUserMenuOpen(false); openAuthModal('login'); }}
                          className="w-full flex items-center space-x-2 p-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors mb-1.5"
                        >
                          <LogIn className="w-4 h-4" />
                          <span>Sign In / Create Account</span>
                        </button>
                        <button
                          onClick={() => { setIsUserMenuOpen(false); openAuthModal('login'); }}
                          className="w-full flex items-center space-x-2 p-2 rounded-xl bg-white/5 hover:bg-white/10 text-indigo-300 transition-colors"
                        >
                          <Sparkles className="w-4 h-4 text-indigo-400" />
                          <span>Log in as Demo User</span>
                        </button>
                      </div>
                    )}
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 w-full max-w-7xl mx-auto p-4 sm:p-6 z-10 relative pb-40">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.25, ease: "easeOut" }}
            className="w-full min-h-full"
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Floating Mac-like Dock */}
      <motion.div 
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3, type: 'spring', damping: 20 }}
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 pointer-events-auto"
      >
        <div className="glass rounded-2xl p-2 flex items-center space-x-1 relative shadow-2xl border border-white/10 bg-[#0B0F17]/80 backdrop-blur-xl">
          {tabs.map((tab) => {
            const isActive = location.pathname.startsWith(tab.path);
            const Icon = tab.icon;
            
            return (
              <Link
                key={tab.id}
                to={tab.path}
                onMouseEnter={() => setHoveredTab(tab.id)}
                onMouseLeave={() => setHoveredTab(null)}
                className="relative flex flex-col items-center justify-center w-16 h-16 rounded-xl transition-all duration-300 group"
              >
                {isActive && (
                  <motion.div
                    layoutId="active-pill"
                    className="absolute inset-0 bg-indigo-600/20 rounded-xl border border-indigo-500/30 shadow-inner"
                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                  />
                )}
                
                <Icon 
                  className={cn(
                    "w-5 h-5 mb-1 transition-all duration-300 relative z-10",
                    isActive ? "text-indigo-400 scale-110" : "text-gray-400 group-hover:text-gray-200",
                    hoveredTab === tab.id && !isActive ? "scale-110 text-white" : ""
                  )} 
                />
                
                <span className={cn(
                  "text-[10px] font-medium tracking-wide relative z-10 transition-colors",
                  isActive ? "text-indigo-300 font-semibold" : "text-gray-400 group-hover:text-gray-200"
                )}>
                  {tab.label}
                </span>

                {isActive && (
                  <div className="absolute -bottom-1.5 w-1 h-1 bg-indigo-400 rounded-full shadow-[0_0_8px_rgba(99,102,241,0.8)]" />
                )}
              </Link>
            );
          })}
        </div>
      </motion.div>

      {/* Global Modals */}
      <SearchModal isOpen={isSearchOpen} onClose={() => setIsSearchOpen(false)} />
      <AuthModal />
    </div>
  );
}
