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

function MiniLogo({ name, size = 14 }) {
  const logo = platformLogos[name];
  const color = getPlatformColor(name);
  if (logo) return <div className="flex items-center justify-center flex-shrink-0" style={{ width: size, height: size, color }}>{logo}</div>;
  return <div className="rounded-full flex-shrink-0" style={{ width: size - 4, height: size - 4, backgroundColor: color, opacity: 0.7 }} />;
}

export default function PlatformSelector({ selectedPlatforms, onSelectionChange, disabled }) {
  const [platforms, setPlatforms] = useState({ email: [], phone: [] });
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/platforms`).then(r => setPlatforms(r.data.platforms)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const isAll = selectedPlatforms.length === 0;
  const toggle = (name) => {
    if (selectedPlatforms.includes(name)) onSelectionChange(selectedPlatforms.filter(p => p !== name));
    else onSelectionChange([...selectedPlatforms, name]);
  };
  const fmt = (name) => PLATFORM_LABELS[name] || name.charAt(0).toUpperCase() + name.slice(1).replace(/_/g, ' ');

  if (loading) return <div className="mb-4 p-3 rounded-xl glass-card"><span className="text-gray-500 text-xs">Chargement...</span></div>;

  return (
    <div className="mb-4">
      <button onClick={() => setIsOpen(!isOpen)} disabled={disabled}
        className={`w-full p-3.5 rounded-xl border transition-all flex items-center justify-between ${isOpen ? 'border-purple-500/30 bg-gradient-to-r from-purple-600/10 to-violet-600/10' : 'border-white/10 bg-white/[0.02] hover:bg-white/[0.04] hover:border-purple-500/20'} ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}`}>
        <div className="flex items-center gap-2.5">
          <Filter className={`w-4 h-4 ${isOpen ? 'text-[#8B5CF6]' : 'text-gray-500'}`} />
          <span className="text-white text-sm font-medium">{isAll ? "Toutes les plateformes" : `${selectedPlatforms.length} sélectionnée(s)`}</span>
        </div>
        {!isAll && selectedPlatforms.length <= 8 && <div className="flex gap-1">{selectedPlatforms.map(p => <MiniLogo key={p} name={p} />)}</div>}
        <svg className={`w-4 h-4 text-gray-500 transition-transform ${isOpen ? 'rotate-180' : ''}`} viewBox="0 0 20 20" fill="currentColor">
          <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
        </svg>
      </button>

      {isOpen && (
        <div className="mt-2 p-4 rounded-xl border border-white/10 bg-[#0C0C16]" style={{boxShadow:'0 0 30px rgba(139,92,246,0.06)'}}>
          <div className="flex gap-2 mb-4">
            <Button size="sm" onClick={() => onSelectionChange([])} className={isAll ? 'btn-click-effect bg-gradient-to-r from-[#00F0FF] to-[#8B5CF6] text-white font-bold text-xs h-7' : 'border-white/10 text-gray-400 bg-transparent hover:text-white text-xs h-7'} variant={isAll ? 'default' : 'outline'}>Toutes</Button>
            {!isAll && <Button size="sm" variant="outline" onClick={() => onSelectionChange([])} className="border-white/10 text-gray-400 bg-transparent hover:text-white text-xs h-7"><X className="w-3 h-3 mr-1" /> Reset</Button>}
          </div>

          <div className="mb-4">
            <p className="text-[10px] text-yellow-400 mb-2 uppercase tracking-wider font-bold">Proxy requis</p>
            <div className="flex flex-wrap gap-1.5">
              {platforms.email.filter(p => p.type === 'custom').map(p => {
                const sel = selectedPlatforms.includes(p.name) || isAll;
                return (
                  <button key={p.name} onClick={() => toggle(p.name)}
                    className={`px-2.5 py-1.5 rounded-lg text-[11px] flex items-center gap-1.5 transition-all border ${sel ? 'bg-gradient-to-r from-purple-600/20 to-violet-600/20 text-white border-purple-500/30' : 'bg-white/[0.02] text-gray-500 border-white/5 hover:border-white/10 hover:text-gray-300'}`}>
                    <MiniLogo name={p.name} size={14} />{fmt(p.name)}
                    {sel && <Check className="w-3 h-3 text-green-400" />}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <p className="text-[10px] text-[#00F0FF] mb-2 uppercase tracking-wider font-bold">Standard</p>
            <div className="flex flex-wrap gap-1.5 max-h-[220px] overflow-y-auto pr-1">
              {platforms.email.filter(p => p.type === 'holehe').map(p => {
                const sel = selectedPlatforms.includes(p.name) || isAll;
                return (
                  <button key={p.name} onClick={() => toggle(p.name)}
                    className={`px-2.5 py-1.5 rounded-lg text-[11px] flex items-center gap-1.5 transition-all border ${sel ? 'bg-gradient-to-r from-purple-600/20 to-violet-600/20 text-white border-purple-500/30' : 'bg-white/[0.02] text-gray-500 border-white/5 hover:border-white/10 hover:text-gray-300'}`}>
                    <MiniLogo name={p.name} size={14} />{fmt(p.name)}
                    {sel && <Check className="w-3 h-3 text-green-400" />}
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
