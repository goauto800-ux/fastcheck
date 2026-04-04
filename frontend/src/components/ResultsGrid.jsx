import { motion, AnimatePresence } from "framer-motion";
import {
  Mail, Phone, CheckCircle, XCircle, Loader2, Search, AlertCircle, ShieldAlert,
  Globe, ShoppingCart, Music, MessageCircle, Code,
  Briefcase, Car, Coffee, Calendar, Dumbbell
} from "lucide-react";
import { platformLogos, getPlatformColor } from "./PlatformLogos";

const PLATFORM_CONFIG = {
  netflix: { name: "Netflix", color: "#E50914", category: "streaming", needsProxy: true },
  uber_eats: { name: "Uber Eats", color: "#06C167", category: "food", needsProxy: true },
  binance: { name: "Binance", color: "#F0B90B", category: "crypto", needsProxy: true },
  coinbase: { name: "Coinbase", color: "#0052FF", category: "crypto", needsProxy: true },
  deliveroo: { name: "Deliveroo", color: "#00CCBC", category: "food", needsProxy: true },
  amazon: { name: "Amazon", color: "#FF9900" }, ebay: { name: "eBay", color: "#E53238" },
  nike: { name: "Nike", color: "#FFFFFF" }, discord: { name: "Discord", color: "#5865F2" },
  instagram: { name: "Instagram", color: "#E4405F" }, twitter: { name: "Twitter/X", color: "#FFFFFF" },
  pinterest: { name: "Pinterest", color: "#BD081C" }, snapchat: { name: "Snapchat", color: "#FFFC00" },
  tumblr: { name: "Tumblr", color: "#36465D" }, imgur: { name: "Imgur", color: "#1BB76E" },
  patreon: { name: "Patreon", color: "#FF424D" }, strava: { name: "Strava", color: "#FC4C02" },
  quora: { name: "Quora", color: "#B92B27" }, spotify: { name: "Spotify", color: "#1DB954" },
  soundcloud: { name: "SoundCloud", color: "#FF5500" }, github: { name: "GitHub", color: "#FFFFFF" },
  docker: { name: "Docker", color: "#2496ED" }, codecademy: { name: "Codecademy", color: "#1F4056" },
  google: { name: "Google", color: "#4285F4" }, yahoo: { name: "Yahoo", color: "#6001D2" },
  protonmail: { name: "ProtonMail", color: "#6D4AFF" }, adobe: { name: "Adobe", color: "#FF0000" },
  office365: { name: "Office 365", color: "#D83B01" }, lastpass: { name: "LastPass", color: "#D32D27" },
  firefox: { name: "Firefox", color: "#FF7139" }, venmo: { name: "Venmo", color: "#3D95CE" },
  wordpress: { name: "WordPress", color: "#21759B" }, blablacar: { name: "BlaBlaCar", color: "#00AAFF" },
  buymeacoffee: { name: "Buy Me Coffee", color: "#FFDD00" }, eventbrite: { name: "Eventbrite", color: "#F05537" },
};

function PlatformIcon({ platform, config }) {
  const logo = platformLogos[platform];
  const color = config?.color || getPlatformColor(platform);
  if (logo) return <div className="w-4 h-4 flex items-center justify-center" style={{ color }}>{logo}</div>;
  return <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color, opacity: 0.6 }} />;
}

function StatusBadge({ status }) {
  const map = {
    pending: { c: "text-yellow-400", icon: Loader2, l: "En cours", spin: true },
    found: { c: "text-green-400", icon: CheckCircle, l: "Trouvé" },
    unverifiable: { c: "text-yellow-400", icon: ShieldAlert, l: "N/V" },
    rate_limited: { c: "text-orange-400", icon: AlertCircle, l: "Limité" },
    error: { c: "text-orange-400", icon: AlertCircle, l: "Erreur" },
    not_supported: { c: "text-gray-600", icon: XCircle, l: "N/S" },
  };
  const cfg = map[status] || { c: "text-red-400", icon: XCircle, l: "Non trouvé" };
  const Icon = cfg.icon;
  return (
    <div className={`flex items-center gap-1 ${cfg.c}`}>
      <Icon className={`w-3 h-3 ${cfg.spin ? 'animate-spin' : ''}`} />
      <span className="text-[11px] font-mono">{cfg.l}</span>
    </div>
  );
}

function ResultCard({ result, index }) {
  const isEmail = result.identifier_type === "email";
  const foundCount = result.platforms.filter(p => p.status === "found").length;
  const unv = result.platforms.filter(p => p.status === "unverifiable").length;
  const verified = result.platforms.length - unv;
  const hasFound = foundCount > 0;

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.02, duration: 0.25 }} className="masonry-item" data-testid={`result-card-${index}`}>
      <div className={`glass-card rounded-xl p-4 hover-lift ${hasFound ? 'border-green-500/20 shadow-[0_0_20px_rgba(0,255,100,0.06)]' : ''}`}>
        {/* Header */}
        <div className="flex items-start gap-2.5 mb-3 pb-3 border-b border-white/5">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 bg-gradient-to-br ${isEmail ? 'from-[#00F0FF]/20 to-[#8B5CF6]/20' : 'from-[#FF00FF]/20 to-[#8B5CF6]/20'}`}>
            {isEmail ? <Mail className="w-4 h-4 text-[#00F0FF]" /> : <Phone className="w-4 h-4 text-[#FF00FF]" />}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-white text-sm font-medium truncate font-mono" title={result.identifier}>{result.identifier}</p>
            <p className="text-gray-500 text-[11px] mt-0.5">
              {isEmail ? "Email" : "Tél"} · <span className={foundCount > 0 ? 'text-green-400' : 'text-red-400'}>{foundCount}</span>/{verified}
              {unv > 0 && <span className="text-yellow-400"> · {unv} n/v</span>}
            </p>
          </div>
        </div>
        {/* Platforms */}
        <div className="space-y-0 max-h-[360px] overflow-y-auto">
          {result.platforms.map((p, idx) => {
            const cfg = PLATFORM_CONFIG[p.platform];
            return (
              <div key={p.platform} className={`flex items-center justify-between py-2 ${idx < result.platforms.length - 1 ? 'border-b border-white/5' : ''}`}
                data-testid={`platform-${p.platform}-${p.status}`}>
                <div className="flex items-center gap-2">
                  <PlatformIcon platform={p.platform} config={cfg} />
                  <span className="text-xs text-gray-400">{cfg?.name || p.platform}</span>
                  {cfg?.needsProxy && <span className="text-[8px] px-1 py-px rounded bg-yellow-500/10 text-yellow-500/60 font-mono uppercase">proxy</span>}
                </div>
                <StatusBadge status={p.status} />
              </div>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}

export default function ResultsGrid({ results, isLoading }) {
  if (results.length === 0 && !isLoading) {
    return (
      <div className="text-center py-20" data-testid="empty-results">
        <div className="w-16 h-16 rounded-2xl bg-white/[0.03] border border-white/10 flex items-center justify-center mx-auto mb-4">
          <Search className="w-8 h-8 text-gray-600" />
        </div>
        <p className="text-gray-500 text-sm">Entrez des emails ou numéros pour vérifier sur 35+ plateformes.</p>
      </div>
    );
  }
  return (
    <div className="masonry-grid" data-testid="results-grid">
      <AnimatePresence mode="popLayout">
        {results.map((result, i) => <ResultCard key={result.id} result={result} index={i} />)}
      </AnimatePresence>
    </div>
  );
}
