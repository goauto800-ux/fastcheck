import { motion, AnimatePresence } from "framer-motion";
import { Mail, Phone, CheckCircle, XCircle, Loader2, Search } from "lucide-react";
import { FaUber, FaAmazon } from "react-icons/fa";
import { SiNetflix, SiBinance, SiCoinbase } from "react-icons/si";

const PLATFORM_CONFIG = {
  uber_eats: {
    name: "Uber Eats",
    icon: FaUber,
    color: "#06C167",
  },
  amazon: {
    name: "Amazon",
    icon: FaAmazon,
    color: "#FF9900",
  },
  netflix: {
    name: "Netflix",
    icon: SiNetflix,
    color: "#E50914",
  },
  binance: {
    name: "Binance",
    icon: SiBinance,
    color: "#F0B90B",
  },
  coinbase: {
    name: "Coinbase",
    icon: SiCoinbase,
    color: "#0052FF",
  },
};

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
              {isEmail ? "Email" : "Téléphone"} • {foundCount}/5 trouvé(s)
            </p>
          </div>
        </div>

        {/* Platform Results */}
        <div className="relative space-y-0">
          {result.platforms.map((platform, idx) => {
            const config = PLATFORM_CONFIG[platform.platform];
            const Icon = config?.icon;
            
            return (
              <div
                key={platform.platform}
                className={`flex items-center justify-between py-2.5 ${
                  idx < result.platforms.length - 1 ? "border-b border-white/5" : ""
                }`}
                data-testid={`platform-${platform.platform}-${platform.status}`}
              >
                <div className="flex items-center gap-2.5">
                  {Icon && (
                    <Icon 
                      className="w-4 h-4" 
                      style={{ color: config.color }}
                    />
                  )}
                  <span className="text-sm font-mono text-slate-300">
                    {config?.name || platform.platform}
                  </span>
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
          Aucun résultat. Uploadez un fichier ou collez vos données pour commencer.
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
