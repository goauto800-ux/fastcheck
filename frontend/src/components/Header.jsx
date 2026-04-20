import { useState, useEffect } from "react";
import { Shield } from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

export default function Header() {
  const [healthInfo, setHealthInfo] = useState(null);

  useEffect(() => {
    const fetchInfo = async () => {
      try { const r = await axios.get(`${BACKEND_URL}/api/health`); setHealthInfo(r.data); } catch (e) {}
    };
    fetchInfo();
    const interval = setInterval(fetchInfo, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="sticky top-0 z-50 bg-[#05050A]/80 backdrop-blur-xl border-b border-white/10" data-testid="header">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#06C167] flex items-center justify-center text-white font-bold text-sm">
              UE
            </div>
            <span className="text-lg font-bold text-white tracking-tight">
              Uber<span className="text-[#06C167]">Check</span>
            </span>
          </div>

          {/* Status */}
          <div className="flex items-center gap-3">
            {healthInfo && healthInfo.proxies_active > 0 && (
              <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#06C167]/5 border border-[#06C167]/20 text-xs font-medium text-[#06C167]">
                <Shield className="w-3.5 h-3.5" />
                {healthInfo.proxies_active} proxy{healthInfo.proxies_active > 1 ? 's' : ''}
              </div>
            )}
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/10">
              <div className="relative">
                <div className="w-2 h-2 rounded-full bg-[#06C167]" style={{boxShadow:'0 0 8px rgba(6,193,103,0.6)'}} />
                <div className="absolute inset-0 w-2 h-2 rounded-full bg-[#06C167] animate-ping opacity-30" />
              </div>
              <span className="text-xs font-medium text-[#06C167]">Online</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
