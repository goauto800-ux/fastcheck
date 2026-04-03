import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Check, Filter, X } from "lucide-react";
import { Button } from "./ui/button";
import { platformLogos, getPlatformColor } from "./PlatformLogos";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Platform labels
const PLATFORM_LABELS = {
  netflix: "Netflix",
  uber_eats: "Uber Eats",
  binance: "Binance",
  coinbase: "Coinbase",
  deliveroo: "Deliveroo",
  amazon: "Amazon",
  ebay: "eBay",
  nike: "Nike",
  discord: "Discord",
  instagram: "Instagram",
  twitter: "Twitter/X",
  snapchat: "Snapchat",
  spotify: "Spotify",
  github: "GitHub",
  google: "Google",
  yahoo: "Yahoo",
  protonmail: "ProtonMail",
  pinterest: "Pinterest",
  tumblr: "Tumblr",
  imgur: "Imgur",
  patreon: "Patreon",
  strava: "Strava",
  quora: "Quora",
  soundcloud: "SoundCloud",
  docker: "Docker",
  codecademy: "Codecademy",
  adobe: "Adobe",
  office365: "Office 365",
  lastpass: "LastPass",
  firefox: "Firefox",
  venmo: "Venmo",
  wordpress: "WordPress",
  blablacar: "BlaBlaCar",
  buymeacoffee: "Buy Me Coffee",
  eventbrite: "Eventbrite",
};

// Mini platform icon with glow
function MiniPlatformLogo({ name, size = 14 }) {
  const logo = platformLogos[name];
  const color = getPlatformColor(name);
  
  if (logo) {
    return (
      <div 
        className="flex items-center justify-center flex-shrink-0"
        style={{ 
          width: size, 
          height: size, 
          color: color,
          filter: `drop-shadow(0 0 4px ${color}80)`
        }}
      >
        {logo}
      </div>
    );
  }
  
  // Fallback colored dot with glow
  return (
    <div
      className="rounded-full flex-shrink-0"
      style={{
        width: size - 4,
        height: size - 4,
        backgroundColor: color,
        boxShadow: `0 0 6px ${color}80, 0 0 12px ${color}40`,
      }}
    />
  );
}

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

  const formatLabel = (name) => {
    return PLATFORM_LABELS[name] || name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');
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
        
        {/* Selected platforms preview - show SVG logos */}
        {!isAllSelected && selectedPlatforms.length > 0 && selectedPlatforms.length <= 8 && (
          <div className="flex gap-1.5 items-center">
            {selectedPlatforms.map(p => (
              <MiniPlatformLogo key={p} name={p} size={16} />
            ))}
          </div>
        )}

        {/* Chevron */}
        <motion.svg
          animate={{ rotate: isOpen ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="w-5 h-5 text-slate-400"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </motion.svg>
      </motion.button>

      {/* Dropdown Panel */}
      {isOpen && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 p-5 rounded-xl border border-white/10 bg-[#0A0710] backdrop-blur-sm"
        >
          {/* Actions */}
          <div className="flex gap-2 mb-5">
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
          <div className="mb-5">
            <h4 className="text-xs font-mono text-amber-400 mb-3 flex items-center gap-2 uppercase tracking-wider">
              <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor">
                <path d="M6 0L7.5 4.5H12L8.25 7.5L9.75 12L6 9L2.25 12L3.75 7.5L0 4.5H4.5L6 0Z" style={{filter: "drop-shadow(0 0 4px #F59E0B)"}}/>
              </svg>
              Plateformes personnalisées (proxy requis)
            </h4>
            <div className="flex flex-wrap gap-2">
              {platforms.email.filter(p => p.type === 'custom').map((platform) => {
                const isSelected = selectedPlatforms.includes(platform.name);
                const color = getPlatformColor(platform.name);
                return (
                  <motion.button
                    key={platform.name}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => togglePlatform(platform.name)}
                    className={`
                      px-3 py-2 rounded-lg text-xs font-mono flex items-center gap-2.5 transition-all
                      ${isSelected || isAllSelected
                        ? 'bg-white/10 text-white border border-white/20' 
                        : 'bg-white/[0.03] text-slate-500 border border-white/5 hover:border-white/15 hover:bg-white/[0.06]'
                      }
                    `}
                    style={
                      (isSelected || isAllSelected) 
                        ? { boxShadow: `0 0 12px ${color}20, inset 0 0 12px ${color}08` }
                        : {}
                    }
                  >
                    <MiniPlatformLogo name={platform.name} size={16} />
                    {formatLabel(platform.name)}
                    {(isSelected || isAllSelected) && <Check className="w-3 h-3 text-green-400" />}
                  </motion.button>
                );
              })}
            </div>
          </div>

          {/* Holehe Platforms */}
          <div>
            <h4 className="text-xs font-mono text-blue-400 mb-3 flex items-center gap-2 uppercase tracking-wider">
              <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor" style={{filter: "drop-shadow(0 0 4px #3B82F6)"}}>
                <circle cx="6" cy="6" r="5" stroke="currentColor" strokeWidth="1.5" fill="none"/>
                <circle cx="6" cy="6" r="2" fill="currentColor"/>
              </svg>
              Plateformes standard
            </h4>
            <div className="flex flex-wrap gap-2 max-h-[250px] overflow-y-auto custom-scrollbar pr-1">
              {platforms.email.filter(p => p.type === 'holehe').map((platform) => {
                const isSelected = selectedPlatforms.includes(platform.name);
                const color = getPlatformColor(platform.name);
                return (
                  <motion.button
                    key={platform.name}
                    whileHover={{ scale: 1.03 }}
                    whileTap={{ scale: 0.97 }}
                    onClick={() => togglePlatform(platform.name)}
                    className={`
                      px-3 py-2 rounded-lg text-xs font-mono flex items-center gap-2.5 transition-all
                      ${isSelected || isAllSelected
                        ? 'bg-white/10 text-white border border-white/20' 
                        : 'bg-white/[0.03] text-slate-500 border border-white/5 hover:border-white/15 hover:bg-white/[0.06]'
                      }
                    `}
                    style={
                      (isSelected || isAllSelected) 
                        ? { boxShadow: `0 0 12px ${color}20, inset 0 0 12px ${color}08` }
                        : {}
                    }
                  >
                    <MiniPlatformLogo name={platform.name} size={16} />
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
