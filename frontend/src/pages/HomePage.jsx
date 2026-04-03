import { useState, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
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

  // Check proxy status on mount
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

    const BATCH_SIZE = 5;
    const totalBatches = Math.ceil(identifiers.length / BATCH_SIZE);
    let completedCount = 0;

    try {
      for (let i = 0; i < totalBatches; i++) {
        const batch = identifiers.slice(i * BATCH_SIZE, (i + 1) * BATCH_SIZE);
        
        const requestData = { identifiers: batch };
        if (selectedPlatforms.length > 0) {
          requestData.platforms = selectedPlatforms;
        }

        const response = await axios.post(`${API}/verify`, requestData);
        const batchResults = response.data.results;

        // Add results immediately as they arrive
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
      // Step 1: Parse file to detect emails/phones
      const response = await axios.post(`${API}/parse-file`, formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });

      // Step 2: Show preview modal with detected data
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

    // Use the existing handleVerify
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

    // Get all unique platform names from results
    const allPlatforms = new Set();
    results.forEach(r => r.platforms.forEach(p => allPlatforms.add(p.platform)));
    const platformList = Array.from(allPlatforms).sort();

    // Create CSV content with all platforms
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
    txtContent += "       FAST - Résultats de vérification\n";
    txtContent += `       Date: ${new Date().toLocaleDateString('fr-FR')}\n`;
    txtContent += "═══════════════════════════════════════════\n\n";

    results.forEach((r, idx) => {
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

    // Summary
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
    found: results.reduce(
      (acc, r) => acc + r.platforms.filter((p) => p.status === "found").length,
      0
    ),
    notFound: results.reduce(
      (acc, r) => acc + r.platforms.filter((p) => p.status === "not_found").length,
      0
    ),
    unverifiable: results.reduce(
      (acc, r) => acc + r.platforms.filter((p) => p.status === "unverifiable").length,
      0
    ),
    rateLimited: results.reduce(
      (acc, r) => acc + r.platforms.filter((p) => p.status === "rate_limited" || p.status === "error").length,
      0
    ),
  };

  return (
    <div className="min-h-screen bg-[#05030A] bg-grid relative">
      {/* Background overlay with image */}
      <div
        className="fixed inset-0 opacity-[0.08] mix-blend-overlay pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(ellipse at center, transparent 0%, #05030A 70%), url('https://images.unsplash.com/photo-1771875802948-0d0f3424fe6d?w=1920&q=80')`,
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      />

      <div className="relative z-10">
        <Header />

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
          {/* Hero Section */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="font-heading text-4xl sm:text-5xl lg:text-6xl font-black tracking-tighter mb-4">
              <span className="gradient-text">Vérification</span>{" "}
              <span className="text-white">Rapide</span>
            </h1>
            <p className="text-slate-400 text-sm sm:text-base max-w-2xl mx-auto font-mono">
              Vérifiez emails et numéros de téléphone sur
              Netflix, Uber Eats, Binance, Coinbase, Deliveroo, Snapchat et 30+ plateformes
            </p>
          </motion.div>

          {/* Proxy Manager */}
          <ProxyManager onProxyChange={(count) => setProxyCount(count)} />

          {/* Platform Selector */}
          <PlatformSelector 
            selectedPlatforms={selectedPlatforms}
            onSelectionChange={setSelectedPlatforms}
            disabled={isVerifying}
          />

          {/* Proxy Warning Banner */}
          {proxyCount === 0 && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-8 p-4 rounded-xl border border-amber-500/30 bg-amber-500/5 backdrop-blur-sm"
            >
              <div className="flex items-start gap-3">
                <ShieldAlert className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-amber-400 text-sm font-medium font-mono">
                    Aucun proxy configuré
                  </p>
                  <p className="text-amber-400/70 text-xs font-mono mt-1">
                    Netflix, Uber Eats, Binance, Coinbase et Deliveroo nécessitent des proxies résidentiels pour fonctionner. 
                    Sans proxy, ces plateformes afficheront "Non vérifiable". Les 30+ autres plateformes fonctionnent normalement.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Input Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
            >
              <UploadZone onFileUpload={handleFileUpload} disabled={isVerifying || isParsing} />
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <TextPasteZone onVerify={handleVerify} disabled={isVerifying} />
            </motion.div>
          </div>

          {/* Progress Bar */}
          <AnimatePresence>
            {isVerifying && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mb-8"
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-400 font-mono flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-400 animate-pulse" />
                    Vérification en cours...
                  </span>
                  <span className="text-sm font-mono">
                    <span className="text-blue-400">{verifiedCount}</span>
                    <span className="text-slate-600">/</span>
                    <span className="text-slate-400">{totalToVerify}</span>
                    <span className="text-slate-600 ml-2">({Math.round(progress)}%)</span>
                  </span>
                </div>
                <div className="h-2.5 bg-white/5 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full progress-bar rounded-full"
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    transition={{ duration: 0.5 }}
                  />
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Stats & Actions */}
          {results.length > 0 && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="mb-8"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <StatsBar stats={stats} />
                <div className="flex gap-2 flex-wrap">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleClear}
                    data-testid="clear-results-btn"
                    className="border-white/10 text-slate-400 hover:text-white hover:border-white/20 bg-transparent"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Effacer
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleExport}
                    data-testid="export-results-btn"
                    className="bg-gradient-to-r from-blue-600 to-purple-600 hover:shadow-[0_0_20px_rgba(139,92,246,0.4)] transition-all"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    CSV
                  </Button>
                  <Button
                    size="sm"
                    onClick={handleExportTxt}
                    data-testid="export-txt-btn"
                    className="bg-gradient-to-r from-indigo-600 to-blue-600 hover:shadow-[0_0_20px_rgba(99,102,241,0.4)] transition-all"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    TXT
                  </Button>
                </div>
              </div>
            </motion.div>
          )}

          {/* Results Grid */}
          <ResultsGrid results={results} isLoading={isVerifying} />
        </main>
      </div>

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
