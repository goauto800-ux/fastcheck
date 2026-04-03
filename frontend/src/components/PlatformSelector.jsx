import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Check, Filter, X } from "lucide-react";
import { Button } from "./ui/button";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Platform icons/colors mapping
const PLATFORM_STYLES = {
  netflix: { color: "bg-red-500", label: "Netflix" },
  uber_eats: { color: "bg-green-500", label: "Uber Eats" },
  binance: { color: "bg-yellow-500", label: "Binance" },
  coinbase: { color: "bg-blue-500", label: "Coinbase" },
  deliveroo: { color: "bg-teal-500", label: "Deliveroo" },
  amazon: { color: "bg-orange-500", label: "Amazon" },
  discord: { color: "bg-indigo-500", label: "Discord" },
  instagram: { color: "bg-pink-500", label: "Instagram" },
  twitter: { color: "bg-sky-500", label: "Twitter" },
  snapchat: { color: "bg-yellow-400", label: "Snapchat" },
  spotify: { color: "bg-green-400", label: "Spotify" },
  github: { color: "bg-gray-500", label: "GitHub" },
  google: { color: "bg-red-400", label: "Google" },
  // Default for others
  default: { color: "bg-slate-500", label: "" }
};

export default function PlatformSelector({ selectedPlatforms, onSelectionChange, disabled }) {
  const [platforms, setPlatforms] = useState({ email: [], phone: [] });
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlatforms = async () => {
      try {
        const resp = await axios.get(`${API}/platforms`);
        setPlatforms(resp.data.platforms);
      } catch (e) {
        console.error("Failed to fetch platforms:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchPlatforms();
  }, []);

  const allPlatforms = [...platforms.email, ...platforms.phone];
  const isAllSelected = selectedPlatforms.length === 0;
  
  const togglePlatform = (platformName) => {
    if (selectedPlatforms.includes(platformName)) {
      const newSelection = selectedPlatforms.filter(p => p !== platformName);
      onSelectionChange(newSelection);
    } else {
      onSelectionChange([...selectedPlatforms, platformName]);
    }
  };

  const selectAll = () => {
    onSelectionChange([]);
  };

  const clearSelection = () => {
    onSelectionChange([]);
  };

  const getPlatformStyle = (name) => {
    return PLATFORM_STYLES[name] || PLATFORM_STYLES.default;
  };

  const formatLabel = (name) => {
    const style = getPlatformStyle(name);
    if (style.label) return style.label;
    return name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');
  };

  if (loading) {
    return (
      <div className="mb-6 p-4 rounded-xl border border-white/10 bg-white/5">
        <div className="animate-pulse flex items-center gap-2">
          <Filter className="w-4 h-4 text-slate-500" />
          <span className="text-slate-500 text-sm font-mono">Chargement des plateformes...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6">
      {/* Toggle Button */}
      <motion.button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full p-4 rounded-xl border transition-all flex items-center justify-between
          ${isOpen ? 'border-purple-500/50 bg-purple-500/10' : 'border-white/10 bg-white/5 hover:border-white/20'}
          ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <div className="flex items-center gap-3">
          <Filter className={`w-5 h-5 ${isOpen ? 'text-purple-400' : 'text-slate-400'}`} />
          <span className="text-white font-mono text-sm">
            {isAllSelected ? (
              "Toutes les plateformes"
            ) : (
              `${selectedPlatforms.length} plateforme(s) sélectionnée(s)`
            )}
          </span>
        </div>
        
        {/* Selected platforms preview */}
        {!isAllSelected && selectedPlatforms.length > 0 && selectedPlatforms.length <= 5 && (
          <div className="flex gap-1">
            {selectedPlatforms.map(p => (
              <span 
                key={p}
                className={`w-2 h-2 rounded-full ${getPlatformStyle(p).color}`}
              />
            ))}
          </div>
        )}
      </motion.button>

      {/* Dropdown Panel */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 p-4 rounded-xl border border-white/10 bg-[#0A0710]"
        >
          {/* Actions */}
          <div className="flex gap-2 mb-4">
            <Button
              size="sm"
              variant={isAllSelected ? "default" : "outline"}
              onClick={selectAll}
              className={isAllSelected 
                ? "bg-purple-600 text-white" 
                : "border-white/10 text-slate-400 bg-transparent hover:text-white"
              }
            >
              Toutes
            </Button>
            {!isAllSelected && (
              <Button
                size="sm"
                variant="outline"
                onClick={clearSelection}
                className="border-white/10 text-slate-400 bg-transparent hover:text-white"
              >
                <X className="w-3 h-3 mr-1" />
                Réinitialiser
              </Button>
            )}
          </div>

          {/* Custom Platforms (need proxy) */}
          <div className="mb-4">
            <h4 className="text-xs font-mono text-amber-400 mb-2 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              Plateformes personnalisées (proxy requis)
            </h4>
            <div className="flex flex-wrap gap-2">
              {platforms.email.filter(p => p.type === 'custom').map((platform) => {
                const isSelected = selectedPlatforms.includes(platform.name);
                const style = getPlatformStyle(platform.name);
                return (
                  <motion.button
                    key={platform.name}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => togglePlatform(platform.name)}
                    className={`
                      px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-2 transition-all
                      ${isSelected || isAllSelected
                        ? 'bg-white/10 text-white border border-white/20' 
                        : 'bg-white/5 text-slate-500 border border-transparent hover:border-white/10'
                      }
                    `}
                  >
                    <span className={`w-2 h-2 rounded-full ${style.color}`} />
                    {formatLabel(platform.name)}
                    {(isSelected || isAllSelected) && <Check className="w-3 h-3 text-green-400" />}
                  </motion.button>
                );
              })}
            </div>
          </div>

          {/* Holehe Platforms */}
          <div>
            <h4 className="text-xs font-mono text-blue-400 mb-2 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-blue-400" />
              Plateformes standard
            </h4>
            <div className="flex flex-wrap gap-2 max-h-[200px] overflow-y-auto">
              {platforms.email.filter(p => p.type === 'holehe').map((platform) => {
                const isSelected = selectedPlatforms.includes(platform.name);
                const style = getPlatformStyle(platform.name);
                return (
                  <motion.button
                    key={platform.name}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => togglePlatform(platform.name)}
                    className={`
                      px-3 py-1.5 rounded-lg text-xs font-mono flex items-center gap-2 transition-all
                      ${isSelected || isAllSelected
                        ? 'bg-white/10 text-white border border-white/20' 
                        : 'bg-white/5 text-slate-500 border border-transparent hover:border-white/10'
                      }
                    `}
                  >
                    <span className={`w-2 h-2 rounded-full ${style.color}`} />
                    {formatLabel(platform.name)}
                    {(isSelected || isAllSelected) && <Check className="w-3 h-3 text-green-400" />}
                  </motion.button>
                );
              })}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
