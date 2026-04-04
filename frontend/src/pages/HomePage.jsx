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
      try {
        const resp = await axios.get(`${API}/proxies`);
        setProxyCount(resp.data.active || 0);
      } catch (e) {
        setProxyCount(0);
      }
    };
    checkProxies();
  }, []);

  const handleVerify = useCallback(async (identifiers) => {
    if (!identifiers || identifiers.length === 0) {
      toast.error("Aucun email ou numéro valide trouvé");
      return;
    }

    setIsVerifying(true);
    setProgress(0);
    setVerifiedCount(0);
    setTotalToVerify(identifiers.length);
    setResults([]);

    let batchSize = 5;
    try {
      const threadResp = await axios.get(`${API}/config/threads?total=${identifiers.length}`);
      batchSize = threadResp.data.recommended_batch_size || 5;
    } catch {
      // fallback
    }

    const totalBatches = Math.ceil(identifiers.length / batchSize);
    let completedCount = 0;

    try {
      for (let i = 0; i < totalBatches; i++) {
        const batch = identifiers.slice(i * batchSize, (i + 1) * batchSize);
        const requestData = { identifiers: batch };
        if (selectedPlatforms.length > 0) {
          requestData.platforms = selectedPlatforms;
        }

        const response = await axios.post(`${API}/verify`, requestData);
        const batchResults = response.data.results;

        setResults((prev) => [...prev, ...batchResults]);
        completedCount += batch.length;
        setVerifiedCount(completedCount);
        setProgress((completedCount / identifiers.length) * 100);
      }

      toast.success(`${identifiers.length} vérification(s) terminée(s)`);
    } catch (error) {
      console.error("Verification error:", error);
      if (completedCount > 0) {
        toast.warning(`${completedCount}/${identifiers.length} vérifiés — erreur sur le reste`);
      } else {
        toast.error("Erreur lors de la vérification");
      }
    } finally {
      setIsVerifying(false);
      setProgress(100);
    }
  }, [selectedPlatforms]);

  const handleFileUpload = useCallback(async (file) => {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setIsParsing(true);
    try {
      const response = await axios.post(`${API}/parse-file`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setFilePreviewData(response.data);
    } catch (error) {
      console.error("File parse error:", error);
      const message = error.response?.data?.detail || "Erreur lors de l'analyse du fichier";
      toast.error(message);
    } finally {
      setIsParsing(false);
    }
  }, []);

  const handleFilePreviewConfirm = useCallback(async (identifiers, type) => {
    setFilePreviewData(null);
    if (!identifiers || identifiers.length === 0) {
      toast.error("Aucun identifiant sélectionné");
      return;
    }
    const typeLabel = type === "email" ? "emails" : type === "phone" ? "numéros" : "identifiants";
    toast.info(`Vérification de ${identifiers.length} ${typeLabel}...`);
    handleVerify(identifiers);
  }, [handleVerify]);

  const handleFilePreviewCancel = useCallback(() => {
    setFilePreviewData(null);
  }, []);

  const handleExport = useCallback(() => {
    if (results.length === 0) {
      toast.error("Aucun résultat à exporter");
      return;
    }
    const allPlatforms = new Set();
    results.forEach(r => r.platforms.forEach(p => allPlatforms.add(p.platform)));
    const platformList = Array.from(allPlatforms).sort();
    const headers = ["Identifiant", "Type", ...platformList.map(p => p.charAt(0).toUpperCase() + p.slice(1).replace('_', ' '))];
    const rows = results.map((r) => {
      const platformStatuses = {};
      r.platforms.forEach((p) => {
        const statusMap = {
          "found": "Trouvé",
          "not_found": "Non trouvé",
          "unverifiable": "Non vérifiable (proxy requis)",
          "rate_limited": "Limité",
          "error": "Erreur"
        };
        platformStatuses[p.platform] = statusMap[p.status] || p.status;
      });
      return [
        r.identifier,
        r.identifier_type === "email" ? "Email" : "Téléphone",
        ...platformList.map(p => platformStatuses[p] || "-"),
      ];
    });
    const csvContent = [headers, ...rows].map((row) => row.map(cell => `"${cell}"`).join(",")).join("\n");
    const blob = new Blob(["\uFEFF" + csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `fast_results_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("Résultats exportés en CSV");
  }, [results]);

  const handleExportTxt = useCallback(() => {
    if (results.length === 0) {
      toast.error("Aucun résultat à exporter");
      return;
    }
    const statusMap = {
      "found": "✓ Trouvé",
      "not_found": "✗ Non trouvé",
      "unverifiable": "⚠ Non vérifiable",
      "rate_limited": "⏳ Limité",
      "error": "⚠ Erreur"
    };
    let txtContent = "═══════════════════════════════════════════\n";
    txtContent += "       FAST — Résultats de vérification\n";
    txtContent += `       Date: ${new Date().toLocaleDateString('fr-FR')}\n`;
    txtContent += "═══════════════════════════════════════════\n\n";
    results.forEach((r) => {
      const type = r.identifier_type === "email" ? "Email" : "Téléphone";
      const foundCount = r.platforms.filter(p => p.status === "found").length;
      const totalCount = r.platforms.length;
      txtContent += `┌─── ${type}: ${r.identifier}\n`;
      txtContent += `│    Trouvé sur ${foundCount}/${totalCount} plateformes\n`;
      txtContent += `│\n`;
      r.platforms.forEach((p) => {
        const name = p.platform.charAt(0).toUpperCase() + p.platform.slice(1).replace('_', ' ');
        const status = statusMap[p.status] || p.status;
        txtContent += `│  ${status.padEnd(22)} ${name}\n`;
      });
      txtContent += `└${"─".repeat(44)}\n\n`;
    });
    const totalFound = results.reduce((acc, r) => acc + r.platforms.filter(p => p.status === "found").length, 0);
    const totalNotFound = results.reduce((acc, r) => acc + r.platforms.filter(p => p.status === "not_found").length, 0);
    const totalUnverifiable = results.reduce((acc, r) => acc + r.platforms.filter(p => p.status === "unverifiable").length, 0);
    txtContent += "═══════════════════════════════════════════\n";
    txtContent += "                 RÉSUMÉ\n";
    txtContent += "═══════════════════════════════════════════\n";
    txtContent += `  Identifiants vérifiés: ${results.length}\n`;
    txtContent += `  Trouvés: ${totalFound}\n`;
    txtContent += `  Non trouvés: ${totalNotFound}\n`;
    txtContent += `  Non vérifiables: ${totalUnverifiable}\n`;
    txtContent += "═══════════════════════════════════════════\n";
    const blob = new Blob([txtContent], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `fast_results_${new Date().toISOString().split("T")[0]}.txt`;
    link.click();
    URL.revokeObjectURL(url);
    toast.success("Résultats exportés en TXT");
  }, [results]);

  const handleClear = useCallback(() => {
    setResults([]);
    setProgress(0);
    setTotalToVerify(0);
    setVerifiedCount(0);
    toast.info("Résultats effacés");
  }, []);

  const stats = {
    total: results.length,
    found: results.reduce((acc, r) => acc + r.platforms.filter((p) => p.status === "found").length, 0),
    notFound: results.reduce((acc, r) => acc + r.platforms.filter((p) => p.status === "not_found").length, 0),
    unverifiable: results.reduce((acc, r) => acc + r.platforms.filter((p) => p.status === "unverifiable").length, 0),
    rateLimited: results.reduce((acc, r) => acc + r.platforms.filter((p) => p.status === "rate_limited" || p.status === "error").length, 0),
  };

  return (
    <div className="min-h-screen bg-[#080810]">
      <Header />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero */}
        <div className="text-center mb-10">
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight mb-2 text-white">
            Vérification <span className="text-[#00d4ff]">Rapide</span>
          </h1>
          <p className="text-sm text-[#55556a] max-w-xl mx-auto">
            Vérifiez emails et numéros sur Netflix, Uber Eats, Binance, Coinbase, Deliveroo et 30+ plateformes
          </p>
        </div>

        {/* Proxy Manager */}
        <ProxyManager onProxyChange={(count) => setProxyCount(count)} />

        {/* Platform Selector */}
        <PlatformSelector
          selectedPlatforms={selectedPlatforms}
          onSelectionChange={setSelectedPlatforms}
          disabled={isVerifying}
        />

        {/* Proxy Warning */}
        {proxyCount === 0 && (
          <div className="mb-6 px-4 py-3 rounded-lg border border-[#ffb020]/20 bg-[#ffb020]/[0.04]">
            <div className="flex items-start gap-2.5">
              <ShieldAlert className="w-4 h-4 text-[#ffb020] flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-[#ffb020] text-xs font-medium">Aucun proxy configuré</p>
                <p className="text-[#ffb020]/50 text-[11px] mt-0.5">
                  Netflix, Uber Eats, Binance, Coinbase et Deliveroo nécessitent des proxies résidentiels.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Input Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <UploadZone onFileUpload={handleFileUpload} disabled={isVerifying || isParsing} />
          <TextPasteZone onVerify={handleVerify} disabled={isVerifying} />
        </div>

        {/* Progress Bar */}
        <AnimatePresence>
          {isVerifying && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              className="mb-6"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-[#8888a0] flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-[#00d4ff] animate-pulse" />
                  Vérification en cours...
                </span>
                <span className="text-xs font-mono">
                  <span className="text-[#00d4ff]">{verifiedCount}</span>
                  <span className="text-[#55556a]">/</span>
                  <span className="text-[#8888a0]">{totalToVerify}</span>
                  <span className="text-[#55556a] ml-1">({Math.round(progress)}%)</span>
                </span>
              </div>
              <div className="h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                <motion.div
                  className="h-full progress-bar rounded-full"
                  initial={{ width: 0 }}
                  animate={{ width: `${progress}%` }}
                  transition={{ duration: 0.4 }}
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Stats & Actions */}
        {results.length > 0 && (
          <div className="mb-6">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <StatsBar stats={stats} />
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleClear}
                  data-testid="clear-results-btn"
                  className="border-white/[0.08] text-[#8888a0] hover:text-white hover:border-white/[0.15] bg-transparent text-xs h-8"
                >
                  <Trash2 className="w-3.5 h-3.5 mr-1.5" />
                  Effacer
                </Button>
                <Button
                  size="sm"
                  onClick={handleExport}
                  data-testid="export-results-btn"
                  className="bg-[#00d4ff]/10 text-[#00d4ff] hover:bg-[#00d4ff]/20 border border-[#00d4ff]/20 text-xs h-8"
                >
                  <Download className="w-3.5 h-3.5 mr-1.5" />
                  CSV
                </Button>
                <Button
                  size="sm"
                  onClick={handleExportTxt}
                  data-testid="export-txt-btn"
                  className="bg-white/[0.04] text-[#8888a0] hover:text-white hover:bg-white/[0.08] border border-white/[0.08] text-xs h-8"
                >
                  <FileText className="w-3.5 h-3.5 mr-1.5" />
                  TXT
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Results Grid */}
        <ResultsGrid results={results} isLoading={isVerifying} />
      </main>

      {/* File Preview Modal */}
      {filePreviewData && (
        <FilePreviewModal
          data={filePreviewData}
          onConfirm={handleFilePreviewConfirm}
          onCancel={handleFilePreviewCancel}
          disabled={isVerifying}
        />
      )}
    </div>
  );
}
