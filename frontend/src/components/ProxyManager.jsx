import { useState, useCallback, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  Shield, Plus, Trash2, RefreshCw, CheckCircle, XCircle,
  AlertCircle, ChevronDown, ChevronUp, Loader2, Globe
} from "lucide-react";
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
    try {
      const response = await axios.get(`${API}/proxies`);
      const proxyList = response.data.proxies || [];
      setProxies(proxyList);
      if (onProxyChange) onProxyChange(proxyList.filter(p => p.status === "active").length);
    } catch (error) {
      console.error("Error fetching proxies:", error);
    }
  }, [onProxyChange]);

  useEffect(() => {
    if (isExpanded) fetchProxies();
  }, [isExpanded, fetchProxies]);

  const handleAddProxies = useCallback(async () => {
    if (!proxyInput.trim()) { toast.error("Entrez au moins un proxy"); return; }
    setIsLoading(true);
    try {
      const proxyList = proxyInput.split(/[\n,]/).map(p => p.trim()).filter(p => p.length > 0);
      const response = await axios.post(`${API}/proxies/add`, { proxies: proxyList, proxy_type: proxyType });
      if (response.data.success) {
        toast.success(response.data.message);
        setProxyInput("");
        const pl = response.data.proxies || [];
        setProxies(pl);
        if (onProxyChange) onProxyChange(pl.filter(p => p.status === "active").length);
      } else { toast.error("Erreur lors de l'ajout"); }
    } catch (error) { toast.error("Erreur lors de l'ajout"); }
    finally { setIsLoading(false); }
  }, [proxyInput, proxyType, onProxyChange]);

  const handleDeleteProxy = useCallback(async (proxyId) => {
    try {
      await axios.delete(`${API}/proxies/${proxyId}`);
      setProxies(prev => {
        const newList = prev.filter(p => p.id !== proxyId);
        if (onProxyChange) onProxyChange(newList.filter(p => p.status === "active").length);
        return newList;
      });
      toast.success("Proxy supprimé");
    } catch (error) { toast.error("Erreur"); }
  }, [onProxyChange]);

  const handleClearAll = useCallback(async () => {
    try {
      await axios.delete(`${API}/proxies`);
      setProxies([]);
      if (onProxyChange) onProxyChange(0);
      toast.success("Tous les proxies supprimés");
    } catch (error) { toast.error("Erreur"); }
  }, [onProxyChange]);

  const handleTestProxies = useCallback(async () => {
    if (proxies.length === 0) { toast.error("Aucun proxy"); return; }
    setIsTesting(true);
    try {
      const response = await axios.post(`${API}/proxies/test`);
      const results = response.data.results || [];
      const working = results.filter(r => r.status === "working").length;
      const failed = results.filter(r => r.status === "failed").length;
      toast.success(`Test: ${working} OK, ${failed} échoué(s)`);
      fetchProxies();
    } catch (error) { toast.error("Erreur test"); }
    finally { setIsTesting(false); }
  }, [proxies, fetchProxies]);

  const activeCount = proxies.filter(p => p.status === "active").length;

  return (
    <div className="mb-4">
      <div className="bg-[#111120] border border-white/[0.06] rounded-xl overflow-hidden">
        {/* Header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
          data-testid="proxy-toggle"
        >
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-[#00ff88]/[0.08] flex items-center justify-center">
              <Shield className="w-4 h-4 text-[#00ff88]" />
            </div>
            <div className="text-left">
              <h3 className="text-white text-sm font-semibold">Proxies</h3>
              <p className="text-[#55556a] text-[11px]">
                {proxies.length === 0 ? "Aucun configuré" : `${activeCount}/${proxies.length} actif(s)`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {proxies.length > 0 && (
              <div className={`w-1.5 h-1.5 rounded-full ${activeCount > 0 ? "bg-[#00ff88]" : "bg-[#ffb020]"}`} />
            )}
            {isExpanded ? <ChevronUp className="w-4 h-4 text-[#55556a]" /> : <ChevronDown className="w-4 h-4 text-[#55556a]" />}
          </div>
        </button>

        {/* Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.15 }}
              className="border-t border-white/[0.04]"
            >
              <div className="p-4 space-y-4">
                {/* Controls */}
                <div className="flex items-center gap-3">
                  <select
                    value={proxyType}
                    onChange={(e) => setProxyType(e.target.value)}
                    className="bg-[#0e0e1a] border border-white/[0.08] rounded-md px-3 py-1.5 text-white text-xs focus:outline-none focus:border-[#00d4ff]/30"
                    data-testid="proxy-type-select"
                  >
                    <option value="auto">Auto</option>
                    <option value="http">HTTP</option>
                    <option value="socks4">SOCKS4</option>
                    <option value="socks5">SOCKS5</option>
                  </select>
                  <Button size="sm" onClick={handleTestProxies} disabled={isTesting || proxies.length === 0}
                    variant="outline" className="border-white/[0.08] text-[#8888a0] hover:text-white bg-transparent text-xs h-7"
                    data-testid="test-proxies-btn">
                    {isTesting ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5 mr-1" />}
                    Test
                  </Button>
                  {proxies.length > 0 && (
                    <Button size="sm" onClick={handleClearAll} variant="outline"
                      className="border-[#ff3860]/20 text-[#ff3860]/70 hover:text-[#ff3860] bg-transparent hover:bg-[#ff3860]/[0.06] text-xs h-7"
                      data-testid="clear-proxies-btn">
                      <Trash2 className="w-3.5 h-3.5 mr-1" /> Tout supprimer
                    </Button>
                  )}
                </div>

                {/* Textarea */}
                <div className="relative">
                  <textarea
                    value={proxyInput}
                    onChange={(e) => setProxyInput(e.target.value)}
                    placeholder={"ip:port\nip:port:user:pass\nuser:pass@ip:port"}
                    className="w-full h-24 rounded-lg p-3 font-mono text-xs resize-none bg-[#0e0e1a] border border-white/[0.08] text-[#00ff88]/70 placeholder:text-[#33334a] focus:outline-none focus:border-[#00ff88]/30 transition-all"
                    data-testid="proxy-input"
                  />
                  <Button size="sm" onClick={handleAddProxies} disabled={isLoading || !proxyInput.trim()}
                    className="absolute bottom-3 right-3 bg-[#00ff88] text-black hover:bg-[#00ff88]/90 text-xs h-7 font-semibold"
                    data-testid="add-proxies-btn">
                    {isLoading ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Plus className="w-3.5 h-3.5 mr-1" />}
                    Ajouter
                  </Button>
                </div>

                {/* Proxy List */}
                {proxies.length > 0 && (
                  <div className="space-y-1.5">
                    <h4 className="text-[10px] text-[#55556a] uppercase tracking-wider">Proxies ({proxies.length})</h4>
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {proxies.map((proxy) => (
                        <div key={proxy.id}
                          className="flex items-center justify-between p-2.5 rounded-lg bg-white/[0.02] border border-white/[0.04] hover:border-white/[0.08] transition-colors"
                          data-testid={`proxy-item-${proxy.id}`}>
                          <div className="flex items-center gap-2.5">
                            <div className={`w-1.5 h-1.5 rounded-full ${proxy.status === "active" ? "bg-[#00ff88]" : "bg-[#ffb020]"}`} />
                            <Globe className="w-3.5 h-3.5 text-[#55556a]" />
                            <div>
                              <p className="text-xs font-mono text-white">{proxy.host}:{proxy.port}</p>
                              <p className="text-[10px] font-mono text-[#55556a]">
                                {proxy.protocol.toUpperCase()}{proxy.has_auth && " · Auth"} · {proxy.requests} req{proxy.failures > 0 && ` · ${proxy.failures} err`}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-1.5">
                            {proxy.status === "active"
                              ? <CheckCircle className="w-3.5 h-3.5 text-[#00ff88]" />
                              : <AlertCircle className="w-3.5 h-3.5 text-[#ffb020]" />}
                            <button onClick={() => handleDeleteProxy(proxy.id)}
                              className="p-1 rounded hover:bg-[#ff3860]/[0.08] text-[#55556a] hover:text-[#ff3860] transition-colors"
                              data-testid={`delete-proxy-${proxy.id}`}>
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Info */}
                <div className="p-3 rounded-lg bg-[#00ff88]/[0.03] border border-[#00ff88]/10">
                  <p className="text-[11px] text-[#00ff88]/50">
                    Proxies en rotation. Formats: HTTP, SOCKS4, SOCKS5. Inactif après 3 échecs.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
