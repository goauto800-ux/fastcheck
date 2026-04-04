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
    try { const r = await axios.get(`${API}/proxies`); const pl = r.data.proxies || []; setProxies(pl); if (onProxyChange) onProxyChange(pl.filter(p => p.status === "active").length); } catch {}
  }, [onProxyChange]);

  useEffect(() => { if (isExpanded) fetchProxies(); }, [isExpanded, fetchProxies]);

  const handleAdd = useCallback(async () => {
    if (!proxyInput.trim()) { toast.error("Entrez au moins un proxy"); return; }
    setIsLoading(true);
    try {
      const list = proxyInput.split(/[\n,]/).map(s => s.trim()).filter(s => s);
      const r = await axios.post(`${API}/proxies/add`, { proxies: list, proxy_type: proxyType });
      if (r.data.success) { toast.success(r.data.message); setProxyInput(""); const pl = r.data.proxies || []; setProxies(pl); if (onProxyChange) onProxyChange(pl.filter(p => p.status === "active").length); }
    } catch { toast.error("Erreur"); } finally { setIsLoading(false); }
  }, [proxyInput, proxyType, onProxyChange]);

  const handleDelete = useCallback(async (id) => {
    try { await axios.delete(`${API}/proxies/${id}`); setProxies(prev => { const n = prev.filter(p => p.id !== id); if (onProxyChange) onProxyChange(n.filter(p => p.status === "active").length); return n; }); toast.success("Supprimé"); } catch { toast.error("Erreur"); }
  }, [onProxyChange]);

  const handleClearAll = useCallback(async () => {
    try { await axios.delete(`${API}/proxies`); setProxies([]); if (onProxyChange) onProxyChange(0); toast.success("Tout supprimé"); } catch { toast.error("Erreur"); }
  }, [onProxyChange]);

  const handleTest = useCallback(async () => {
    if (!proxies.length) { toast.error("Aucun proxy"); return; }
    setIsTesting(true);
    try { const r = await axios.post(`${API}/proxies/test`); const res = r.data.results || []; toast.success(`${res.filter(x=>x.status==="working").length} OK, ${res.filter(x=>x.status==="failed").length} échoué(s)`); fetchProxies(); }
    catch { toast.error("Erreur"); } finally { setIsTesting(false); }
  }, [proxies, fetchProxies]);

  const active = proxies.filter(p => p.status === "active").length;

  return (
    <div className="mb-4">
      <div className="glass-card rounded-xl overflow-hidden">
        <button onClick={() => setIsExpanded(!isExpanded)} className="w-full px-4 py-3.5 flex items-center justify-between hover:bg-white/[0.02] transition-colors" data-testid="proxy-toggle">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-green-500/20 to-emerald-600/20 flex items-center justify-center">
              <Shield className="w-4 h-4 text-green-400" />
            </div>
            <div className="text-left">
              <h3 className="text-white text-sm font-semibold">Proxies</h3>
              <p className="text-gray-500 text-[11px]">{proxies.length === 0 ? "Aucun configuré" : `${active}/${proxies.length} actif(s)`}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {proxies.length > 0 && <div className={`w-2 h-2 rounded-full ${active > 0 ? 'bg-green-400' : 'bg-yellow-400'}`} style={active > 0 ? {boxShadow:'0 0 8px rgba(74,222,128,0.5)'} : {}} />}
            {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
          </div>
        </button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.2 }} className="border-t border-white/5">
              <div className="p-4 space-y-4">
                <div className="flex items-center gap-3">
                  <select value={proxyType} onChange={e => setProxyType(e.target.value)} className="bg-[#0C0C16] border border-white/10 rounded-lg px-3 py-1.5 text-white text-xs focus:outline-none focus:border-[#00F0FF]/40" data-testid="proxy-type-select">
                    <option value="auto">Auto</option><option value="http">HTTP</option><option value="socks4">SOCKS4</option><option value="socks5">SOCKS5</option>
                  </select>
                  <Button size="sm" onClick={handleTest} disabled={isTesting || !proxies.length} variant="outline" className="border-white/10 text-gray-400 hover:text-white bg-transparent text-xs h-7" data-testid="test-proxies-btn">
                    {isTesting ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5 mr-1" />} Test
                  </Button>
                  {proxies.length > 0 && <Button size="sm" onClick={handleClearAll} variant="outline" className="border-red-500/20 text-red-400/60 hover:text-red-400 bg-transparent text-xs h-7" data-testid="clear-proxies-btn"><Trash2 className="w-3.5 h-3.5 mr-1" /> Tout supprimer</Button>}
                </div>
                <div className="relative">
                  <textarea value={proxyInput} onChange={e => setProxyInput(e.target.value)} placeholder={"ip:port\nip:port:user:pass"}
                    className="w-full h-24 rounded-lg p-3 font-mono text-xs resize-none bg-[#0C0C16] border border-white/10 text-green-400/60 placeholder:text-gray-700 focus:outline-none focus:border-green-400/30 transition-all" data-testid="proxy-input" />
                  <Button size="sm" onClick={handleAdd} disabled={isLoading || !proxyInput.trim()}
                    className="absolute bottom-3 right-3 btn-click-effect bg-gradient-to-r from-green-500 to-emerald-600 text-white font-bold text-xs h-7 hover:opacity-90" data-testid="add-proxies-btn">
                    {isLoading ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Plus className="w-3.5 h-3.5 mr-1" />} Ajouter
                  </Button>
                </div>
                {proxies.length > 0 && (
                  <div className="space-y-1.5">
                    <p className="text-[10px] text-gray-500 uppercase tracking-wider font-bold">Proxies ({proxies.length})</p>
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {proxies.map(proxy => (
                        <div key={proxy.id} className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] border border-white/5 hover:border-white/10 transition-colors" data-testid={`proxy-item-${proxy.id}`}>
                          <div className="flex items-center gap-2.5">
                            <div className={`w-2 h-2 rounded-full ${proxy.status === 'active' ? 'bg-green-400' : 'bg-yellow-400'}`} />
                            <Globe className="w-3.5 h-3.5 text-gray-500" />
                            <div>
                              <p className="text-xs font-mono text-white">{proxy.host}:{proxy.port}</p>
                              <p className="text-[10px] font-mono text-gray-600">{proxy.protocol.toUpperCase()}{proxy.has_auth && ' · Auth'} · {proxy.requests} req</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-1.5">
                            {proxy.status === 'active' ? <CheckCircle className="w-3.5 h-3.5 text-green-400" /> : <AlertCircle className="w-3.5 h-3.5 text-yellow-400" />}
                            <button onClick={() => handleDelete(proxy.id)} className="p-1 rounded hover:bg-red-500/10 text-gray-600 hover:text-red-400 transition-colors" data-testid={`delete-proxy-${proxy.id}`}><Trash2 className="w-3.5 h-3.5" /></button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="p-3 rounded-lg bg-green-500/5 border border-green-500/10">
                  <p className="text-[11px] text-green-400/40">Proxies en rotation. Formats: HTTP, SOCKS4, SOCKS5. Inactif après 3 échecs.</p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
