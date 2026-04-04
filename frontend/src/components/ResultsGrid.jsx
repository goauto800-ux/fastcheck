import { motion, AnimatePresence } from "framer-motion";
import {
  Mail, Phone, CheckCircle, XCircle, Loader2, Search, AlertCircle, ShieldAlert,
  Globe, ShoppingCart, Music, Camera, MessageCircle, Code,
  Briefcase, Car, Coffee, Calendar, Dumbbell
} from "lucide-react";
import { platformLogos, getPlatformColor } from "./PlatformLogos";

const PLATFORM_CONFIG = {
  netflix: { name: "Netflix", color: "#E50914", category: "streaming", needsProxy: true },
  uber_eats: { name: "Uber Eats", color: "#06C167", category: "food", needsProxy: true },
  binance: { name: "Binance", color: "#F0B90B", category: "crypto", needsProxy: true },
  coinbase: { name: "Coinbase", color: "#0052FF", category: "crypto", needsProxy: true },
  deliveroo: { name: "Deliveroo", color: "#00CCBC", category: "food", needsProxy: true },
  amazon: { name: "Amazon", color: "#FF9900", category: "shopping" },
  ebay: { name: "eBay", color: "#E53238", category: "shopping" },
  nike: { name: "Nike", color: "#FFFFFF", category: "shopping" },
  discord: { name: "Discord", color: "#5865F2", category: "social" },
  instagram: { name: "Instagram", color: "#E4405F", category: "social" },
  twitter: { name: "Twitter/X", color: "#FFFFFF", category: "social" },
  pinterest: { name: "Pinterest", color: "#BD081C", category: "social" },
  snapchat: { name: "Snapchat", color: "#FFFC00", category: "social" },
  tumblr: { name: "Tumblr", color: "#36465D", category: "social" },
  imgur: { name: "Imgur", color: "#1BB76E", category: "social" },
  patreon: { name: "Patreon", color: "#FF424D", category: "social" },
  strava: { name: "Strava", color: "#FC4C02", category: "sport" },
  quora: { name: "Quora", color: "#B92B27", category: "social" },
  spotify: { name: "Spotify", color: "#1DB954", category: "music" },
  soundcloud: { name: "SoundCloud", color: "#FF5500", category: "music" },
  github: { name: "GitHub", color: "#FFFFFF", category: "dev" },
  docker: { name: "Docker", color: "#2496ED", category: "dev" },
  codecademy: { name: "Codecademy", color: "#1F4056", category: "dev" },
  google: { name: "Google", color: "#4285F4", category: "email" },
  yahoo: { name: "Yahoo", color: "#6001D2", category: "email" },
  protonmail: { name: "ProtonMail", color: "#6D4AFF", category: "email" },
  adobe: { name: "Adobe", color: "#FF0000", category: "software" },
  office365: { name: "Office 365", color: "#D83B01", category: "software" },
  lastpass: { name: "LastPass", color: "#D32D27", category: "software" },
  firefox: { name: "Firefox", color: "#FF7139", category: "software" },
  venmo: { name: "Venmo", color: "#3D95CE", category: "payment" },
  wordpress: { name: "WordPress", color: "#21759B", category: "software" },
  blablacar: { name: "BlaBlaCar", color: "#00AAFF", category: "transport" },
  buymeacoffee: { name: "Buy Me Coffee", color: "#FFDD00", category: "crowdfunding" },
  eventbrite: { name: "Eventbrite", color: "#F05537", category: "events" },
};

function getCategoryIcon(category) {
  switch (category) {
    case "shopping": return ShoppingCart;
    case "food": return ShoppingCart;
    case "social": return MessageCircle;
    case "music": return Music;
    case "streaming": return Music;
    case "dev": return Code;
    case "email": return Mail;
    case "software": return Briefcase;
    case "transport": return Car;
    case "crowdfunding": return Coffee;
    case "events": return Calendar;
    case "sport": return Dumbbell;
    case "crypto": return Globe;
    case "payment": return Globe;
    default: return Globe;
  }
}

function PlatformIcon({ platform, config }) {
  const logo = platformLogos[platform];
  const color = config?.color || getPlatformColor(platform);

  if (logo) {
    return (
      <div
        className="w-4 h-4 flex items-center justify-center opacity-80"
        style={{ color: color }}
      >
        {logo}
      </div>
    );
  }

  const Icon = getCategoryIcon(config?.category);
  return <Icon className="w-3.5 h-3.5 opacity-60" style={{ color: color }} />;
}

function StatusBadge({ status }) {
  if (status === "pending") {
    return (
      <div className="flex items-center gap-1 text-[#ffb020]">
        <Loader2 className="w-3 h-3 animate-spin" />
        <span className="text-[11px] font-mono">En cours</span>
      </div>
    );
  }
  if (status === "found") {
    return (
      <div className="flex items-center gap-1 text-[#00ff88]">
        <CheckCircle className="w-3 h-3" />
        <span className="text-[11px] font-mono">Trouvé</span>
      </div>
    );
  }
  if (status === "unverifiable") {
    return (
      <div className="flex items-center gap-1 text-[#ffb020]">
        <ShieldAlert className="w-3 h-3" />
        <span className="text-[11px] font-mono">Non vérifiable</span>
      </div>
    );
  }
  if (status === "rate_limited") {
    return (
      <div className="flex items-center gap-1 text-orange-400">
        <AlertCircle className="w-3 h-3" />
        <span className="text-[11px] font-mono">Limité</span>
      </div>
    );
  }
  if (status === "error") {
    return (
      <div className="flex items-center gap-1 text-orange-400">
        <AlertCircle className="w-3 h-3" />
        <span className="text-[11px] font-mono">Erreur</span>
      </div>
    );
  }
  if (status === "not_supported") {
    return (
      <div className="flex items-center gap-1 text-[#55556a]">
        <XCircle className="w-3 h-3" />
        <span className="text-[11px] font-mono">Non supporté</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-1 text-[#ff3860]">
      <XCircle className="w-3 h-3" />
      <span className="text-[11px] font-mono">Non trouvé</span>
    </div>
  );
}

function ResultCard({ result, index }) {
  const isEmail = result.identifier_type === "email";
  const foundCount = result.platforms.filter((p) => p.status === "found").length;
  const unverifiableCount = result.platforms.filter((p) => p.status === "unverifiable").length;
  const totalCount = result.platforms.length;
  const verifiedCount = totalCount - unverifiableCount;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03, duration: 0.25 }}
      className="masonry-item"
      data-testid={`result-card-${index}`}
    >
      <div className="bg-[#111120] border border-white/[0.06] rounded-xl p-4 hover:border-[#00d4ff]/20 transition-all duration-200">
        {/* Header */}
        <div className="flex items-start gap-2.5 mb-3 pb-3 border-b border-white/[0.04]">
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
            isEmail
              ? "bg-[#00d4ff]/[0.08] text-[#00d4ff]"
              : "bg-[#a855f7]/[0.08] text-[#a855f7]"
          }`}>
            {isEmail ? <Mail className="w-4 h-4" /> : <Phone className="w-4 h-4" />}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-white text-sm font-medium truncate font-mono" title={result.identifier}>
              {result.identifier}
            </p>
            <p className="text-[#55556a] text-[11px] mt-0.5">
              {isEmail ? "Email" : "Tél"} · <span className="text-[#00ff88]">{foundCount}</span>/{verifiedCount}
              {unverifiableCount > 0 && (
                <span className="text-[#ffb020]"> · {unverifiableCount} n/v</span>
              )}
            </p>
          </div>
        </div>

        {/* Platforms */}
        <div className="space-y-0 max-h-[360px] overflow-y-auto">
          {result.platforms.map((platform, idx) => {
            const config = PLATFORM_CONFIG[platform.platform];
            return (
              <div
                key={platform.platform}
                className={`flex items-center justify-between py-2 ${
                  idx < result.platforms.length - 1 ? "border-b border-white/[0.03]" : ""
                }`}
                data-testid={`platform-${platform.platform}-${platform.status}`}
              >
                <div className="flex items-center gap-2">
                  <PlatformIcon platform={platform.platform} config={config} />
                  <span className="text-[12px] text-[#8888a0]">
                    {config?.name || platform.platform}
                  </span>
                  {config?.needsProxy && (
                    <span className="text-[9px] px-1 py-px rounded bg-[#ffb020]/10 text-[#ffb020]/70 font-mono">
                      PROXY
                    </span>
                  )}
                </div>
                <StatusBadge status={platform.status} />
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
      <div className="text-center py-16" data-testid="empty-results">
        <div className="w-14 h-14 rounded-xl bg-white/[0.03] flex items-center justify-center mx-auto mb-3">
          <Search className="w-7 h-7 text-[#55556a]" />
        </div>
        <p className="text-[#55556a] text-sm">
          Entrez des emails ou numéros pour vérifier sur 35+ plateformes.
        </p>
      </div>
    );
  }

  return (
    <div className="masonry-grid" data-testid="results-grid">
      <AnimatePresence mode="popLayout">
        {results.map((result, index) => (
          <ResultCard key={result.id} result={result} index={index} />
        ))}
      </AnimatePresence>
    </div>
  );
}
