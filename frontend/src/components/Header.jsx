import { useState, useEffect } from "react";
import { Cpu, Zap, Activity } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function Header() {
  const [threadInfo, setThreadInfo] = useState(null);

  useEffect(() => {
    const fetchInfo = async () => {
      try {
        const resp = await axios.get(`${BACKEND_URL}/api/config/threads`);
        setThreadInfo(resp.data);
      } catch (e) {}
    };
    fetchInfo();
    const interval = setInterval(fetchInfo, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-[#060612]/70 backdrop-blur-xl border-b border-white/[0.04]" data-testid="header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo */}
          <div className="flex items-center gap-2.5 cursor-pointer" data-testid="logo">
            <div className="w-8 h-8 rounded-lg bg-[#00e5ff]/[0.08] border border-[#00e5ff]/20 flex items-center justify-center" style={{boxShadow:'0 0 20px rgba(0,229,255,0.15)'}}>
              <Zap className="w-4 h-4 text-[#00e5ff]" />
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold tracking-tight leading-none neon-cyan">FAST</span>
              <span className="text-[9px] text-[#44445e] tracking-widest uppercase leading-none">checker</span>
            </div>
          </div>

          {/* Thread pills */}
          <div className="hidden sm:flex items-center gap-2">
            {threadInfo && (
              <>
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#00e5ff]/[0.06] border border-[#00e5ff]/15 text-[11px] font-mono text-[#00e5ff]/80" style={{boxShadow:'0 0 12px rgba(0,229,255,0.08)'}}>
                  <Cpu className="w-3 h-3" />
                  {threadInfo.max_concurrent_identifiers}x
                </div>
                <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#00ff88]/[0.06] border border-[#00ff88]/15 text-[11px] font-mono text-[#00ff88]/80" style={{boxShadow:'0 0 12px rgba(0,255,136,0.08)'}}>
                  <Activity className="w-3 h-3" />
                  {threadInfo.max_concurrent_platforms} checks
                  {threadInfo.active_proxies > 0 && <span> · {threadInfo.active_proxies}p</span>}
                </div>
              </>
            )}
          </div>

          {/* Status */}
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-[#00ff88]/[0.06] border border-[#00ff88]/15" style={{boxShadow:'0 0 15px rgba(0,255,136,0.1)'}}>
            <div className="relative">
              <div className="w-1.5 h-1.5 rounded-full bg-[#00ff88]" style={{boxShadow:'0 0 8px rgba(0,255,136,0.6)'}} />
              <div className="absolute inset-0 w-1.5 h-1.5 rounded-full bg-[#00ff88] animate-ping opacity-30" />
            </div>
            <span className="text-[11px] font-medium text-[#00ff88]/80">Online</span>
          </div>
        </div>
      </div>
    </header>
  );
}
