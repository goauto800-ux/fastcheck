import { motion } from "framer-motion";
import { Zap } from "lucide-react";

export default function Header() {
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

          {/* Tagline */}
          <div className="hidden sm:block">
            <span className="text-xs font-mono text-slate-500 tracking-wider uppercase">
              Identity Verification Tool
            </span>
          </div>

          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs font-mono text-slate-400">Online</span>
          </div>
        </div>
      </div>
    </motion.header>
  );
}
