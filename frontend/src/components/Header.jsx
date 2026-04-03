import { motion } from "framer-motion";
import { Zap, Cpu } from "lucide-react";
import { useState, useEffect } from "react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

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
          <div className="flex items-center gap-3" data-testid="logo">
            <div className="relative">
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
              <div className="absolute -inset-1 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 blur-sm -z-10" />
            </div>
            <span className="font-heading text-2xl font-black tracking-tighter gradient-text">
              FAST
            </span>
          </div>

          {/* Threading info */}
          {threadInfo && (
            <div className="hidden sm:flex items-center gap-4">
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-blue-500/10 border border-blue-500/20">
                <Cpu className="w-3.5 h-3.5 text-blue-400" />
                <span className="text-xs font-mono text-blue-400">
                  {threadInfo.max_concurrent_identifiers} threads
                </span>
              </div>
              <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-purple-500/10 border border-purple-500/20">
                <Zap className="w-3.5 h-3.5 text-purple-400" />
                <span className="text-xs font-mono text-purple-400">
                  {threadInfo.max_concurrent_platforms} checks//{threadInfo.active_proxies > 0 ? ` • ${threadInfo.active_proxies} proxies` : ""}
                </span>
              </div>
            </div>
          )}

          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono text-slate-400">Auto</span>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
