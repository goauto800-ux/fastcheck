import { useState, useEffect } from "react";
import { Check, Filter, X } from "lucide-react";
import { Button } from "./ui/button";
import { platformLogos, getPlatformColor } from "./PlatformLogos";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const PLATFORM_LABELS = {
  netflix: "Netflix", uber_eats: "Uber Eats", binance: "Binance", coinbase: "Coinbase",
  deliveroo: "Deliveroo", amazon: "Amazon", ebay: "eBay", nike: "Nike",
  discord: "Discord", instagram: "Instagram", twitter: "Twitter/X", snapchat: "Snapchat",
  spotify: "Spotify", github: "GitHub", google: "Google", yahoo: "Yahoo",
  protonmail: "ProtonMail", pinterest: "Pinterest", tumblr: "Tumblr", imgur: "Imgur",
  patreon: "Patreon", strava: "Strava", quora: "Quora", soundcloud: "SoundCloud",
  docker: "Docker", codecademy: "Codecademy", adobe: "Adobe", office365: "Office 365",
  lastpass: "LastPass", firefox: "Firefox", venmo: "Venmo", wordpress: "WordPress",
  blablacar: "BlaBlaCar", buymeacoffee: "Buy Me Coffee", eventbrite: "Eventbrite",
};

function MiniPlatformLogo({ name, size = 14 }) {
  const logo = platformLogos[name];
  const color = getPlatformColor(name);
  if (logo) {
    return (
      <div className="flex items-center justify-center flex-shrink-0 opacity-80"
        style={{ width: size, height: size, color: color }}>
        {logo}
      </div>
    );
  }
  return (
    <div className="rounded-full flex-shrink-0"
      style={{ width: size - 4, height: size - 4, backgroundColor: color, opacity: 0.7 }} />
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
      onSelectionChange(selectedPlatforms.filter(p => p !== platformName));
    } else {
      onSelectionChange([...selectedPlatforms, platformName]);
    }
  };

  const selectAll = () => onSelectionChange([]);
  const clearSelection = () => onSelectionChange([]);

  const formatLabel = (name) => {
    return PLATFORM_LABELS[name] || name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');
  };

  if (loading) {
    return (
      <div className="mb-4 p-3 rounded-lg border border-white/[0.06] bg-white/[0.02]">
        <div className="flex items-center gap-2">
          <Filter className="w-3.5 h-3.5 text-[#55556a]" />
          <span className="text-[#55556a] text-xs">Chargement...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-4">
      <button
        onClick={() => setIsOpen(!isOpen)}
        disabled={disabled}
        className={`
          w-full p-3 rounded-lg border transition-all flex items-center justify-between
          ${isOpen ? 'border-[#00d4ff]/30 bg-[#00d4ff]/[0.04]' : 'border-white/[0.06] bg-white/[0.02] hover:border-white/[0.1]'}
          ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
        `}
      >
        <div className="flex items-center gap-2.5">
          <Filter className={`w-4 h-4 ${isOpen ? 'text-[#00d4ff]' : 'text-[#55556a]'}`} />
          <span className="text-white text-sm">
            {isAllSelected ? "Toutes les plateformes" : `${selectedPlatforms.length} sélectionnée(s)`}
          </span>
        </div>

        {!isAllSelected && selectedPlatforms.length > 0 && selectedPlatforms.length <= 8 && (
          <div className="flex gap-1 items-center">
            {selectedPlatforms.map(p => <MiniPlatformLogo key={p} name={p} size={14} />)}
          </div>
        )}

        <svg
          className={`w-4 h-4 text-[#55556a] transition-transform ${isOpen ? 'rotate-180' : ''}`}
          viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <div className="mt-1.5 p-4 rounded-lg border border-white/[0.06] bg-[#0e0e1a]">
          {/* Actions */}
          <div className="flex gap-2 mb-4">
            <Button
              size="sm"
              variant={isAllSelected ? "default" : "outline"}
              onClick={selectAll}
              className={isAllSelected
                ? "bg-[#00d4ff] text-black text-xs h-7"
                : "border-white/[0.08] text-[#8888a0] bg-transparent hover:text-white text-xs h-7"
              }
            >
              Toutes
            </Button>
            {!isAllSelected && (
              <Button size="sm" variant="outline" onClick={clearSelection}
                className="border-white/[0.08] text-[#8888a0] bg-transparent hover:text-white text-xs h-7">
                <X className="w-3 h-3 mr-1" /> Reset
              </Button>
            )}
          </div>

          {/* Custom Platforms */}
          <div className="mb-4">
            <h4 className="text-[10px] text-[#ffb020] mb-2 uppercase tracking-wider font-medium">
              Proxy requis
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {platforms.email.filter(p => p.type === 'custom').map((platform) => {
                const isSelected = selectedPlatforms.includes(platform.name);
                return (
                  <button
                    key={platform.name}
                    onClick={() => togglePlatform(platform.name)}
                    className={`
                      px-2.5 py-1.5 rounded-md text-[11px] flex items-center gap-1.5 transition-all
                      ${isSelected || isAllSelected
                        ? 'bg-white/[0.08] text-white border border-white/[0.15]'
                        : 'bg-white/[0.02] text-[#55556a] border border-white/[0.04] hover:border-white/[0.1] hover:text-[#8888a0]'
                      }
                    `}
                  >
                    <MiniPlatformLogo name={platform.name} size={14} />
                    {formatLabel(platform.name)}
                    {(isSelected || isAllSelected) && <Check className="w-3 h-3 text-[#00ff88]" />}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Standard Platforms */}
          <div>
            <h4 className="text-[10px] text-[#00d4ff] mb-2 uppercase tracking-wider font-medium">
              Standard
            </h4>
            <div className="flex flex-wrap gap-1.5 max-h-[220px] overflow-y-auto pr-1">
              {platforms.email.filter(p => p.type === 'holehe').map((platform) => {
                const isSelected = selectedPlatforms.includes(platform.name);
                return (
                  <button
                    key={platform.name}
                    onClick={() => togglePlatform(platform.name)}
                    className={`
                      px-2.5 py-1.5 rounded-md text-[11px] flex items-center gap-1.5 transition-all
                      ${isSelected || isAllSelected
                        ? 'bg-white/[0.08] text-white border border-white/[0.15]'
                        : 'bg-white/[0.02] text-[#55556a] border border-white/[0.04] hover:border-white/[0.1] hover:text-[#8888a0]'
                      }
                    `}
                  >
                    <MiniPlatformLogo name={platform.name} size={14} />
                    {formatLabel(platform.name)}
                    {(isSelected || isAllSelected) && <Check className="w-3 h-3 text-[#00ff88]" />}
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
