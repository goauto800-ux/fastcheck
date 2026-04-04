import { useState, useEffect } from "react";
import { Cpu, Activity } from "lucide-react";
import axios from "axios";
import DiblowLogo from "./DiblowLogo";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function Header() {
  const [threadInfo, setThreadInfo] = useState(null);

  useEffect(() => {
    const fetchInfo = async () => {
      try { const r = await axios.get(`${BACKEND_URL}/api/config/threads`); setThreadInfo(r.data); } catch (e) {}
    };
    fetchInfo();
    const interval = setInterval(fetchInfo, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-[#05050A]/80 backdrop-blur-xl border-b border-white/10" data-testid="header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <DiblowLogo size="md" />

          {/* Thread info */}
          <div className="hidden sm:flex items-center gap-3">
            {threadInfo && (
              <>
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/10 text-xs font-mono text-gray-300">
                  <Cpu className="w-3.5 h-3.5 text-[#00F0FF]" />
                  <span className="text-[#00F0FF]">{threadInfo.max_concurrent_identifiers}</span>x threads
                </div>
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/10 text-xs font-mono text-gray-300">
                  <Activity className="w-3.5 h-3.5 text-[#FF00FF]" />
                  <span className="text-[#FF00FF]">{threadInfo.max_concurrent_platforms}</span> checks
                  {threadInfo.active_proxies > 0 && <span className="text-[#8B5CF6]"> · {threadInfo.active_proxies}p</span>}
                </div>
              </>
            )}
          </div>

          {/* Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/10">
            <div className="relative">
              <div className="w-2 h-2 rounded-full bg-[#00F0FF]" style={{boxShadow:'0 0 8px rgba(0,240,255,0.6)'}} />
              <div className="absolute inset-0 w-2 h-2 rounded-full bg-[#00F0FF] animate-ping opacity-30" />
            </div>
            <span className="text-xs font-medium text-[#00F0FF]">Online</span>
          </div>
        </div>
      </div>
    </header>
  );
}
