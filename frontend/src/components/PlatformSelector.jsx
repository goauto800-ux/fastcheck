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
  if (logo) return <div className="flex items-center justify-center flex-shrink-0" style={{ width: size, height: size, color, filter: `drop-shadow(0 0 3px ${color}50)` }}>{logo}</div>;
  return <div className="rounded-full flex-shrink-0" style={{ width: size - 4, height: size - 4, backgroundColor: color, boxShadow: `0 0 6px ${color}40` }} />;
}

export default function PlatformSelector({ selectedPlatforms, onSelectionChange, disabled }) {
  const [platforms, setPlatforms] = useState({ email: [], phone: [] });
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchPlatforms = async () => {
      try { const resp = await axios.get(`${API}/platforms`); setPlatforms(resp.data.platforms); } catch (e) {}
      finally { setLoading(false); }
    };
    fetchPlatforms();
  }, []);

  const isAllSelected = selectedPlatforms.length === 0;
  const togglePlatform = (name) => {
    if (selectedPlatforms.includes(name)) onSelectionChange(selectedPlatforms.filter(p => p !== name));
    else onSelectionChange([...selectedPlatforms, name]);
  };
  const formatLabel = (name) => PLATFORM_LABELS[name] || name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');

  if (loading) return <div className="mb-4 p-3 rounded-lg border border-white/[0.04] bg-[#0c0c1d]"><span className="text-[#44445e] text-xs">Chargement...</span></div>;

  return (
    <div className="mb-4">
      <button onClick={() => setIsOpen(!isOpen)} disabled={disabled}
        className={`w-full p-3 rounded-lg border transition-all flex items-center justify-between ${isOpen ? 'border-[#00e5ff]/20 bg-[#00e5ff]/[0.03]' : 'border-white/[0.05] bg-[#0c0c1d] hover:border-white/[0.08]'} ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}
        style={isOpen ? {boxShadow:'0 0 20px rgba(0,229,255,0.04)'} : {}}>
        <div className="flex items-center gap-2.5">
          <Filter className={`w-4 h-4 ${isOpen ? 'text-[#00e5ff]' : 'text-[#44445e]'}`} />
          <span className="text-white text-sm">{isAllSelected ? "Toutes les plateformes" : `${selectedPlatforms.length} sélectionnée(s)`}</span>
        </div>
        {!isAllSelected && selectedPlatforms.length > 0 && selectedPlatforms.length <= 8 && (
          <div className="flex gap-1 items-center">{selectedPlatforms.map(p => <MiniPlatformLogo key={p} name={p} size={14} />)}</div>
        )}
        <svg className={`w-4 h-4 text-[#44445e] transition-transform ${isOpen ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <div className="mt-1.5 p-4 rounded-lg border border-white/[0.05] bg-[#0a0a1a]" style={{boxShadow:'0 0 30px rgba(0,229,255,0.03)'}}>
          <div className="flex gap-2 mb-4">
            <Button size="sm" onClick={() => onSelectionChange([])} className={isAllSelected ? "bg-[#00e5ff] text-[#060612] text-xs h-7 font-semibold btn-glow" : "border-white/[0.06] text-[#7a7a9a] bg-transparent hover:text-white text-xs h-7"} variant={isAllSelected ? "default" : "outline"}>Toutes</Button>
            {!isAllSelected && <Button size="sm" variant="outline" onClick={() => onSelectionChange([])} className="border-white/[0.06] text-[#7a7a9a] bg-transparent hover:text-white text-xs h-7"><X className="w-3 h-3 mr-1" /> Reset</Button>}
          </div>

          <div className="mb-4">
            <h4 className="text-[10px] text-[#ffb020] mb-2 uppercase tracking-wider font-medium" style={{textShadow:'0 0 8px rgba(255,176,32,0.3)'}}>Proxy requis</h4>
            <div className="flex flex-wrap gap-1.5">
              {platforms.email.filter(p => p.type === 'custom').map((platform) => {
                const sel = selectedPlatforms.includes(platform.name) || isAllSelected;
                return (
                  <button key={platform.name} onClick={() => togglePlatform(platform.name)}
                    className={`px-2.5 py-1.5 rounded-md text-[11px] flex items-center gap-1.5 transition-all border ${sel ? 'bg-white/[0.06] text-white border-white/[0.12]' : 'bg-white/[0.02] text-[#44445e] border-white/[0.04] hover:border-white/[0.08] hover:text-[#7a7a9a]'}`}
                    style={sel ? {boxShadow:`0 0 10px ${getPlatformColor(platform.name)}15`} : {}}>
                    <MiniPlatformLogo name={platform.name} size={14} />
                    {formatLabel(platform.name)}
                    {sel && <Check className="w-3 h-3 text-[#00ff88]" style={{filter:'drop-shadow(0 0 3px rgba(0,255,136,0.5))'}} />}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <h4 className="text-[10px] text-[#00e5ff] mb-2 uppercase tracking-wider font-medium" style={{textShadow:'0 0 8px rgba(0,229,255,0.3)'}}>Standard</h4>
            <div className="flex flex-wrap gap-1.5 max-h-[220px] overflow-y-auto pr-1">
              {platforms.email.filter(p => p.type === 'holehe').map((platform) => {
                const sel = selectedPlatforms.includes(platform.name) || isAllSelected;
                return (
                  <button key={platform.name} onClick={() => togglePlatform(platform.name)}
                    className={`px-2.5 py-1.5 rounded-md text-[11px] flex items-center gap-1.5 transition-all border ${sel ? 'bg-white/[0.06] text-white border-white/[0.12]' : 'bg-white/[0.02] text-[#44445e] border-white/[0.04] hover:border-white/[0.08] hover:text-[#7a7a9a]'}`}
                    style={sel ? {boxShadow:`0 0 10px ${getPlatformColor(platform.name)}15`} : {}}>
                    <MiniPlatformLogo name={platform.name} size={14} />
                    {formatLabel(platform.name)}
                    {sel && <Check className="w-3 h-3 text-[#00ff88]" style={{filter:'drop-shadow(0 0 3px rgba(0,255,136,0.5))'}} />}
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
