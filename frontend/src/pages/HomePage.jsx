import { useState, useCallback, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import axios from "axios";
import Header from "../components/Header";
import UploadZone from "../components/UploadZone";
import TextPasteZone from "../components/TextPasteZone";
import ResultsGrid from "../components/ResultsGrid";
import StatsBar from "../components/StatsBar";
import ProxyManager from "../components/ProxyManager";
import PlatformSelector from "../components/PlatformSelector";
import FilePreviewModal from "../components/FilePreviewModal";
import { Button } from "../components/ui/button";
import { Download, Zap, Trash2, ShieldAlert, FileText } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function HomePage() {
  const [results, setResults] = useState([]);
  const [isVerifying, setIsVerifying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [totalToVerify, setTotalToVerify] = useState(0);
  const [verifiedCount, setVerifiedCount] = useState(0);
  const [proxyCount, setProxyCount] = useState(0);
  const [selectedPlatforms, setSelectedPlatforms] = useState([]);
  const [filePreviewData, setFilePreviewData] = useState(null);
  const [isParsing, setIsParsing] = useState(false);

  useEffect(() => {
    const checkProxies = async () => {
      try { const r = await axios.get(`${API}/proxies`); setProxyCount(r.data.active || 0); } catch (e) { setProxyCount(0); }
    };
    checkProxies();
  }, []);

  const handleVerify = useCallback(async (identifiers) => {
    if (!identifiers || identifiers.length === 0) { toast.error("Aucun email ou numéro valide trouvé"); return; }
    setIsVerifying(true); setProgress(0); setVerifiedCount(0); setTotalToVerify(identifiers.length); setResults([]);
    let batchSize = 10;
    try { const tr = await axios.get(`${API}/config/threads?total=${identifiers.length}`); batchSize = tr.data.recommended_batch_size || 10; } catch {}
    const totalBatches = Math.ceil(identifiers.length / batchSize);
    let completedCount = 0;
    try {
      for (let i = 0; i < totalBatches; i++) {
        const batch = identifiers.slice(i * batchSize, (i + 1) * batchSize);
        const req = { identifiers: batch };
        if (selectedPlatforms.length > 0) req.platforms = selectedPlatforms;
        const resp = await axios.post(`${API}/verify`, req);
        setResults(prev => [...prev, ...resp.data.results]);
        completedCount += batch.length;
        setVerifiedCount(completedCount);
        setProgress((completedCount / identifiers.length) * 100);
      }
      toast.success(`${identifiers.length} vérification(s) terminée(s)`);
    } catch (error) {
      if (completedCount > 0) toast.warning(`${completedCount}/${identifiers.length} vérifiés`);
      else toast.error("Erreur lors de la vérification");
    } finally { setIsVerifying(false); setProgress(100); }
  }, [selectedPlatforms]);

  const handleFileUpload = useCallback(async (file) => {
    if (!file) return;
    const fd = new FormData(); fd.append("file", file); setIsParsing(true);
    try { const r = await axios.post(`${API}/parse-file`, fd, { headers: { "Content-Type": "multipart/form-data" } }); setFilePreviewData(r.data); }
    catch (e) { toast.error(e.response?.data?.detail || "Erreur lors de l'analyse"); }
    finally { setIsParsing(false); }
  }, []);

  const handleFilePreviewConfirm = useCallback(async (ids, type) => {
    setFilePreviewData(null);
    if (!ids || ids.length === 0) { toast.error("Aucun identifiant sélectionné"); return; }
    handleVerify(ids);
  }, [handleVerify]);

  // EXPORT: Only FOUND/VALID
  const handleExport = useCallback(() => {
    if (results.length === 0) { toast.error("Aucun résultat"); return; }
    const valid = [];
    results.forEach(r => {
      const found = r.platforms.filter(p => p.status === "found");
      const relevant = selectedPlatforms.length > 0 ? found.filter(p => selectedPlatforms.includes(p.platform)) : found;
      if (relevant.length > 0) valid.push({ id: r.identifier, type: r.identifier_type === "email" ? "Email" : "Tél", platforms: relevant.map(p => p.platform.charAt(0).toUpperCase() + p.platform.slice(1).replace('_', ' ')) });
    });
    if (valid.length === 0) { toast.error("Aucun résultat valide"); return; }
    const csv = ["Identifiant,Type,Plateformes", ...valid.map(v => `"${v.id}","${v.type}","${v.platforms.join(', ')}"`)].join("\n");
    const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url;
    a.download = `diblowcloud_valides_${new Date().toISOString().split("T")[0]}.csv`; a.click(); URL.revokeObjectURL(url);
    toast.success(`${valid.length} valide(s) exporté(s)`);
  }, [results, selectedPlatforms]);

  const handleExportTxt = useCallback(() => {
    if (results.length === 0) { toast.error("Aucun résultat"); return; }
    const valid = [];
    results.forEach(r => {
      const found = r.platforms.filter(p => p.status === "found");
      const relevant = selectedPlatforms.length > 0 ? found.filter(p => selectedPlatforms.includes(p.platform)) : found;
      if (relevant.length > 0) valid.push(r.identifier);
    });
    if (valid.length === 0) { toast.error("Aucun résultat valide"); return; }
    const blob = new Blob([valid.join("\n")], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob); const a = document.createElement("a"); a.href = url;
    a.download = `diblowcloud_valides_${new Date().toISOString().split("T")[0]}.txt`; a.click(); URL.revokeObjectURL(url);
    toast.success(`${valid.length} valide(s) exporté(s)`);
  }, [results, selectedPlatforms]);

  const handleClear = useCallback(() => { setResults([]); setProgress(0); setTotalToVerify(0); setVerifiedCount(0); toast.info("Résultats effacés"); }, []);

  const stats = {
    total: results.length,
    found: results.reduce((a, r) => a + r.platforms.filter(p => p.status === "found").length, 0),
    notFound: results.reduce((a, r) => a + r.platforms.filter(p => p.status === "not_found").length, 0),
    unverifiable: results.reduce((a, r) => a + r.platforms.filter(p => p.status === "unverifiable").length, 0),
    rateLimited: results.reduce((a, r) => a + r.platforms.filter(p => p.status === "rate_limited" || p.status === "error").length, 0),
  };

  const validExportCount = results.filter(r => {
    const f = r.platforms.filter(p => p.status === "found");
    if (f.length === 0) return false;
    return selectedPlatforms.length > 0 ? f.some(p => selectedPlatforms.includes(p.platform)) : true;
  }).length;

  return (
    <div className="min-h-screen bg-[#05050A] relative">
      <Header />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero */}
        <div className="text-center mb-10 animate-fade-in-up">
          <div className="inline-block mb-4">
            <span className="px-4 py-1.5 rounded-full text-xs font-medium bg-white/5 border border-[#00F0FF]/30 text-[#00F0FF]">
              Vérification multi-plateforme ultra-rapide
            </span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tighter mb-3 font-heading">
            <span className="cosmic-gradient">Vérification Rapide</span>
          </h1>
          <p className="text-base text-gray-400 max-w-xl mx-auto leading-relaxed">
            Vérifiez emails et numéros sur Netflix, Uber Eats, Binance, Coinbase, Deliveroo et 30+ plateformes
          </p>
        </div>

        <ProxyManager onProxyChange={(count) => setProxyCount(count)} />
        <PlatformSelector selectedPlatforms={selectedPlatforms} onSelectionChange={setSelectedPlatforms} disabled={isVerifying} />

        {proxyCount === 0 && (
          <div className="mb-6 px-4 py-3 rounded-xl glass-card border-yellow-500/20">
            <div className="flex items-start gap-2.5">
              <ShieldAlert className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-yellow-400 text-xs font-semibold">Aucun proxy configuré</p>
                <p className="text-yellow-400/40 text-[11px] mt-0.5">Netflix, Uber Eats, Binance, Coinbase et Deliveroo nécessitent des proxies résidentiels.</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <UploadZone onFileUpload={handleFileUpload} disabled={isVerifying || isParsing} />
          <TextPasteZone onVerify={handleVerify} disabled={isVerifying} />
        </div>

        <AnimatePresence>
          {isVerifying && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-[#00F0FF] animate-glow-pulse" /> Vérification en cours...
                </span>
                <span className="text-sm font-mono">
                  <span className="text-[#00F0FF]">{verifiedCount}</span>
                  <span className="text-gray-600">/</span>
                  <span className="text-gray-400">{totalToVerify}</span>
                  <span className="text-gray-600 ml-1">({Math.round(progress)}%)</span>
                </span>
              </div>
              <div className="h-2 bg-white/5 rounded-full overflow-hidden border border-white/5">
                <motion.div className="h-full progress-bar rounded-full" initial={{ width: 0 }} animate={{ width: `${progress}%` }} transition={{ duration: 0.3 }} />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {results.length > 0 && (
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <StatsBar stats={stats} />
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={handleClear} data-testid="clear-results-btn"
                  className="border-white/10 text-gray-400 hover:text-white hover:bg-white/5 bg-transparent text-xs h-8">
                  <Trash2 className="w-3.5 h-3.5 mr-1.5" /> Effacer
                </Button>
                <Button size="sm" onClick={handleExport} data-testid="export-results-btn"
                  className="btn-click-effect bg-gradient-to-r from-[#00F0FF] to-[#8B5CF6] text-white font-bold text-xs h-8 hover:opacity-90">
                  <Download className="w-3.5 h-3.5 mr-1.5" /> CSV {validExportCount > 0 && `(${validExportCount})`}
                </Button>
                <Button size="sm" onClick={handleExportTxt} data-testid="export-txt-btn"
                  className="bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 border border-white/10 text-xs h-8">
                  <FileText className="w-3.5 h-3.5 mr-1.5" /> TXT {validExportCount > 0 && `(${validExportCount})`}
                </Button>
              </div>
            </div>
          </div>
        )}

        <ResultsGrid results={results} isLoading={isVerifying} />
      </main>

      {filePreviewData && <FilePreviewModal data={filePreviewData} onConfirm={handleFilePreviewConfirm} onCancel={() => setFilePreviewData(null)} disabled={isVerifying} />}
    </div>
  );
}
