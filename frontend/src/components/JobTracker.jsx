import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Button } from "./ui/button";
import { 
  Loader2, CheckCircle2, XCircle, Download, FileText, 
  RefreshCw, Clock, Zap, Database, AlertTriangle 
} from "lucide-react";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function JobTracker({ jobId, onClose }) {
  const [job, setJob] = useState(null);
  const [error, setError] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchJob = useCallback(async () => {
    if (!jobId) return;
    try {
      setIsRefreshing(true);
      const response = await axios.get(`${API}/jobs/${jobId}`);
      setJob(response.data);
      setError(null);
    } catch (e) {
      setError(e.response?.data?.detail || "Erreur lors de la récupération du job");
    } finally {
      setIsRefreshing(false);
    }
  }, [jobId]);

  useEffect(() => {
    fetchJob();
    
    // Auto-refresh while job is running
    const interval = setInterval(() => {
      if (job?.status === "running" || job?.status === "pending") {
        fetchJob();
      }
    }, 2000);
    
    return () => clearInterval(interval);
  }, [fetchJob, job?.status]);

  const handleDownloadCSV = async () => {
    window.open(`${API}/jobs/${jobId}/results/csv`, '_blank');
  };

  const handleDownloadTXT = async () => {
    window.open(`${API}/jobs/${jobId}/results/txt`, '_blank');
  };

  const handleDownloadJSONL = async () => {
    window.open(`${API}/jobs/${jobId}/results/jsonl`, '_blank');
  };

  if (!job && !error) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="glass-card p-8 rounded-2xl">
          <Loader2 className="w-8 h-8 text-[#00F0FF] animate-spin mx-auto" />
          <p className="text-gray-400 mt-4">Chargement du job...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
        <div className="glass-card p-8 rounded-2xl max-w-md w-full">
          <XCircle className="w-12 h-12 text-red-500 mx-auto" />
          <h3 className="text-xl font-bold text-white mt-4 text-center">Erreur</h3>
          <p className="text-gray-400 mt-2 text-center">{error}</p>
          <Button onClick={onClose} className="w-full mt-6 bg-white/10 hover:bg-white/20">
            Fermer
          </Button>
        </div>
      </div>
    );
  }

  const getStatusIcon = () => {
    switch (job.status) {
      case "pending":
        return <Clock className="w-6 h-6 text-yellow-400 animate-pulse" />;
      case "running":
        return <Loader2 className="w-6 h-6 text-[#00F0FF] animate-spin" />;
      case "completed":
        return <CheckCircle2 className="w-6 h-6 text-green-400" />;
      case "failed":
        return <XCircle className="w-6 h-6 text-red-500" />;
      default:
        return <Database className="w-6 h-6 text-gray-400" />;
    }
  };

  const getStatusText = () => {
    switch (job.status) {
      case "pending":
        return "En attente...";
      case "running":
        return "Vérification en cours...";
      case "completed":
        return "Terminé !";
      case "failed":
        return "Échec";
      default:
        return job.status;
    }
  };

  const formatNumber = (num) => {
    return new Intl.NumberFormat('fr-FR').format(num);
  };

  const estimatedTimeRemaining = () => {
    if (job.status !== "running" || job.processed === 0) return null;
    const elapsed = (new Date() - new Date(job.started_at)) / 1000;
    const rate = job.processed / elapsed;
    const remaining = (job.total - job.processed) / rate;
    
    if (remaining < 60) return `~${Math.ceil(remaining)}s`;
    if (remaining < 3600) return `~${Math.ceil(remaining / 60)}min`;
    return `~${Math.ceil(remaining / 3600)}h`;
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card p-6 sm:p-8 rounded-2xl max-w-xl w-full max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            {getStatusIcon()}
            <div>
              <h3 className="text-lg font-bold text-white">{getStatusText()}</h3>
              <p className="text-xs text-gray-500">{job.filename}</p>
            </div>
          </div>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={fetchJob}
            disabled={isRefreshing}
            className="text-gray-400 hover:text-white"
          >
            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
          </Button>
        </div>

        {/* Progress */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-400">Progression</span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-mono">
                <span className="text-[#00F0FF]">{formatNumber(job.processed)}</span>
                <span className="text-gray-600">/</span>
                <span className="text-gray-400">{formatNumber(job.total)}</span>
              </span>
              {estimatedTimeRemaining() && (
                <span className="text-xs text-gray-500">({estimatedTimeRemaining()})</span>
              )}
            </div>
          </div>
          <div className="h-3 bg-white/5 rounded-full overflow-hidden border border-white/5">
            <motion.div 
              className="h-full bg-gradient-to-r from-[#00F0FF] to-[#8B5CF6] rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${job.progress}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <div className="text-right mt-1">
            <span className="text-xs font-mono text-gray-500">{job.progress}%</span>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          <div className="bg-green-500/10 border border-green-500/20 rounded-xl p-3 text-center">
            <p className="text-2xl font-bold text-green-400">{formatNumber(job.found)}</p>
            <p className="text-xs text-green-400/70">Trouvés</p>
          </div>
          <div className="bg-gray-500/10 border border-gray-500/20 rounded-xl p-3 text-center">
            <p className="text-2xl font-bold text-gray-400">{formatNumber(job.not_found)}</p>
            <p className="text-xs text-gray-400/70">Non trouvés</p>
          </div>
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-3 text-center">
            <p className="text-2xl font-bold text-yellow-400">{formatNumber(job.unverifiable)}</p>
            <p className="text-xs text-yellow-400/70">Non vérifiables</p>
          </div>
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 text-center">
            <p className="text-2xl font-bold text-red-400">{formatNumber(job.errors)}</p>
            <p className="text-xs text-red-400/70">Erreurs</p>
          </div>
        </div>

        {/* Speed indicator */}
        {job.status === "running" && job.processed > 0 && job.started_at && (
          <div className="mb-6 p-3 bg-[#00F0FF]/5 border border-[#00F0FF]/20 rounded-xl">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-[#00F0FF]" />
              <span className="text-sm text-[#00F0FF]">
                ~{Math.round(job.processed / ((new Date() - new Date(job.started_at)) / 1000))} vérifications/sec
              </span>
            </div>
          </div>
        )}

        {/* Download buttons */}
        {(job.status === "completed" || job.processed > 0) && (
          <div className="space-y-3">
            <p className="text-sm text-gray-400 flex items-center gap-2">
              <Download className="w-4 h-4" /> Télécharger les résultats
            </p>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
              <Button 
                onClick={handleDownloadCSV}
                className="bg-gradient-to-r from-[#00F0FF] to-[#8B5CF6] text-white font-bold hover:opacity-90"
              >
                <Download className="w-4 h-4 mr-2" /> CSV
              </Button>
              <Button 
                onClick={handleDownloadTXT}
                className="bg-white/10 hover:bg-white/20 text-white"
              >
                <FileText className="w-4 h-4 mr-2" /> TXT
              </Button>
              <Button 
                onClick={handleDownloadJSONL}
                className="bg-white/10 hover:bg-white/20 text-white"
              >
                <Database className="w-4 h-4 mr-2" /> JSONL
              </Button>
            </div>
            <p className="text-xs text-gray-500 text-center mt-2">
              CSV et TXT contiennent uniquement les identifiants valides (trouvés sur au moins 1 plateforme)
            </p>
          </div>
        )}

        {/* Warning for running jobs */}
        {job.status === "running" && (
          <div className="mt-4 p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-xl">
            <div className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-yellow-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-yellow-400">
                Le traitement continue en arrière-plan. Vous pouvez fermer cette fenêtre et revenir plus tard.
              </p>
            </div>
          </div>
        )}

        {/* Close button */}
        <Button 
          onClick={onClose}
          variant="outline"
          className="w-full mt-6 border-white/10 text-gray-400 hover:text-white hover:bg-white/5"
        >
          {job.status === "completed" ? "Fermer" : "Masquer (traitement continue)"}
        </Button>
      </motion.div>
    </div>
  );
}
