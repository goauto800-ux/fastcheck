import { useState, useCallback, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Shield, Plus, Trash2, RefreshCw, CheckCircle, AlertCircle, ChevronDown, ChevronUp, Loader2, Globe } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ProxyManager({ onProxyChange }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [proxies, setProxies] = useState([]);
  const [proxyInput, setProxyInput] = useState("");
  const [proxyType, setProxyType] = useState("auto");
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  const fetchProxies = useCallback(async () => {
    try { const r = await axios.get(`${API}/proxies`); const pl = r.data.proxies || []; setProxies(pl); if (onProxyChange) onProxyChange(pl.filter(p => p.status === "active").length); } catch (e) {}
  }, [onProxyChange]);

  useEffect(() => { if (isExpanded) fetchProxies(); }, [isExpanded, fetchProxies]);

  const handleAddProxies = useCallback(async () => {
    if (!proxyInput.trim()) { toast.error("Entrez au moins un proxy"); return; }
    setIsLoading(true);
    try {
      const list = proxyInput.split(/[\n,]/).map(p => p.trim()).filter(p => p.length > 0);
      const r = await axios.post(`${API}/proxies/add`, { proxies: list, proxy_type: proxyType });
      if (r.data.success) { toast.success(r.data.message); setProxyInput(""); const pl = r.data.proxies || []; setProxies(pl); if (onProxyChange) onProxyChange(pl.filter(p => p.status === "active").length); }
    } catch (e) { toast.error("Erreur"); } finally { setIsLoading(false); }
  }, [proxyInput, proxyType, onProxyChange]);

  const handleDeleteProxy = useCallback(async (id) => {
    try { await axios.delete(`${API}/proxies/${id}`); setProxies(prev => { const n = prev.filter(p => p.id !== id); if (onProxyChange) onProxyChange(n.filter(p => p.status === "active").length); return n; }); toast.success("Supprimé"); } catch (e) { toast.error("Erreur"); }
  }, [onProxyChange]);

  const handleClearAll = useCallback(async () => {
    try { await axios.delete(`${API}/proxies`); setProxies([]); if (onProxyChange) onProxyChange(0); toast.success("Tout supprimé"); } catch (e) { toast.error("Erreur"); }
  }, [onProxyChange]);

  const handleTestProxies = useCallback(async () => {
    if (proxies.length === 0) { toast.error("Aucun proxy"); return; }
    setIsTesting(true);
    try { const r = await axios.post(`${API}/proxies/test`); const res = r.data.results || []; toast.success(`Test: ${res.filter(r=>r.status==="working").length} OK, ${res.filter(r=>r.status==="failed").length} échoué(s)`); fetchProxies(); } catch (e) { toast.error("Erreur"); } finally { setIsTesting(false); }
  }, [proxies, fetchProxies]);

  const activeCount = proxies.filter(p => p.status === "active").length;

  return (
    <div className="mb-4">
      <div className="bg-[#0c0c1d] border border-white/[0.05] rounded-xl overflow-hidden" style={{boxShadow:'0 0 25px rgba(0,255,136,0.02)'}}>
        <button onClick={() => setIsExpanded(!isExpanded)} className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/[0.015] transition-colors" data-testid="proxy-toggle">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#00ff88]/[0.07] flex items-center justify-center" style={{boxShadow:'0 0 15px rgba(0,255,136,0.08)'}}>
              <Shield className="w-4 h-4 text-[#00ff88]" />
            </div>
            <div className="text-left">
              <h3 className="text-white text-sm font-semibold">Proxies</h3>
              <p className="text-[#44445e] text-[11px]">{proxies.length === 0 ? "Aucun configuré" : `${activeCount}/${proxies.length} actif(s)`}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {proxies.length > 0 && <div className={`w-1.5 h-1.5 rounded-full ${activeCount > 0 ? "bg-[#00ff88]" : "bg-[#ffb020]"}`} style={activeCount > 0 ? {boxShadow:'0 0 6px rgba(0,255,136,0.5)'} : {}} />}
            {isExpanded ? <ChevronUp className="w-4 h-4 text-[#44445e]" /> : <ChevronDown className="w-4 h-4 text-[#44445e]" />}
          </div>
        </button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.15 }} className="border-t border-white/[0.03]">
              <div className="p-4 space-y-4">
                <div className="flex items-center gap-3">
                  <select value={proxyType} onChange={(e) => setProxyType(e.target.value)} className="bg-[#0a0a1a] border border-white/[0.06] rounded-md px-3 py-1.5 text-white text-xs focus:outline-none focus:border-[#00e5ff]/20" data-testid="proxy-type-select">
                    <option value="auto">Auto</option><option value="http">HTTP</option><option value="socks4">SOCKS4</option><option value="socks5">SOCKS5</option>
                  </select>
                  <Button size="sm" onClick={handleTestProxies} disabled={isTesting || proxies.length === 0} variant="outline" className="border-white/[0.06] text-[#7a7a9a] hover:text-white bg-transparent text-xs h-7" data-testid="test-proxies-btn">
                    {isTesting ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5 mr-1" />} Test
                  </Button>
                  {proxies.length > 0 && <Button size="sm" onClick={handleClearAll} variant="outline" className="border-[#ff3060]/15 text-[#ff3060]/60 hover:text-[#ff3060] bg-transparent text-xs h-7" data-testid="clear-proxies-btn"><Trash2 className="w-3.5 h-3.5 mr-1" /> Tout supprimer</Button>}
                </div>

                <div className="relative">
                  <textarea value={proxyInput} onChange={(e) => setProxyInput(e.target.value)} placeholder={"ip:port\nip:port:user:pass"}
                    className="w-full h-24 rounded-lg p-3 font-mono text-xs resize-none bg-[#0a0a1a] border border-white/[0.06] text-[#00ff88]/60 placeholder:text-[#2a2a40] focus:outline-none focus:border-[#00ff88]/20 transition-all"
                    style={{boxShadow:'inset 0 0 20px rgba(0,255,136,0.02)'}} data-testid="proxy-input" />
                  <Button size="sm" onClick={handleAddProxies} disabled={isLoading || !proxyInput.trim()}
                    className="absolute bottom-3 right-3 bg-[#00ff88] text-[#060612] hover:bg-[#00ff88]/90 text-xs h-7 font-semibold btn-glow-green" data-testid="add-proxies-btn">
                    {isLoading ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Plus className="w-3.5 h-3.5 mr-1" />} Ajouter
                  </Button>
                </div>

                {proxies.length > 0 && (
                  <div className="space-y-1.5">
                    <h4 className="text-[10px] text-[#44445e] uppercase tracking-wider">Proxies ({proxies.length})</h4>
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {proxies.map((proxy) => (
                        <div key={proxy.id} className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.015] border border-white/[0.04] hover:border-white/[0.06] transition-colors" data-testid={`proxy-item-${proxy.id}`}>
                          <div className="flex items-center gap-2.5">
                            <div className={`w-1.5 h-1.5 rounded-full ${proxy.status === "active" ? "bg-[#00ff88]" : "bg-[#ffb020]"}`} style={proxy.status === "active" ? {boxShadow:'0 0 6px rgba(0,255,136,0.5)'} : {}} />
                            <Globe className="w-3.5 h-3.5 text-[#44445e]" />
                            <div>
                              <p className="text-xs font-mono text-white">{proxy.host}:{proxy.port}</p>
                              <p className="text-[10px] font-mono text-[#44445e]">{proxy.protocol.toUpperCase()}{proxy.has_auth && " · Auth"} · {proxy.requests} req{proxy.failures > 0 && ` · ${proxy.failures} err`}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-1.5">
                            {proxy.status === "active" ? <CheckCircle className="w-3.5 h-3.5 text-[#00ff88]" /> : <AlertCircle className="w-3.5 h-3.5 text-[#ffb020]" />}
                            <button onClick={() => handleDeleteProxy(proxy.id)} className="p-1 rounded hover:bg-[#ff3060]/[0.06] text-[#44445e] hover:text-[#ff3060] transition-colors" data-testid={`delete-proxy-${proxy.id}`}><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="p-3 rounded-lg bg-[#00ff88]/[0.02] border border-[#00ff88]/[0.08]">
                  <p className="text-[11px] text-[#00ff88]/40">Proxies en rotation. Formats: HTTP, SOCKS4, SOCKS5. Inactif après 3 échecs.</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
