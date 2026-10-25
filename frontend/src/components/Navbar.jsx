import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { BarChart3, LogOut, User, UploadCloud, Sun, Moon } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const { isDark, toggleTheme } = useTheme();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="bg-slate-900 dark:bg-[#111827] border-b border-slate-800 dark:border-[#293548] text-white sticky top-0 z-40 transition-colors duration-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Link to="/" className="flex items-center space-x-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-500 dark:from-blue-600 dark:to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
              <BarChart3 className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="text-lg font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 dark:from-white dark:via-blue-100 dark:to-slate-300 bg-clip-text text-transparent">
                VendorMetrics
              </span>
              <span className="hidden sm:inline-block ml-2 text-xs font-medium px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 dark:bg-blue-500/10 dark:text-blue-400 border border-indigo-500/20 dark:border-blue-500/30">
                Analytics Hub
              </span>
            </div>
          </Link>
        </div>

        <div className="flex items-center space-x-3 sm:space-x-4">
          <div className="hidden md:flex items-center space-x-1.5 text-xs text-emerald-400 bg-emerald-950/40 border border-emerald-800/40 px-3 py-1.5 rounded-full">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>MySQL 8.0 Live</span>
          </div>

          <Link
            to="/upload"
            className="hidden sm:inline-flex items-center space-x-1.5 text-xs font-semibold bg-indigo-600 hover:bg-indigo-500 dark:bg-blue-600 dark:hover:bg-blue-500 text-white px-3.5 py-1.5 rounded-lg shadow-xs transition"
          >
            <UploadCloud className="w-4 h-4" />
            <span>Upload Data</span>
          </Link>

          {/* Theme Toggle Button */}
          <button
            type="button"
            onClick={toggleTheme}
            onKeyDown={(e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                toggleTheme();
              }
            }}
            className="p-2 rounded-xl text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 dark:bg-[#172033] dark:hover:bg-[#1E293B] border border-slate-700 dark:border-[#293548] focus:outline-hidden focus:ring-2 focus:ring-blue-400 transition flex items-center justify-center cursor-pointer shadow-xs"
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? (
              <Sun className="w-4 h-4 text-amber-300 animate-in fade-in zoom-in-75 duration-200" />
            ) : (
              <Moon className="w-4 h-4 text-slate-300 animate-in fade-in zoom-in-75 duration-200" />
            )}
          </button>

          {user && (
            <div className="flex items-center space-x-3 border-l border-slate-800 dark:border-[#293548] pl-3 sm:pl-4">
              <div className="flex items-center space-x-2 text-sm text-slate-300">
                <div className="w-8 h-8 rounded-full bg-slate-800 dark:bg-[#172033] border border-slate-700 dark:border-[#293548] flex items-center justify-center text-slate-300">
                  <User className="w-4 h-4" />
                </div>
                <div className="hidden lg:block text-left">
                  <div className="text-xs font-medium text-slate-200">{user.name || user.email}</div>
                  <div className="text-[10px] text-slate-400">{user.email}</div>
                </div>
              </div>

              <button
                type="button"
                onClick={handleLogout}
                className="p-1.5 text-slate-400 hover:text-rose-400 rounded-lg hover:bg-slate-800/60 dark:hover:bg-[#172033] transition"
                title="Logout"
                aria-label="Logout"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

export default Navbar;
