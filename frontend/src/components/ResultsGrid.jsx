import { motion, AnimatePresence } from "framer-motion";
import { 
  Mail, Phone, CheckCircle, XCircle, Loader2, Search, AlertCircle, ShieldAlert,
  Globe, ShoppingCart, Music, Camera, MessageCircle, Code, 
  Briefcase, Car, Coffee, Calendar, Dumbbell
} from "lucide-react";
import { platformLogos, getPlatformColor } from "./PlatformLogos";

// Simple platform config with colors only
const PLATFORM_CONFIG = {
  // Priority platforms (custom) - Need residential proxies!
  netflix: { name: "Netflix", color: "#E50914", category: "streaming", needsProxy: true },
  uber_eats: { name: "Uber Eats", color: "#06C167", category: "food", needsProxy: true },
  binance: { name: "Binance", color: "#F0B90B", category: "crypto", needsProxy: true },
  coinbase: { name: "Coinbase", color: "#0052FF", category: "crypto", needsProxy: true },
  deliveroo: { name: "Deliveroo", color: "#00CCBC", category: "food", needsProxy: true },
  
  // Shopping & Food (holehe - works without proxy)
  amazon: { name: "Amazon", color: "#FF9900", category: "shopping" },
  ebay: { name: "eBay", color: "#E53238", category: "shopping" },
  nike: { name: "Nike", color: "#FFFFFF", category: "shopping" },
  
  // Social Media (holehe - works without proxy)
  discord: { name: "Discord", color: "#5865F2", category: "social" },
  instagram: { name: "Instagram", color: "#E4405F", category: "social" },
  twitter: { name: "Twitter/X", color: "#000000", category: "social" },
  pinterest: { name: "Pinterest", color: "#BD081C", category: "social" },
  snapchat: { name: "Snapchat", color: "#FFFC00", category: "social" },
  tumblr: { name: "Tumblr", color: "#36465D", category: "social" },
  imgur: { name: "Imgur", color: "#1BB76E", category: "social" },
  patreon: { name: "Patreon", color: "#FF424D", category: "social" },
  strava: { name: "Strava", color: "#FC4C02", category: "sport" },
  quora: { name: "Quora", color: "#B92B27", category: "social" },
  
  // Music & Streaming (holehe)
  spotify: { name: "Spotify", color: "#1DB954", category: "music" },
  soundcloud: { name: "SoundCloud", color: "#FF5500", category: "music" },
  
  // Tech & Dev (holehe)
  github: { name: "GitHub", color: "#FFFFFF", category: "dev" },
  docker: { name: "Docker", color: "#2496ED", category: "dev" },
  codecademy: { name: "Codecademy", color: "#1F4056", category: "dev" },
  
  // Email providers (holehe)
  google: { name: "Google", color: "#4285F4", category: "email" },
  yahoo: { name: "Yahoo", color: "#6001D2", category: "email" },
  protonmail: { name: "ProtonMail", color: "#6D4AFF", category: "email" },
  
  // Software (holehe)
  adobe: { name: "Adobe", color: "#FF0000", category: "software" },
  office365: { name: "Office 365", color: "#D83B01", category: "software" },
  lastpass: { name: "LastPass", color: "#D32D27", category: "software" },
  firefox: { name: "Firefox", color: "#FF7139", category: "software" },
  
  // Payment (holehe)
  venmo: { name: "Venmo", color: "#3D95CE", category: "payment" },
  
  // Other (holehe)
  wordpress: { name: "WordPress", color: "#21759B", category: "software" },
  blablacar: { name: "BlaBlaCar", color: "#00AAFF", category: "transport" },
  buymeacoffee: { name: "Buy Me Coffee", color: "#FFDD00", category: "crowdfunding" },
  eventbrite: { name: "Eventbrite", color: "#F05537", category: "events" },
};

// Get icon based on category
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

// Platform logo component with glow
function PlatformIcon({ platform, config }) {
  const logo = platformLogos[platform];
  const color = config?.color || getPlatformColor(platform);
  
  if (logo) {
    return (
      <div 
        className="w-5 h-5 flex items-center justify-center"
        style={{ 
          color: color,
          filter: `drop-shadow(0 0 6px ${color}80)`
        }}
      >
        {logo}
      </div>
    );
  }
  
  // Fallback to category icon
  const Icon = getCategoryIcon(config?.category);
  return (
    <Icon 
      className="w-4 h-4" 
      style={{ 
        color: color,
        filter: `drop-shadow(0 0 4px ${color}60)`
      }}
    />
  );
}

function StatusBadge({ status }) {
  if (status === "pending") {
    return (
      <div className="flex items-center gap-1.5 text-yellow-400">
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
        <span className="text-xs font-mono">En cours</span>
      </div>
    );
  }

  if (status === "found") {
    return (
      <div className="flex items-center gap-1.5 text-emerald-400">
        <CheckCircle className="w-3.5 h-3.5" />
        <span className="text-xs font-mono">Trouvé</span>
      </div>
    );
  }

  if (status === "unverifiable") {
    return (
      <div className="flex items-center gap-1.5 text-amber-500">
        <ShieldAlert className="w-3.5 h-3.5" />
        <span className="text-xs font-mono">Non vérifiable</span>
      </div>
    );
  }

  if (status === "rate_limited") {
    return (
      <div className="flex items-center gap-1.5 text-orange-400">
        <AlertCircle className="w-3.5 h-3.5" />
        <span className="text-xs font-mono">Limité</span>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex items-center gap-1.5 text-orange-400">
        <AlertCircle className="w-3.5 h-3.5" />
        <span className="text-xs font-mono">Erreur</span>
      </div>
    );
  }

  if (status === "not_supported") {
    return (
      <div className="flex items-center gap-1.5 text-slate-500">
        <XCircle className="w-3.5 h-3.5" />
        <span className="text-xs font-mono">Non supporté</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5 text-rose-400">
      <XCircle className="w-3.5 h-3.5" />
      <span className="text-xs font-mono">Non trouvé</span>
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
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="masonry-item"
      data-testid={`result-card-${index}`}
    >
      <div className="bg-white/[0.02] border border-white/[0.05] rounded-2xl p-5 backdrop-blur-sm hover:border-blue-500/30 transition-all duration-300 shadow-[0_8px_32px_rgba(0,0,0,0.12)] relative overflow-hidden group">
        {/* Glow effect on hover */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* Header */}
        <div className="relative flex items-start gap-3 mb-4 pb-4 border-b border-white/5">
          <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
            isEmail 
              ? "bg-blue-500/10 text-blue-400" 
              : "bg-purple-500/10 text-purple-400"
          }`}>
            {isEmail ? <Mail className="w-5 h-5" /> : <Phone className="w-5 h-5" />}
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-white font-medium text-sm truncate font-mono" title={result.identifier}>
              {result.identifier}
            </p>
            <p className="text-slate-500 text-xs font-mono mt-0.5">
              {isEmail ? "Email" : "Téléphone"} • {foundCount}/{verifiedCount} vérifié(s)
              {unverifiableCount > 0 && (
                <span className="text-amber-500/70"> • {unverifiableCount} non vérifiable(s)</span>
              )}
            </p>
          </div>
        </div>

        {/* Platform Results - scrollable if many */}
        <div className="relative space-y-0 max-h-[400px] overflow-y-auto custom-scrollbar">
          {result.platforms.map((platform, idx) => {
            const config = PLATFORM_CONFIG[platform.platform];
            
            return (
              <div
                key={platform.platform}
                className={`flex items-center justify-between py-2.5 ${
                  idx < result.platforms.length - 1 ? "border-b border-white/5" : ""
                }`}
                data-testid={`platform-${platform.platform}-${platform.status}`}
              >
                <div className="flex items-center gap-2.5">
                  <PlatformIcon platform={platform.platform} config={config} />
                  <span className="text-sm font-mono text-slate-300">
                    {config?.name || platform.platform}
                  </span>
                  {config?.needsProxy && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/20 text-orange-400 font-mono">
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
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="text-center py-16"
        data-testid="empty-results"
      >
        <div className="w-20 h-20 rounded-2xl bg-white/5 flex items-center justify-center mx-auto mb-4">
          <Search className="w-10 h-10 text-slate-600" />
        </div>
        <p className="text-slate-500 font-mono text-sm">
          Aucun résultat. Entrez des emails ou numéros pour vérifier sur 35+ plateformes.
        </p>
      </motion.div>
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
