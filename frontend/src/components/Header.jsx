import { motion } from "framer-motion";
import { Cpu } from "lucide-react";
import { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Custom FAST Logo SVG with lightning bolt
function FastLogo() {
  return (
    <div className="relative group">
      {/* Glow background */}
      <div className="absolute -inset-2 rounded-2xl bg-gradient-to-br from-blue-500/30 to-purple-600/30 blur-lg opacity-60 group-hover:opacity-100 transition-opacity duration-500" />
      
      {/* Main logo container */}
      <div className="relative w-11 h-11 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-purple-500/25 overflow-hidden">
        {/* Animated shine effect */}
        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-700" />
        
        {/* Lightning bolt SVG */}
        <svg 
          viewBox="0 0 24 24" 
          className="w-6 h-6 relative z-10"
          fill="none"
          stroke="white"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" fill="white" stroke="none" />
        </svg>
      </div>
    </div>
  );
}

export default function Header() {
  const [threadInfo, setThreadInfo] = useState(null);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const resp = await axios.get(`${BACKEND_URL}/api/config/threads`);
        setThreadInfo(resp.data);
      } catch (e) {
        // ignore
      }
    };
    fetchInfo();
    const interval = setInterval(fetchInfo, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="sticky top-0 z-50 glass border-b border-white/5"
      data-testid="header"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <motion.div 
            className="flex items-center gap-3 cursor-pointer" 
            data-testid="logo"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <FastLogo />
            <div className="flex flex-col">
              <span className="font-heading text-2xl font-black tracking-tighter leading-none">
                <span className="bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
                  FAST
                </span>
              </span>
              <span className="text-[9px] font-mono text-slate-500 tracking-[0.3em] uppercase leading-none">
                Identity Checker
              </span>
            </div>
          </motion.div>

          {/* Threading info */}
          {threadInfo && (
            <div className="hidden sm:flex items-center gap-3">
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <Cpu className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-xs font-mono text-blue-400">
                  {threadInfo.max_concurrent_identifiers} threads
                </span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <svg className="w-3.5 h-3.5 text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
                </svg>
                <span className="text-xs font-mono text-purple-400">
                  {threadInfo.max_concurrent_platforms} checks//{threadInfo.active_proxies > 0 ? ` • ${threadInfo.active_proxies} proxies` : ""}
                </span>
              </div>
            </div>
          )}

          {/* Status indicator */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <div className="relative">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-400 animate-ping opacity-50" />
            </div>
            <span className="text-xs font-mono text-emerald-400">Online</span>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
