import { useState, useCallback, useEffect } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { toast } from "sonner";
import axios from "axios";
import Header from "../components/Header";
import UploadZone from "../components/UploadZone";
import TextPasteZone from "../components/TextPasteZone";
import ProxyManager from "../components/ProxyManager";
import { Button } from "../components/ui/button";
import { Download, Zap, Trash2, FileText, CheckCircle2, XCircle, AlertTriangle, Shield } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function HomePage() {
  const [results, setResults] = useState([]);
  const [isVerifying, setIsVerifying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [totalToVerify, setTotalToVerify] = useState(0);
  const [verifiedCount, setVerifiedCount] = useState(0);
  const [proxyCount, setProxyCount] = useState(0);

  useEffect(() => {
    const checkHealth = async () => {
      try { 
        const r = await axios.get(`${API}/health`); 
        setProxyCount(r.data.proxies_active || 0); 
      } catch (e) { 
        setProxyCount(0); 
      }
    };
    checkHealth();
  }, []);

  const handleVerify = useCallback(async (emails) => {
    if (!emails || emails.length === 0) { toast.error("Aucun email valide trouvé"); return; }
    
    // Filter only valid emails
    const validEmails = emails.filter(e => e.includes("@") && e.includes("."));
    if (validEmails.length === 0) { toast.error("Aucun email valide"); return; }

    setIsVerifying(true); 
    setProgress(0); 
    setVerifiedCount(0); 
    setTotalToVerify(validEmails.length); 
    setResults([]);
    
    // Process in batches of 10 (Playwright is slower, smaller batches)
    const batchSize = Math.min(10, validEmails.length);
    const totalBatches = Math.ceil(validEmails.length / batchSize);
    let completedCount = 0;
    let allResults = [];
    
    try {
      for (let i = 0; i < totalBatches; i++) {
        const batch = validEmails.slice(i * batchSize, (i + 1) * batchSize);
        
        try {
          const resp = await axios.post(`${API}/check`, { emails: batch }, { timeout: 600000 });
          allResults = [...allResults, ...resp.data.results];
          setResults([...allResults]);
        } catch (batchError) {
          console.error(`Batch ${i + 1} error:`, batchError);
          toast.error(`Erreur batch ${i + 1}`);
        }
        
        completedCount += batch.length;
        setVerifiedCount(completedCount);
        setProgress((completedCount / validEmails.length) * 100);
      }
      
      const found = allResults.filter(r => r.status === "found").length;
      toast.success(`Terminé: ${found} compte(s) trouvé(s) / ${allResults.length} vérifiés`);
    } catch (error) {
      console.error("Verification error:", error);
      toast.error("Erreur lors de la vérification");
    } finally { 
      setIsVerifying(false); 
      setProgress(100); 
    }
  }, []);

  const handleFileUpload = useCallback(async (file) => {
    if (!file) return;
    // Read file content and extract emails
    const text = await file.text();
    const emailRegex = /[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}/g;
    const emails = [...new Set((text.match(emailRegex) || []).map(e => e.toLowerCase()))];
    
    if (emails.length === 0) {
      toast.error("Aucun email trouvé dans le fichier");
      return;
    }
    
    toast.info(`${emails.length} email(s) trouvés dans le fichier`);
    handleVerify(emails);
  }, [handleVerify]);

  const handleExportFound = useCallback(() => {
    const found = results.filter(r => r.status === "found");
    if (found.length === 0) { toast.error("Aucun compte trouvé"); return; }
    const content = found.map(r => r.email).join("\n");
    const blob = new Blob([content], { type: "text/plain;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `uber_eats_found_${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success(`${found.length} email(s) exporté(s)`);
  }, [results]);

  const handleExportCSV = useCallback(() => {
    if (results.length === 0) { toast.error("Aucun résultat"); return; }
    const rows = ["Email,Status,Details"];
    results.forEach(r => {
      rows.push(`"${r.email}","${r.status}","${r.details || ''}"`);
    });
    const blob = new Blob(["\uFEFF" + rows.join("\n")], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `uber_eats_results_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    toast.success("Résultats exportés en CSV");
  }, [results]);

  const handleClear = useCallback(() => { 
    setResults([]); setProgress(0); setTotalToVerify(0); setVerifiedCount(0); 
    toast.info("Résultats effacés"); 
  }, []);

  // Stats
  const stats = {
    total: results.length,
    found: results.filter(r => r.status === "found").length,
    notFound: results.filter(r => r.status === "not_found").length,
    captcha: results.filter(r => r.status === "captcha").length,
    errors: results.filter(r => r.status === "error" || r.status === "unverifiable").length,
  };

  return (
    <div className="min-h-screen bg-[#05050A] relative">
      <Header />

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero */}
        <div className="text-center mb-10 animate-fade-in-up">
          <div className="inline-flex items-center gap-2 mb-4">
            <span className="px-4 py-1.5 rounded-full text-xs font-medium bg-[#06C167]/10 border border-[#06C167]/30 text-[#06C167]">
              🍔 Uber Eats Email Checker
            </span>
            {proxyCount > 0 && (
              <span className="px-3 py-1.5 rounded-full text-xs font-medium bg-green-500/10 border border-green-500/30 text-green-400">
                <Shield className="w-3 h-3 inline mr-1" />{proxyCount} proxy actif{proxyCount > 1 ? 's' : ''}
              </span>
            )}
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tighter mb-3 font-heading">
            <span className="bg-gradient-to-r from-[#06C167] to-[#00D4AA] bg-clip-text text-transparent">Uber Eats Checker</span>
          </h1>
          <p className="text-base text-gray-400 max-w-xl mx-auto leading-relaxed">
            Vérifiez si des emails sont inscrits sur Uber Eats. Ajoutez des proxies datacenter pour une meilleure détection.
          </p>
        </div>

        {/* Proxy Manager */}
        <ProxyManager onProxyChange={(count) => setProxyCount(count)} />

        {/* Input zones */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <UploadZone onFileUpload={handleFileUpload} disabled={isVerifying} />
          <TextPasteZone onVerify={handleVerify} disabled={isVerifying} />
        </div>

        {/* Progress Bar */}
        <AnimatePresence>
          {isVerifying && (
            <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} className="mb-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-400 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-[#06C167] animate-pulse" /> Vérification Uber Eats en cours...
                </span>
                <span className="text-sm font-mono">
                  <span className="text-[#06C167]">{verifiedCount}</span>
                  <span className="text-gray-600">/</span>
                  <span className="text-gray-400">{totalToVerify}</span>
                  <span className="text-gray-600 ml-1">({Math.round(progress)}%)</span>
                </span>
              </div>
              <div className="h-2 bg-white/5 rounded-full overflow-hidden border border-white/5">
                <motion.div 
                  className="h-full bg-gradient-to-r from-[#06C167] to-[#00D4AA] rounded-full" 
                  initial={{ width: 0 }} 
                  animate={{ width: `${progress}%` }} 
                  transition={{ duration: 0.3 }} 
                />
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Results Section */}
        {results.length > 0 && (
          <>
            {/* Stats Bar */}
            <div className="mb-6 p-4 rounded-xl bg-white/[0.02] border border-white/5">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
                <div className="flex items-center gap-4 flex-wrap">
                  <div className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-green-400" />
                    <span className="text-sm text-green-400 font-medium">{stats.found} trouvé{stats.found > 1 ? 's' : ''}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <XCircle className="w-4 h-4 text-red-400" />
                    <span className="text-sm text-red-400 font-medium">{stats.notFound} non-inscrit{stats.notFound > 1 ? 's' : ''}</span>
                  </div>
                  {stats.captcha > 0 && (
                    <div className="flex items-center gap-1.5">
                      <Shield className="w-4 h-4 text-yellow-400" />
                      <span className="text-sm text-yellow-400 font-medium">{stats.captcha} captcha</span>
                    </div>
                  )}
                  {stats.errors > 0 && (
                    <div className="flex items-center gap-1.5">
                      <AlertTriangle className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-gray-500 font-medium">{stats.errors} erreur{stats.errors > 1 ? 's' : ''}</span>
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={handleClear}
                    className="border-white/10 text-gray-400 hover:text-white hover:bg-white/5 bg-transparent text-xs h-8">
                    <Trash2 className="w-3.5 h-3.5 mr-1.5" /> Effacer
                  </Button>
                  <Button size="sm" onClick={handleExportFound} disabled={stats.found === 0}
                    className="bg-[#06C167] text-white font-bold text-xs h-8 hover:bg-[#06C167]/80 disabled:opacity-50">
                    <Download className="w-3.5 h-3.5 mr-1.5" /> TXT ({stats.found})
                  </Button>
                  <Button size="sm" onClick={handleExportCSV}
                    className="bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 border border-white/10 text-xs h-8">
                    <FileText className="w-3.5 h-3.5 mr-1.5" /> CSV
                  </Button>
                </div>
              </div>
            </div>

            {/* Results Grid */}
            <div className="space-y-2">
              {results.map((r, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: idx * 0.02 }}
                  className={`flex items-center justify-between p-3 rounded-lg border ${
                    r.status === "found" 
                      ? "bg-green-500/5 border-green-500/20" 
                      : r.status === "not_found"
                      ? "bg-red-500/5 border-red-500/20"
                      : r.status === "captcha"
                      ? "bg-yellow-500/5 border-yellow-500/20"
                      : "bg-white/[0.02] border-white/5"
                  }`}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    {r.status === "found" && <CheckCircle2 className="w-4 h-4 text-green-400 flex-shrink-0" />}
                    {r.status === "not_found" && <XCircle className="w-4 h-4 text-red-400 flex-shrink-0" />}
                    {r.status === "captcha" && <Shield className="w-4 h-4 text-yellow-400 flex-shrink-0" />}
                    {(r.status === "error" || r.status === "unverifiable") && <AlertTriangle className="w-4 h-4 text-gray-500 flex-shrink-0" />}
                    <span className="text-sm text-white font-mono truncate">{r.email}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      r.status === "found" 
                        ? "bg-green-500/10 text-green-400"
                        : r.status === "not_found"
                        ? "bg-red-500/10 text-red-400"
                        : r.status === "captcha"
                        ? "bg-yellow-500/10 text-yellow-400"
                        : "bg-white/5 text-gray-500"
                    }`}>
                      {r.status === "found" ? "✓ Inscrit" : r.status === "not_found" ? "✗ Non inscrit" : r.status === "captcha" ? "⚠ Captcha" : "? Erreur"}
                    </span>
                    {r.details && (
                      <span className="text-[10px] text-gray-500 max-w-[150px] truncate hidden sm:block">{r.details}</span>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </>
        )}

        {/* Empty state */}
        {!isVerifying && results.length === 0 && (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-3">🍔</div>
            <p className="text-sm">Entrez des emails ou uploadez un fichier pour commencer la vérification Uber Eats</p>
            {proxyCount === 0 && (
              <p className="text-xs text-yellow-500/70 mt-2">
                ⚠️ Ajoutez des proxies datacenter pour une meilleure détection
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
