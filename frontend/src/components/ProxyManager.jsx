import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Shield, Plus, Trash2, RefreshCw, CheckCircle, XCircle, 
  AlertCircle, ChevronDown, ChevronUp, Loader2, Globe
} from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ProxyManager() {
  const [isExpanded, setIsExpanded] = useState(false);
  const [proxies, setProxies] = useState([]);
  const [proxyInput, setProxyInput] = useState("");
  const [proxyType, setProxyType] = useState("auto");
  const [isLoading, setIsLoading] = useState(false);
  const [isTesting, setIsTesting] = useState(false);

  const fetchProxies = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/proxies`);
      setProxies(response.data.proxies || []);
    } catch (error) {
      console.error("Error fetching proxies:", error);
    }
  }, []);

  useEffect(() => {
    if (isExpanded) {
      fetchProxies();
    }
  }, [isExpanded, fetchProxies]);

  const handleAddProxies = useCallback(async () => {
    if (!proxyInput.trim()) {
      toast.error("Entrez au moins un proxy");
      return;
    }

    setIsLoading(true);
    try {
      // Parse proxies from input (one per line or comma separated)
      const proxyList = proxyInput
        .split(/[\n,]/)
        .map(p => p.trim())
        .filter(p => p.length > 0);

      const response = await axios.post(`${API}/proxies/add`, {
        proxies: proxyList,
        proxy_type: proxyType
      });

      if (response.data.success) {
        toast.success(response.data.message);
        setProxyInput("");
        setProxies(response.data.proxies || []);
      } else {
        toast.error("Erreur lors de l'ajout des proxies");
      }
    } catch (error) {
      console.error("Error adding proxies:", error);
      toast.error("Erreur lors de l'ajout des proxies");
    } finally {
      setIsLoading(false);
    }
  }, [proxyInput, proxyType]);

  const handleDeleteProxy = useCallback(async (proxyId) => {
    try {
      await axios.delete(`${API}/proxies/${proxyId}`);
      setProxies(prev => prev.filter(p => p.id !== proxyId));
      toast.success("Proxy supprimé");
    } catch (error) {
      console.error("Error deleting proxy:", error);
      toast.error("Erreur lors de la suppression");
    }
  }, []);

  const handleClearAll = useCallback(async () => {
    try {
      await axios.delete(`${API}/proxies`);
      setProxies([]);
      toast.success("Tous les proxies supprimés");
    } catch (error) {
      console.error("Error clearing proxies:", error);
      toast.error("Erreur lors de la suppression");
    }
  }, []);

  const handleTestProxies = useCallback(async () => {
    if (proxies.length === 0) {
      toast.error("Aucun proxy à tester");
      return;
    }

    setIsTesting(true);
    try {
      const response = await axios.post(`${API}/proxies/test`);
      const results = response.data.results || [];
      
      const working = results.filter(r => r.status === "working").length;
      const failed = results.filter(r => r.status === "failed").length;
      
      toast.success(`Test terminé: ${working} fonctionnel(s), ${failed} échoué(s)`);
      fetchProxies();
    } catch (error) {
      console.error("Error testing proxies:", error);
      toast.error("Erreur lors du test des proxies");
    } finally {
      setIsTesting(false);
    }
  }, [proxies, fetchProxies]);

  const activeCount = proxies.filter(p => p.status === "active").length;

  return (
    <div className="mb-8">
      <motion.div
        className="bg-white/[0.02] border border-white/[0.05] rounded-2xl overflow-hidden"
        initial={false}
      >
        {/* Header */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full px-6 py-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors"
          data-testid="proxy-toggle"
        >
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 flex items-center justify-center">
              <Shield className="w-5 h-5 text-emerald-400" />
            </div>
            <div className="text-left">
              <h3 className="text-white font-semibold font-heading">Proxies Rotatifs</h3>
              <p className="text-slate-500 text-xs font-mono">
                {proxies.length === 0 
                  ? "Aucun proxy configuré" 
                  : `${activeCount}/${proxies.length} actif(s)`
                }
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {proxies.length > 0 && (
              <div className={`w-2 h-2 rounded-full ${activeCount > 0 ? "bg-emerald-400" : "bg-orange-400"}`} />
            )}
            {isExpanded ? (
              <ChevronUp className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            )}
          </div>
        </button>

        {/* Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: "auto", opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="border-t border-white/5"
            >
              <div className="p-6 space-y-6">
                {/* Add Proxy Form */}
                <div className="space-y-4">
                  <div className="flex items-center gap-4">
                    <select
                      value={proxyType}
                      onChange={(e) => setProxyType(e.target.value)}
                      className="bg-white/5 border border-white/10 rounded-lg px-4 py-2 text-white text-sm font-mono focus:outline-none focus:border-emerald-500/50"
                      data-testid="proxy-type-select"
                    >
                      <option value="auto">Auto-detect</option>
                      <option value="http">HTTP/HTTPS</option>
                      <option value="socks4">SOCKS4</option>
                      <option value="socks5">SOCKS5</option>
                    </select>
                    <Button
                      size="sm"
                      onClick={handleTestProxies}
                      disabled={isTesting || proxies.length === 0}
                      variant="outline"
                      className="border-white/10 text-slate-400 hover:text-white bg-transparent"
                      data-testid="test-proxies-btn"
                    >
                      {isTesting ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <RefreshCw className="w-4 h-4 mr-2" />
                      )}
                      Tester
                    </Button>
                    {proxies.length > 0 && (
                      <Button
                        size="sm"
                        onClick={handleClearAll}
                        variant="outline"
                        className="border-red-500/30 text-red-400 hover:text-red-300 bg-transparent hover:bg-red-500/10"
                        data-testid="clear-proxies-btn"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Tout supprimer
                      </Button>
                    )}
                  </div>

                  <div className="relative">
                    <textarea
                      value={proxyInput}
                      onChange={(e) => setProxyInput(e.target.value)}
                      placeholder={`Ajoutez vos proxies (un par ligne):\n\nFormats supportés:\n• ip:port\n• ip:port:user:pass\n• user:pass@ip:port\n• http://ip:port\n• socks5://user:pass@ip:port`}
                      className="w-full h-32 rounded-xl p-4 font-mono text-sm resize-none
                        bg-[#0A0710] border border-white/10 text-emerald-300
                        placeholder:text-slate-600
                        focus:outline-none focus:border-emerald-500/50 focus:ring-2 focus:ring-emerald-500/20
                        transition-all duration-300"
                      data-testid="proxy-input"
                    />
                    <Button
                      size="sm"
                      onClick={handleAddProxies}
                      disabled={isLoading || !proxyInput.trim()}
                      className="absolute bottom-4 right-4 bg-gradient-to-r from-emerald-600 to-green-600"
                      data-testid="add-proxies-btn"
                    >
                      {isLoading ? (
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      ) : (
                        <Plus className="w-4 h-4 mr-2" />
                      )}
                      Ajouter
                    </Button>
                  </div>
                </div>

                {/* Proxy List */}
                {proxies.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-mono text-slate-400 uppercase tracking-wider">
                      Proxies ({proxies.length})
                    </h4>
                    <div className="space-y-2 max-h-60 overflow-y-auto custom-scrollbar">
                      {proxies.map((proxy) => (
                        <div
                          key={proxy.id}
                          className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/5 hover:border-white/10 transition-colors"
                          data-testid={`proxy-item-${proxy.id}`}
                        >
                          <div className="flex items-center gap-3">
                            <div className={`w-2 h-2 rounded-full ${
                              proxy.status === "active" ? "bg-emerald-400" : "bg-orange-400"
                            }`} />
                            <Globe className="w-4 h-4 text-slate-500" />
                            <div>
                              <p className="text-sm font-mono text-white">
                                {proxy.host}:{proxy.port}
                              </p>
                              <p className="text-xs font-mono text-slate-500">
                                {proxy.protocol.toUpperCase()} 
                                {proxy.has_auth && " • Auth"} 
                                • {proxy.requests} req 
                                {proxy.failures > 0 && ` • ${proxy.failures} err`}
                              </p>
                            </div>
                          </div>
                          <div className="flex items-center gap-2">
                            {proxy.status === "active" ? (
                              <CheckCircle className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <AlertCircle className="w-4 h-4 text-orange-400" />
                            )}
                            <button
                              onClick={() => handleDeleteProxy(proxy.id)}
                              className="p-1.5 rounded-lg hover:bg-red-500/10 text-slate-500 hover:text-red-400 transition-colors"
                              data-testid={`delete-proxy-${proxy.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Info */}
                <div className="p-4 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                  <p className="text-xs text-emerald-400/80 font-mono">
                    💡 Les proxies sont utilisés en rotation pour éviter les rate limits.
                    Formats: HTTP, HTTPS, SOCKS4, SOCKS5. 
                    Un proxy inactif après 3 échecs est automatiquement désactivé.
                  </p>
                </div>

                {/* Warning for platforms needing proxies */}
                <div className="p-4 rounded-lg bg-orange-500/5 border border-orange-500/20">
                  <p className="text-xs text-orange-400/80 font-mono">
                    ⚠️ <strong>Netflix, Uber Eats, Deliveroo, Binance, Coinbase</strong> nécessitent des 
                    <strong> proxies résidentiels</strong> pour fonctionner correctement. 
                    Sans proxies, ces plateformes retourneront souvent "Non trouvé" même si le compte existe.
                    Les proxies datacenter sont généralement bloqués.
                  </p>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
